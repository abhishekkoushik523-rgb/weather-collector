"""
Open-Meteo Weather Collector
Fetches current weather for Indian cities and stores in MongoDB.
"""

import os
import requests
import pymongo
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")

# City → (latitude, longitude) mapping for India
CITIES = {
    "Mumbai": (19.0760, 72.8777),
    "Delhi": (28.6139, 77.2090),
    "Bengaluru": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Hyderabad": (17.3850, 78.4867),
    "Pune": (18.5204, 73.8567),
}

# Connect to MongoDB
client = pymongo.MongoClient(MONGO_URI)
db = client["weather_db"]
collection = db["weather_data"]

def fetch_openmeteo(lat, lon):
    """Fetch current weather from Open-Meteo"""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return None

def map_weather_code(code):
    """Map Open-Meteo weather code to event category"""
    # Simplified mapping
    if code == 0:
        return "clear"
    elif code in [1, 2, 3]:
        return "cloudy"
    elif code in [45, 48]:
        return "fog"
    elif code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
        return "rainfall"
    elif code in [71, 73, 75, 77, 85, 86]:
        return "snow"  # not in our list but okay
    elif code in [95, 96, 99]:
        return "thunderstorm"
    else:
        return "unknown"

def parse_and_store(city, lat, lon, data):
    """Parse Open-Meteo data and store as Schema V1"""
    if not data:
        return None

    current = data.get("current_weather", {})
    if not current:
        print(f"⚠️  No current weather for {city}")
        return None

    # Generate report_id
    report_id = f"OM_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{city[:3]}"

    # Build Schema V1 document
    doc = {
        "report_id": report_id,
        "text": f"Weather in {city}: {current.get('temperature')}°C, wind {current.get('windspeed')} km/h",  # human-readable
        "source": {
            "type": "api",
            "platform": "open-meteo",
            "user_id": None
        },
        "location": {
            "city": city,
            "state": None,  # not provided
            "latitude": lat,
            "longitude": lon
        },
        "timestamp": datetime.fromisoformat(current.get("time")).isoformat() + "Z",
        "media": {
            "has_photo": False,
            "media_url": None
        },
        # Temporary: store metrics until team decides schema
        "weather_metrics": {
            "temperature": current.get("temperature"),
            "wind_speed": current.get("windspeed"),
            "wind_direction": current.get("winddirection"),
            "weather_code": current.get("weathercode"),
            "condition": map_weather_code(current.get("weathercode"))
        },
        "raw_data": data,  # keep original for debugging
        "created_at": datetime.utcnow().isoformat() + "Z",
        # Other fields that ML/Backend will fill later
        "cleaned_text": None,
        "classification": None,
        "duplicate_detection": None,
        "credibility": None,
        "verification": {"status": "pending", "verified_by": None, "verified_at": None},
        "updated_at": None
    }

    try:
        result = collection.insert_one(doc)
        print(f"✅ Saved {city} | Temp: {current.get('temperature')}°C | ID: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

def main():
    print("🌤️  OPEN-METEO COLLECTOR STARTED\n")
    for city, (lat, lon) in CITIES.items():
        print(f"--- {city} ---")
        data = fetch_openmeteo(lat, lon)
        if data:
            parse_and_store(city, lat, lon, data)
        else:
            print(f"⚠️  No data for {city}, skipping")
        print()
    print("✅ Collection complete!")

if __name__ == "__main__":
    main()
