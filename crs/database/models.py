"""
Database schema definitions for the
Central Receiving Server (CRS).

SQLite Version
"""


CREATE_STATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS stations (

    station_id TEXT PRIMARY KEY,

    station_name TEXT NOT NULL,

    latitude REAL NOT NULL,

    longitude REAL NOT NULL,

    elevation REAL NOT NULL,

    last_health_report TEXT,

    status TEXT DEFAULT 'OFFLINE'
);
"""


CREATE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS events (

    event_id INTEGER PRIMARY KEY AUTOINCREMENT,

    origin_time TEXT NOT NULL,

    estimated_latitude REAL,

    estimated_longitude REAL,

    estimated_depth REAL,

    estimated_magnitude REAL,

    confidence REAL,

    confirmed INTEGER DEFAULT 0,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


CREATE_STATION_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS station_events (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    event_id INTEGER,

    station_id TEXT,

    detection_time TEXT,

    pga REAL,

    sta_lta REAL,

    p_wave_confidence REAL,

    local_confidence REAL,

    waveform_path TEXT,

    FOREIGN KEY(event_id)
        REFERENCES events(event_id),

    FOREIGN KEY(station_id)
        REFERENCES stations(station_id)
);
"""


CREATE_HEALTH_TABLE = """
CREATE TABLE IF NOT EXISTS station_health (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    station_id TEXT,

    cpu_usage REAL,

    memory_usage REAL,

    disk_usage REAL,

    cpu_temperature REAL,

    gps_locked INTEGER,

    sensor_status INTEGER,

    mqtt_connected INTEGER,

    timestamp TEXT,

    FOREIGN KEY(station_id)
        REFERENCES stations(station_id)
);
"""


CREATE_ALERTS_TABLE = """
CREATE TABLE IF NOT EXISTS alerts (

    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,

    event_id INTEGER,

    alert_level TEXT,

    message TEXT,

    issued_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(event_id)
        REFERENCES events(event_id)
);
"""


TABLES = [

    CREATE_STATIONS_TABLE,

    CREATE_EVENTS_TABLE,

    CREATE_STATION_EVENTS_TABLE,

    CREATE_HEALTH_TABLE,

    CREATE_ALERTS_TABLE

]