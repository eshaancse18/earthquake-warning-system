from enum import Enum


# ============================================================
# APPLICATION INFORMATION
# ============================================================

APPLICATION_NAME = (
    "Earthquake Warning System"
)

APPLICATION_VERSION = (
    "1.0.0"
)

APPLICATION_AUTHOR = (
    "CSIO Delhi Metro Project"
)


# ============================================================
# SENSOR STATES
# ============================================================

class SensorState(Enum):

    INITIALIZING = "INITIALIZING"

    READY = "READY"

    ACQUIRING = "ACQUIRING"

    BUFFERING = "BUFFERING"

    FILTERING = "FILTERING"

    DETECTING = "DETECTING"

    EVENT_DETECTED = (
        "EVENT_DETECTED"
    )

    EVENT_CONFIRMED = (
        "EVENT_CONFIRMED"
    )

    TRANSFERRING = (
        "TRANSFERRING"
    )

    HEALTH_CHECK = (
        "HEALTH_CHECK"
    )

    ERROR = "ERROR"

    RESTARTING = "RESTARTING"


# ============================================================
# EVENT STATES
# ============================================================

class EventState(Enum):

    NO_EVENT = "NO_EVENT"

    EVENT_SNIFFED = (
        "EVENT_SNIFFED"
    )

    EVENT_ACTIVE = (
        "EVENT_ACTIVE"
    )

    POST_EVENT = (
        "POST_EVENT"
    )

    EVENT_CONFIRMED = (
        "EVENT_CONFIRMED"
    )

    EVENT_REJECTED = (
        "EVENT_REJECTED"
    )

    EVENT_FINISHED = (
        "EVENT_FINISHED"
    )


# ============================================================
# HEALTH STATES
# ============================================================

class HealthStatus(Enum):

    HEALTHY = "HEALTHY"

    WARNING = "WARNING"

    CRITICAL = "CRITICAL"

    OFFLINE = "OFFLINE"


# ============================================================
# MESSAGE TYPES
# ============================================================

class MessageType(Enum):

    EVENT = "EVENT"

    HEALTH = "HEALTH"

    HEARTBEAT = "HEARTBEAT"

    ACKNOWLEDGEMENT = (
        "ACKNOWLEDGEMENT"
    )

    ERROR = "ERROR"

    SYSTEM = "SYSTEM"


# ============================================================
# GPS STATES
# ============================================================

class GPSStatus(Enum):

    LOCKED = "LOCKED"

    SEARCHING = "SEARCHING"

    DISCONNECTED = (
        "DISCONNECTED"
    )


# ============================================================
# NETWORK STATES
# ============================================================

class NetworkStatus(Enum):

    CONNECTED = "CONNECTED"

    DISCONNECTED = (
        "DISCONNECTED"
    )

    RECONNECTING = (
        "RECONNECTING"
    )


# ============================================================
# DETECTION TYPES
# ============================================================

class DetectionMethod(Enum):

    STALTA = "STALTA"

    PGA = "PGA"

    FREQUENCY = (
        "FREQUENCY"
    )

    PWAVE = "PWAVE"

    COMBINED = "COMBINED"


# ============================================================
# THREAD NAMES
# ============================================================

THREAD_ADC_READER = (
    "ADC_READER_THREAD"
)

THREAD_SENSOR_MANAGER = (
    "SENSOR_MANAGER_THREAD"
)

THREAD_FILTER = (
    "FILTER_THREAD"
)

THREAD_EVENT_DETECTOR = (
    "EVENT_DETECTOR_THREAD"
)

THREAD_MQTT = (
    "MQTT_THREAD"
)

THREAD_HEALTH = (
    "HEALTH_THREAD"
)

THREAD_GPS = (
    "GPS_THREAD"
)

THREAD_STORAGE = (
    "STORAGE_THREAD"
)

THREAD_WATCHDOG = (
    "WATCHDOG_THREAD"
)

THREAD_CRS = (
    "CRS_THREAD"
)


# ============================================================
# QUEUE LIMITS
# ============================================================

RAW_SAMPLE_QUEUE_SIZE = (
    5000
)

FILTERED_SAMPLE_QUEUE_SIZE = (
    5000
)

EVENT_QUEUE_SIZE = (
    1000
)

HEALTH_QUEUE_SIZE = (
    1000
)

TRANSMISSION_QUEUE_SIZE = (
    1000
)


# ============================================================
# BUFFER DEFAULTS
# ============================================================

DEFAULT_PRE_EVENT_SECONDS = (
    30
)

DEFAULT_EVENT_SECONDS = (
    60
)

DEFAULT_POST_EVENT_SECONDS = (
    30
)


# ============================================================
# SAMPLING CONFIGURATION
# ============================================================

MINIMUM_SAMPLING_RATE = (
    50
)

MAXIMUM_SAMPLING_RATE = (
    2000
)

DEFAULT_SAMPLING_RATE = (
    200
)


# ============================================================
# STALTA CONFIGURATION
# ============================================================

DEFAULT_STA_WINDOW_SECONDS = (
    1.0
)

DEFAULT_LTA_WINDOW_SECONDS = (
    10.0
)

DEFAULT_STALTA_THRESHOLD = (
    3.5
)


# ============================================================
# PGA CONFIGURATION
# ============================================================

DEFAULT_PGA_THRESHOLD = (
    0.08
)


# ============================================================
# FREQUENCY FILTERING
# ============================================================

DEFAULT_LOW_CUTOFF_FREQUENCY = (
    0.5
)

DEFAULT_HIGH_CUTOFF_FREQUENCY = (
    20.0
)
# ============================================================
# MQTT CONFIGURATION
# ============================================================

MQTT_QOS_0 = 0

MQTT_QOS_1 = 1

MQTT_QOS_2 = 2

DEFAULT_KEEPALIVE_SECONDS = (
    60
)

MQTT_RECONNECT_DELAY_SECONDS = (
    5
)


# ============================================================
# HEALTH MONITORING
# ============================================================

DEFAULT_HEALTH_REPORT_INTERVAL = (
    30
)

CPU_CRITICAL_THRESHOLD = (
    95.0
)

RAM_CRITICAL_THRESHOLD = (
    95.0
)

DISK_CRITICAL_THRESHOLD = (
    95.0
)

TEMPERATURE_CRITICAL_THRESHOLD = (
    80.0
)

GPS_HEALTH_TIMEOUT_SECONDS = (
    30
)

MAX_SENSOR_READ_ERRORS = (
    100
)

MAX_GPS_PARSE_ERRORS = (
    100
)


# ============================================================
# WATCHDOG SETTINGS
# ============================================================

WATCHDOG_CHECK_INTERVAL = (
    10
)

WATCHDOG_TIMEOUT_SECONDS = (
    60
)


# ============================================================
# RETRY SETTINGS
# ============================================================

MAX_RETRY_ATTEMPTS = (
    5
)

RETRY_DELAY_SECONDS = (
    5
)


# ============================================================
# EVENT CONFIRMATION
# ============================================================

MINIMUM_CONFIRMATION_VOTES = (
    2
)

MAX_EVENT_CONFIRMATION_TIME_SECONDS = (
    5
)


# ============================================================
# FILE SYSTEM
# ============================================================

LOG_DIRECTORY = (
    "logs"
)

WAVEFORM_DIRECTORY = (
    "waveforms"
)

DATABASE_DIRECTORY = (
    "database"
)

MAX_LOCAL_EVENTS = (
    1000
)


# ============================================================
# LOGGING FORMATS
# ============================================================

LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(threadName)s | "
    "%(name)s | "
    "%(message)s"
)

LOG_DATE_FORMAT = (
    "%Y-%m-%d %H:%M:%S"
)


# ============================================================
# EVENT FILE PREFIXES
# ============================================================

EVENT_FILE_PREFIX = (
    "event"
)

WAVEFORM_FILE_PREFIX = (
    "waveform"
)

HEALTH_FILE_PREFIX = (
    "health"
)


# ============================================================
# SYSTEM EXIT CODES
# ============================================================

EXIT_SUCCESS = 0

EXIT_CONFIGURATION_ERROR = 1

EXIT_SENSOR_ERROR = 2

EXIT_COMMUNICATION_ERROR = 3

EXIT_DATABASE_ERROR = 4

EXIT_FATAL_ERROR = 99


# ============================================================
# CRS COMMUNICATION KEYS
# ============================================================

KEY_EVENT_ID = (
    "event_id"
)

KEY_STATION_ID = (
    "station_id"
)

KEY_TIMESTAMP = (
    "timestamp"
)

KEY_WAVEFORM = (
    "waveform"
)

KEY_PGA = (
    "pga"
)

KEY_STALTA = (
    "stalta"
)

KEY_CONFIDENCE = (
    "confidence"
)

KEY_HEALTH = (
    "health"
)

KEY_GPS_STATUS = (
    "gps_status"
)

KEY_CPU_USAGE = (
    "cpu_usage"
)

KEY_RAM_USAGE = (
    "ram_usage"
)

KEY_DISK_USAGE = (
    "disk_usage"
)

KEY_TEMPERATURE = (
    "temperature"
)


# ============================================================
# EVENT DETECTION DEFAULTS
# ============================================================

DEFAULT_EVENT_CONFIDENCE = (
    0.75
)

DEFAULT_PWAVE_TRIGGER_RATIO = (
    4.0
)

DEFAULT_PWAVE_CONFIDENCE = (
    0.70
)


# ============================================================
# WAVEFORM STORAGE
# ============================================================

CSV_EXTENSION = ".csv"

JSON_EXTENSION = ".json"


# ============================================================
# EARTHQUAKE FREQUENCY BAND
# ============================================================

EARTHQUAKE_MIN_FREQUENCY_HZ = (
    0.5
)

EARTHQUAKE_MAX_FREQUENCY_HZ = (
    20.0
)


# ============================================================
# CRS CORRELATION SETTINGS
# ============================================================

DEFAULT_CORRELATION_WINDOW_MS = (
    5000
)

DEFAULT_STATION_TIMEOUT_SECONDS = (
    30
)