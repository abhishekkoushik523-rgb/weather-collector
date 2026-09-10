"""
Bridge API - Connects MongoDB pipeline to Frontend
Serves /reports and /stats endpoints matching frontend's expected format.
See: Frontend/INTEGRATION.md
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List

import pymongo
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("bridge")

# ---------------------------------------------------------------------------
# MongoDB
# ---------------------------------------------------------------------------
try:
    client = pymongo.MongoClient(
        os.getenv("MONGODB_URI"),
        tlsAllowInvalidCertificates=True,
        serverSelectionTimeoutMS=10000,
    )
    db = client["weather_db"]
    collection = db["weather_data"]
    log.info("✅ Connected to MongoDB Atlas")
except Exception as e:
    log.error(f"❌ MongoDB connection failed: {e}")
    raise

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(title="Weather Data Bridge API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hackathon: allow all. Lock down for production.
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Lookup tables
# ---------------------------------------------------------------------------

# City → State
CITY_STATE = {
    "Mumbai": "Maharashtra",
    "Delhi": "Delhi",
    "New Delhi": "Delhi",
    "Bengaluru": "Karnataka",
    "Bangalore": "Karnataka",
    "Chennai": "Tamil Nadu",
    "Kolkata": "West Bengal",
    "Hyderabad": "Telangana",
    "Pune": "Maharashtra",
    "Ahmedabad": "Gujarat",
    "Jaipur": "Rajasthan",
    "Lucknow": "Uttar Pradesh",
    "Bhopal": "Madhya Pradesh",
    "Patna": "Bihar",
    "Guwahati": "Assam",
    "Thiruvananthapuram": "Kerala",
}

# City → (lat, lng) — fallback if record lacks coordinates
CITY_COORDS = {
    "Mumbai": (19.0760, 72.8777),
    "Delhi": (28.6139, 77.2090),
    "New Delhi": (28.6139, 77.2090),
    "Bengaluru": (12.9716, 77.5946),
    "Bangalore": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Hyderabad": (17.3850, 78.4867),
    "Pune": (18.5204, 73.8567),
    "Ahmedabad": (23.0225, 72.5714),
    "Jaipur": (26.9124, 75.7873),
    "Lucknow": (26.8467, 80.9462),
    "Bhopal": (23.2599, 77.4126),
    "Patna": (25.5941, 85.1376),
    "Guwahati": (26.1445, 91.7362),
    "Thiruvananthapuram": (8.5241, 76.9366),
}

# Pipeline platform → frontend source (must be one of: twitter, citizen_report, reddit, news_rss)
SOURCE_MAP = {
    "OpenWeatherMap": "citizen_report",
    "open-meteo": "citizen_report",
    "OpenWeatherMap-Forecast": "citizen_report",
    "reddit": "reddit",
    "twitter": "twitter",
    "data.gov.in": "citizen_report",
    "simulated": "citizen_report",
}

# Pipeline event → frontend event (must be one of: rainfall, thunderstorm, flooding,
# heatwave, fog, dust_storm, strong_wind)
EVENT_MAP = {
    "rainfall": "rainfall",
    "thunderstorm": "thunderstorm",
    "flooding": "flooding",
    "flood": "flooding",
    "heatwave": "heatwave",
    "fog": "fog",
    "dust_storm": "dust_storm",
    "dust": "dust_storm",
    "strong_wind": "strong_wind",
    "strong_winds": "strong_wind",
    "wind": "strong_wind",
    "cloudy": "rainfall",       # fallback — clouds often precede rain
    "clear": "heatwave",        # fallback — clear sky in India = hot
    "forecast": "rainfall",     # forecast events → generic
    "unknown": "rainfall",      # catch-all
}

VALID_EVENT_TYPES = {
    "rainfall",
    "thunderstorm",
    "flooding",
    "heatwave",
    "fog",
    "dust_storm",
    "strong_wind",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_iso(value):
    """Convert datetime or string to ISO 8601 string."""
    if value is None:
        return datetime.utcnow().isoformat() + "Z"
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _normalize_platform(src):
    """Extract platform name from source (dict or string)."""
    if isinstance(src, dict):
        return src.get("platform") or src.get("type") or "unknown"
    if isinstance(src, str):
        return src
    return "unknown"


def _map_event(raw_event: str) -> str:
    """Map pipeline event_type to frontend event_type."""
    if not raw_event:
        return "rainfall"
    return EVENT_MAP.get(str(raw_event).lower(), "rainfall")


def transform_record(doc: dict) -> dict:
    """Convert a MongoDB record to the frontend's Report format."""
    loc = doc.get("location") or {}
    src = doc.get("source") or {}
    cls = doc.get("classification") or {}
    met = doc.get("weather_metrics") or {}

    city = loc.get("city") or "Unknown"
    platform = _normalize_platform(src)

    # Coordinates — fallback to known city coords if record lacks them
    lat = loc.get("latitude") or loc.get("lat")
    lng = loc.get("longitude") or loc.get("lng") or loc.get("lon")
    if not lat or not lng:
        fallback = CITY_COORDS.get(city, (20.5937, 78.9629))  # India center
        lat, lng = fallback

    # Event type
    raw_event = cls.get("event_type") if isinstance(cls, dict) else None
    event_type = _map_event(raw_event)

    # Credibility
    confidence = cls.get("confidence") if isinstance(cls, dict) else None
    credibility = int(round((confidence if confidence is not None else 0.85) * 100))
    credibility = max(0, min(100, credibility))

    # Timestamp
    ts = doc.get("created_at") or doc.get("timestamp") or doc.get("api_timestamp")

    # Verification: API data from trusted sources is treated as ML-verified
    verification_status = doc.get("verification_status") or "verified"
    verified_by = doc.get("verified_by") or "ml"

    return {
        "id": doc.get("report_id") or str(doc.get("_id", "")),
        "text": doc.get("text") or "Weather report",
        "source": SOURCE_MAP.get(platform, "citizen_report"),
        "event_type": event_type,
        "city": city,
        "state": CITY_STATE.get(city, loc.get("state") or "Unknown"),
        "locality": loc.get("locality"),
        "lat": float(lat),
        "lng": float(lng),
        "timestamp": _to_iso(ts),
        "credibility_score": credibility,
        "verification_status": verification_status,
        "verified_by": verified_by,
        "media_url": (doc.get("media") or {}).get("media_url"),
        "duplicate_group_id": (doc.get("duplicate_detection") or {}).get("duplicate_group_id"),
    }


def _is_all(value: Optional[str]) -> bool:
    """Return True if filter value means 'no filter'."""
    if not value:
        return True
    return value.strip().lower() in {"all", "all statuses", "all types", "all states", ""}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Weather Data Bridge API",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    try:
        total = collection.count_documents({})
        return {"status": "healthy", "records": total}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": str(e)})


@app.get("/reports")
def get_reports(
    event_type: Optional[str] = Query(None, description="Comma-separated event types"),
    state: Optional[str] = Query(None, description="Comma-separated states"),
    status: Optional[str] = Query(None, description="verification_status filter"),
    date_from: Optional[str] = Query(None, description="ISO date, inclusive"),
    date_to: Optional[str] = Query(None, description="ISO date, inclusive"),
    q: Optional[str] = Query(None, description="Search in text and city"),
    limit: int = Query(1000, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    """Return transformed records in frontend's Report format."""
    query = {}

    # Date range on created_at
    if date_from or date_to:
        date_query = {}
        if date_from:
            date_query["$gte"] = date_from
        if date_to:
            date_query["$lte"] = date_to + "T23:59:59"
        query["created_at"] = date_query

    # Free-text search
    if q and q.strip():
        q_clean = q.strip()
        query["$or"] = [
            {"location.city": {"$regex": q_clean, "$options": "i"}},
            {"text": {"$regex": q_clean, "$options": "i"}},
        ]

    # Fetch from Mongo (sorted newest first)
    cursor = collection.find(query).sort([("created_at", -1), ("_id", -1)]).skip(offset).limit(limit)
    results = [transform_record(doc) for doc in cursor]

    # Post-filters (handle "All" values gracefully)
    if event_type and not _is_all(event_type):
        wanted = {t.strip().lower() for t in event_type.split(",") if t.strip()}
        wanted.discard("all")
        if wanted:
            results = [r for r in results if r["event_type"].lower() in wanted]

    if state and not _is_all(state):
        wanted = {s.strip() for s in state.split(",") if s.strip()}
        if wanted:
            results = [r for r in results if r["state"] in wanted]

    if status and not _is_all(status):
        wanted = status.strip().lower()
        results = [r for r in results if r["verification_status"].lower() == wanted]

    return results


@app.get("/reports/count")
def count_reports():
    """Total record count."""
    return {"total": collection.count_documents({})}


@app.get("/reports/{report_id}")
def get_report(report_id: str):
    """Fetch a single report by ID."""
    doc = collection.find_one({"report_id": report_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")
    return transform_record(doc)


@app.get("/stats")
def get_stats():
    """Aggregated stats matching frontend's expected shape."""
    cursor = collection.find({})
    records = [transform_record(doc) for doc in cursor]

    total = len(records)
    if total == 0:
        return {
            "total": 0,
            "verifiedPct": 0,
            "activeAlerts": 0,
            "mostAffectedState": "—",
        }

    verified = sum(1 for r in records if r["verification_status"] == "verified")
    verified_pct = int(round((verified / total) * 100))

    # Active Alerts: flooding or thunderstorm with credibility > 60
    active = sum(
        1
        for r in records
        if r["event_type"] in {"flooding", "thunderstorm"}
        and r["credibility_score"] > 60
    )

    # Most affected state
    state_counts = {}
    for r in records:
        state_counts[r["state"]] = state_counts.get(r["state"], 0) + 1
    most_affected = max(state_counts, key=state_counts.get) if state_counts else "—"

    return {
        "total": total,
        "verifiedPct": verified_pct,
        "activeAlerts": active,
        "mostAffectedState": most_affected,
    }


@app.patch("/reports/{report_id}")
def update_report(report_id: str, body: dict):
    """Update a report's verification status (human admin override)."""
    new_status = body.get("verification_status")
    if new_status not in {"verified", "pending", "rejected"}:
        raise HTTPException(status_code=400, detail="Invalid verification_status")

    verified_by = body.get("verified_by", "admin")

    result = collection.update_one(
        {"report_id": report_id},
        {
            "$set": {
                "verification_status": new_status,
                "verified_by": verified_by,
                "updated_at": datetime.utcnow().isoformat() + "Z",
            }
        },
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")

    doc = collection.find_one({"report_id": report_id})
    return transform_record(doc)


# ---------------------------------------------------------------------------
# Startup banner
# ---------------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    try:
        n = collection.count_documents({})
        log.info(f"📊 Bridge ready — {n} records in MongoDB")
    except Exception as e:
        log.error(f"Startup check failed: {e}")
