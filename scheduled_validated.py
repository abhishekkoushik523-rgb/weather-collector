"""
Weather Collector v6 – With Data Validation
Checks required fields before inserting.
"""

import os
import sys
import time
import logging
import requests
import pymongo
import schedule
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")
MONGO_URI = os.getenv("MONGODB_URI")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("collector.log"), logging.StreamHandler()]
)

try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client["weather_db"]
    collection = db["weather_data"]
    logging.info("✅ Connected to MongoDB")
except Exception as e:
    logging.error(f"❌ MongoDB connection failed: {e}")
    sys.exit(1)

# ============================================
# VALIDATION FUNCTION
# ============================================
def validate_record(doc):
    """Check if record has required fields"""
    required = [
        ("source.platform", "source.platform"),
        ("location.city", "location.city"),
        ("timestamp", "timestamp"),
        ("weather_metrics.temperature", "weather_metrics.temperature"),
    ]
    
    for field, display in required:
        # Navigate nested fields
        parts = field.split('.')
        val = doc
        for part in parts:
            if isinstance(val, dict):
                val = val.get(part)
            else:
                val = None
                break
        if val is None:
            return False, f"Missing {display}"
    
    return True, "Valid"

def safe_insert(doc):
    """Validate, deduplicate, then insert"""
    # Validate
    is_valid, reason = validate_record(doc)
    if not is_valid:
        logging.warning(f"⏭️  SKIPPED (invalid): {doc.get('location', {}).get('city', 'unknown')} - {reason}")
        return None
    
    # Deduplication (simple: check platform + city + hour)
    platform = doc.get("source", {}).get("platform")
    city = doc.get("location", {}).get("city")
    timestamp_hour = doc.get("timestamp_hour")
    
    if platform and city and timestamp_hour:
        existing = collection.find_one({
            "source.platform": platform,
            "location.city": city,
            "timestamp_hour": timestamp_hour
        })
        if existing:
            logging.info(f"⏭️  DUPLICATE SKIPPED: {platform} - {city}")
            return None
    
    # Insert
    try:
        result = collection.insert_one(doc)
        logging.info(f"✅ SAVED: {platform} - {city} | Event: {doc.get('classification', {}).get('event_type', 'unknown')}")
        return result.inserted_id
    except Exception as e:
        logging.error(f"❌ DB error: {e}")
        return None

# ============================================
# COLLECTORS (simplified – reuse logic from previous)
# ============================================
OWM_CITIES = ["Mumbai", "Delhi", "Bengaluru", "Chennai", "Kolkata"]

def fetch_owm(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
        else:
            logging.warning(f"OWM API error {city}: {r.status_code}")
            return None
    except Exception as e:
        logging.error(f"OWM network error {city}: {e}")
        return None

def collect_owm():
    logging.info("--- OpenWeatherMap ---")
    for city in OWM_CITIES:
        data = fetch_owm(city)
        if not data:
            continue
        
        dt = datetime.fromtimestamp(data.get("dt", 0))
        timestamp_hour = dt.replace(minute=0, second=0, microsecond=0).isoformat()
        temp_c = round(data["main"]["temp"] - 273.15, 1)
        
        # Simple categorization
        events = ["unknown"]
        if temp_c > 40:
            events = ["heatwave"]
        elif data["weather"][0]["id"] in [200, 201, 202, 210, 211, 212, 221, 230, 231, 232]:
            events = ["thunderstorm"]
        elif data["weather"][0]["id"] in [300, 301, 302, 310, 311, 312, 313, 314, 321, 500, 501, 502, 503, 504, 511, 520, 521, 522, 531]:
            events = ["rainfall"]
        elif data["weather"][0]["id"] in [701, 711, 721, 731, 741, 751, 761, 762, 771, 781]:
            events = ["fog"]
        elif data["weather"][0]["id"] == 800:
            events = ["clear"]
        elif data["weather"][0]["id"] in [801, 802, 803, 804]:
            events = ["cloudy"]
        
        doc = {
            "report_id": f"OWM_{datetime.now().strftime('%Y%m%d%H%M%S')}_{city[:3]}",
            "text": f"Weather in {city}: {data['weather'][0]['description']}, {temp_c}°C",
            "source": {"type": "api", "platform": "OpenWeatherMap", "user_id": None},
            "location": {"city": city, "state": None, "latitude": data.get("coord", {}).get("lat"), "longitude": data.get("coord", {}).get("lon")},
            "timestamp": dt.isoformat() + "Z",
            "timestamp_hour": timestamp_hour,
            "media": {"has_photo": False, "media_url": None},
            "weather_metrics": {"temperature": temp_c, "humidity": data["main"].get("humidity"), "wind_speed": data["wind"].get("speed"), "condition": data["weather"][0]["description"]},
            "classification": {"event_type": events[0], "event_types": events, "confidence": 0.95, "categorized_at": datetime.now().isoformat() + "Z"},
            "raw_data": data,
            "created_at": datetime.now().isoformat() + "Z",
            "cleaned_text": None,
            "duplicate_detection": None,
            "credibility": None,
            "verification": {"status": "pending", "verified_by": None, "verified_at": None},
            "updated_at": None
        }
        safe_insert(doc)

# Open-Meteo (reuse logic – I'll keep it concise)
OM_CITIES = {"Mumbai": (19.0760, 72.8777), "Delhi": (28.6139, 77.2090), "Bengaluru": (12.9716, 77.5946), "Chennai": (13.0827, 80.2707), "Kolkata": (22.5726, 88.3639), "Hyderabad": (17.3850, 78.4867), "Pune": (18.5204, 73.8567)}

def fetch_om(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
        else:
            logging.warning(f"OM API error: {r.status_code}")
            return None
    except Exception as e:
        logging.error(f"OM network error: {e}")
        return None

def collect_om():
    logging.info("--- Open-Meteo ---")
    for city, (lat, lon) in OM_CITIES.items():
        data = fetch_om(lat, lon)
        if not data:
            continue
        current = data.get("current_weather", {})
        if not current:
            continue
        dt = datetime.fromisoformat(current.get("time"))
        timestamp_hour = dt.replace(minute=0, second=0, microsecond=0).isoformat()
        
        # Map code
        code = current.get("weathercode", 0)
        if code == 0:
            events = ["clear"]
        elif code in [1, 2, 3]:
            events = ["cloudy"]
        elif code in [45, 48]:
            events = ["fog"]
        elif code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
            events = ["rainfall"]
        elif code in [95, 96, 99]:
            events = ["thunderstorm"]
        else:
            events = ["unknown"]
        
        doc = {
            "report_id": f"OM_{datetime.now().strftime('%Y%m%d%H%M%S')}_{city[:3]}",
            "text": f"Weather in {city}: {current.get('temperature')}°C, wind {current.get('windspeed')} km/h",
            "source": {"type": "api", "platform": "open-meteo", "user_id": None},
            "location": {"city": city, "state": None, "latitude": lat, "longitude": lon},
            "timestamp": current.get("time") + "Z",
            "timestamp_hour": timestamp_hour,
            "media": {"has_photo": False, "media_url": None},
            "weather_metrics": {"temperature": current.get("temperature"), "wind_speed": current.get("windspeed"), "condition": events[0]},
            "classification": {"event_type": events[0], "event_types": events, "confidence": 0.95, "categorized_at": datetime.now().isoformat() + "Z"},
            "raw_data": data,
            "created_at": datetime.now().isoformat() + "Z",
            "cleaned_text": None,
            "duplicate_detection": None,
            "credibility": None,
            "verification": {"status": "pending", "verified_by": None, "verified_at": None},
            "updated_at": None
        }
        safe_insert(doc)

# ============================================
# MAIN
# ============================================
def collect_all():
    logging.info("=" * 50)
    logging.info("🌤️  COLLECTION WITH VALIDATION STARTED")
    collect_owm()
    collect_om()
    logging.info("📊 Cycle complete")
    logging.info("=" * 50)

def main():
    logging.info("🚀 Weather Collector v6 (with validation) started")
    collect_all()
    schedule.every().hour.at(":00").do(collect_all)
    logging.info("⏰ Scheduler active")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("🛑 Collector stopped")
        sys.exit(0)
