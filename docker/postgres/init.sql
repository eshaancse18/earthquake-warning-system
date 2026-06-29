-- ============================================================
-- EARTHQUAKE WARNING SYSTEM
-- CRS DATABASE INITIALIZATION
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- STATIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS stations (

    station_id VARCHAR(64)
        PRIMARY KEY,

    station_name VARCHAR(128)
        NOT NULL,

    latitude DOUBLE PRECISION
        NOT NULL,

    longitude DOUBLE PRECISION
        NOT NULL,

    elevation DOUBLE PRECISION,

    status VARCHAR(32)
        NOT NULL DEFAULT 'OFFLINE',

    last_seen TIMESTAMP,

    created_at TIMESTAMP
        NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stations_status
ON stations(status);

CREATE INDEX IF NOT EXISTS idx_stations_last_seen
ON stations(last_seen);

-- ============================================================
-- EVENT REPORTS
-- ============================================================

CREATE TABLE IF NOT EXISTS event_reports (

    report_id VARCHAR(128)
        PRIMARY KEY,

    station_id VARCHAR(64)
        NOT NULL,

    event_id VARCHAR(128)
        NOT NULL,

    timestamp TIMESTAMP
        NOT NULL,

    confidence DOUBLE PRECISION
        NOT NULL,

    pga DOUBLE PRECISION
        NOT NULL,

    stalta_ratio DOUBLE PRECISION,

    latitude DOUBLE PRECISION,

    longitude DOUBLE PRECISION,

    waveform_path TEXT,

    payload JSONB,

    received_at TIMESTAMP
        NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_event_reports_station
ON event_reports(station_id);

CREATE INDEX IF NOT EXISTS idx_event_reports_event
ON event_reports(event_id);

CREATE INDEX IF NOT EXISTS idx_event_reports_received
ON event_reports(received_at);

CREATE INDEX IF NOT EXISTS idx_event_reports_timestamp
ON event_reports(timestamp);

-- ============================================================
-- CONFIRMED EARTHQUAKES
-- ============================================================

CREATE TABLE IF NOT EXISTS earthquake_events (

    earthquake_id VARCHAR(128)
        PRIMARY KEY,

    confirmed_at TIMESTAMP
        NOT NULL,

    station_count INTEGER
        NOT NULL,

    confidence DOUBLE PRECISION
        NOT NULL,

    magnitude DOUBLE PRECISION,

    epicenter_latitude DOUBLE PRECISION,

    epicenter_longitude DOUBLE PRECISION,

    status VARCHAR(32)
        NOT NULL DEFAULT 'CONFIRMED',

    metadata_json JSONB,

    created_at TIMESTAMP
        NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_earthquake_confirmed
ON earthquake_events(confirmed_at);

CREATE INDEX IF NOT EXISTS idx_earthquake_status
ON earthquake_events(status);

CREATE INDEX IF NOT EXISTS idx_earthquake_magnitude
ON earthquake_events(magnitude);

-- ============================================================
-- HEALTH REPORTS
-- ============================================================

CREATE TABLE IF NOT EXISTS health_reports (

    id BIGSERIAL
        PRIMARY KEY,

    station_id VARCHAR(64)
        NOT NULL,

    cpu_usage DOUBLE PRECISION
        NOT NULL,

    ram_usage DOUBLE PRECISION
        NOT NULL,

    disk_usage DOUBLE PRECISION
        NOT NULL,

    temperature DOUBLE PRECISION
        NOT NULL,

    gps_status VARCHAR(32),

    network_status VARCHAR(32),

    uptime_seconds BIGINT,

    timestamp TIMESTAMP
        NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_health_station
ON health_reports(station_id);

CREATE INDEX IF NOT EXISTS idx_health_timestamp
ON health_reports(timestamp);

-- ============================================================
-- ALERT HISTORY
-- ============================================================

CREATE TABLE IF NOT EXISTS alert_records (

    alert_id VARCHAR(128)
        PRIMARY KEY,

    earthquake_id VARCHAR(128)
        NOT NULL,

    alert_type VARCHAR(64)
        NOT NULL,

    status VARCHAR(32)
        NOT NULL,

    message TEXT,

    created_at TIMESTAMP
        NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alert_earthquake
ON alert_records(earthquake_id);

CREATE INDEX IF NOT EXISTS idx_alert_created
ON alert_records(created_at);

-- ============================================================
-- HEARTBEAT HISTORY
-- ============================================================

CREATE TABLE IF NOT EXISTS heartbeat_reports (

    id BIGSERIAL
        PRIMARY KEY,

    station_id VARCHAR(64)
        NOT NULL,

    received_at TIMESTAMP
        NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_heartbeat_station
ON heartbeat_reports(station_id);

CREATE INDEX IF NOT EXISTS idx_heartbeat_received
ON heartbeat_reports(received_at);

-- ============================================================
-- ERROR REPORTS
-- ============================================================

CREATE TABLE IF NOT EXISTS error_reports (

    id BIGSERIAL
        PRIMARY KEY,

    station_id VARCHAR(64),

    packet_id VARCHAR(128),

    error_type VARCHAR(128),

    error_message TEXT,

    created_at TIMESTAMP
        NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_error_station
ON error_reports(station_id);

CREATE INDEX IF NOT EXISTS idx_error_created
ON error_reports(created_at);

-- ============================================================
-- SYSTEM REPORTS
-- ============================================================

CREATE TABLE IF NOT EXISTS system_reports (

    id BIGSERIAL
        PRIMARY KEY,

    station_id VARCHAR(64),

    severity VARCHAR(32),

    message TEXT,

    created_at TIMESTAMP
        NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_system_created
ON system_reports(created_at);

-- ============================================================
-- INITIAL STATIONS
-- DELHI METRO DEPLOYMENT
-- ============================================================

INSERT INTO stations
(
    station_id,
    station_name,
    latitude,
    longitude,
    elevation,
    status
)
VALUES

(
    'SSN_001',
    'Delhi_Metro_Station_01',
    28.6139,
    77.2090,
    216,
    'OFFLINE'
),

(
    'SSN_002',
    'Delhi_Metro_Station_02',
    28.6200,
    77.2150,
    216,
    'OFFLINE'
),

(
    'SSN_003',
    'Delhi_Metro_Station_03',
    28.6260,
    77.2210,
    216,
    'OFFLINE'
),

(
    'SSN_004',
    'Delhi_Metro_Station_04',
    28.6320,
    77.2270,
    216,
    'OFFLINE'
),

(
    'SSN_005',
    'Delhi_Metro_Station_05',
    28.6380,
    77.2330,
    216,
    'OFFLINE'
)

ON CONFLICT (station_id)
DO NOTHING;