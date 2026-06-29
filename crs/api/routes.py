"""
API Routes

REST API endpoints for the Central Receiving Server.
"""

from fastapi import APIRouter

from database.database import database

router = APIRouter()


# ----------------------------------------------------------
# Root
# ----------------------------------------------------------

@router.get("/")
def root():

    return {
        "message": "Earthquake Warning CRS API",
        "status": "running"
    }


# ----------------------------------------------------------
# Events
# ----------------------------------------------------------

@router.get("/events")
def get_events():

    query = """
    SELECT *
    FROM events
    ORDER BY created_at DESC;
    """

    return database.fetch_all(query)


# ----------------------------------------------------------
# Event by ID
# ----------------------------------------------------------

@router.get("/events/{event_id}")
def get_event(event_id: int):

    query = """
    SELECT *
    FROM events
    WHERE event_id=%s;
    """

    return database.fetch_one(
        query,
        (event_id,)
    )


# ----------------------------------------------------------
# Stations
# ----------------------------------------------------------

@router.get("/stations")
def get_stations():

    query = """
    SELECT *
    FROM stations
    ORDER BY station_id;
    """

    return database.fetch_all(query)


# ----------------------------------------------------------
# Health
# ----------------------------------------------------------

@router.get("/health")
def get_health():

    query = """
    SELECT *
    FROM station_health
    ORDER BY timestamp DESC;
    """

    return database.fetch_all(query)


# ----------------------------------------------------------
# Alerts
# ----------------------------------------------------------

@router.get("/alerts")
def get_alerts():

    query = """
    SELECT *
    FROM alerts
    ORDER BY issued_at DESC;
    """

    return database.fetch_all(query)