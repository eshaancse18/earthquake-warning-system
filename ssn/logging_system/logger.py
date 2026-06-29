import logging
import logging.handlers
import os
import sys
from threading import Lock

from config.station_config import get_config
from utils.constants import (
    LOG_FORMAT,
    LOG_DATE_FORMAT
)


_logger_lock = Lock()

_initialized = False


def initialize_logging() -> None:

    global _initialized

    with _logger_lock:

        if _initialized:
            return

        config = get_config()

        log_file = config.logging.log_file

        log_level = config.logging.log_level.upper()

        log_directory = os.path.dirname(log_file)

        if log_directory:
            os.makedirs(log_directory, exist_ok=True)

        root_logger = logging.getLogger()

        root_logger.setLevel(_get_log_level(log_level))

        root_logger.handlers.clear()

        formatter = logging.Formatter(
            fmt=LOG_FORMAT,
            datefmt=LOG_DATE_FORMAT
        )

        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=20 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8"
        )

        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler(sys.stdout)

        console_handler.setFormatter(formatter)

        root_logger.addHandler(file_handler)

        root_logger.addHandler(console_handler)

        logging.captureWarnings(True)

        _initialized = True


def get_logger(name: str) -> logging.Logger:

    if not _initialized:
        initialize_logging()

    return logging.getLogger(name)


def _get_log_level(level_name: str) -> int:

    mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    return mapping.get(level_name, logging.INFO)


class LoggerMixin:

    @property
    def logger(self) -> logging.Logger:

        return get_logger(self.__class__.__name__)


class EventLogger:

    def __init__(self) -> None:

        self.logger = get_logger("EVENT")

    def event_detected(
        self,
        event_id: str,
        station_id: str,
        pga: float,
        stalta_ratio: float
    ) -> None:

        self.logger.info(
            (
                "EVENT_DETECTED | "
                f"event_id={event_id} | "
                f"station_id={station_id} | "
                f"pga={pga:.6f} | "
                f"stalta={stalta_ratio:.6f}"
            )
        )

    def event_confirmed(
        self,
        event_id: str,
        station_id: str,
        confidence: float
    ) -> None:

        self.logger.info(
            (
                "EVENT_CONFIRMED | "
                f"event_id={event_id} | "
                f"station_id={station_id} | "
                f"confidence={confidence:.4f}"
            )
        )

    def event_rejected(
        self,
        event_id: str,
        station_id: str,
        reason: str
    ) -> None:

        self.logger.warning(
            (
                "EVENT_REJECTED | "
                f"event_id={event_id} | "
                f"station_id={station_id} | "
                f"reason={reason}"
            )
        )


class HealthLogger:

    def __init__(self) -> None:

        self.logger = get_logger("HEALTH")

    def report(
        self,
        cpu_usage: float,
        ram_usage: float,
        disk_usage: float,
        temperature: float
    ) -> None:

        self.logger.info(
            (
                "HEALTH_REPORT | "
                f"cpu={cpu_usage:.2f} | "
                f"ram={ram_usage:.2f} | "
                f"disk={disk_usage:.2f} | "
                f"temperature={temperature:.2f}"
            )
        )


class CommunicationLogger:

    def __init__(self) -> None:

        self.logger = get_logger("COMMUNICATION")

    def mqtt_connected(self) -> None:

        self.logger.info("MQTT_CONNECTED")

    def mqtt_disconnected(self) -> None:

        self.logger.warning("MQTT_DISCONNECTED")

    def packet_sent(
        self,
        topic: str,
        packet_size: int
    ) -> None:

        self.logger.info(
            (
                "PACKET_SENT | "
                f"topic={topic} | "
                f"bytes={packet_size}"
            )
        )

    def packet_failed(
        self,
        topic: str,
        error: str
    ) -> None:

        self.logger.error(
            (
                "PACKET_FAILED | "
                f"topic={topic} | "
                f"error={error}"
            )
        )


class SensorLogger:

    def __init__(self) -> None:

        self.logger = get_logger("SENSOR")

    def acquisition_started(self) -> None:

        self.logger.info("DATA_ACQUISITION_STARTED")

    def acquisition_stopped(self) -> None:

        self.logger.warning("DATA_ACQUISITION_STOPPED")

    def sensor_error(
        self,
        error: str
    ) -> None:

        self.logger.error(
            f"SENSOR_ERROR | {error}"
        )


class GPSLogger:

    def __init__(self) -> None:

        self.logger = get_logger("GPS")

    def gps_locked(self) -> None:

        self.logger.info("GPS_LOCKED")

    def gps_searching(self) -> None:

        self.logger.warning("GPS_SEARCHING")

    def gps_disconnected(self) -> None:

        self.logger.error("GPS_DISCONNECTED")


class SystemLogger:

    def __init__(self) -> None:

        self.logger = get_logger("SYSTEM")

    def startup(self) -> None:

        self.logger.info(
            "SYSTEM_STARTUP"
        )

    def shutdown(self) -> None:

        self.logger.info(
            "SYSTEM_SHUTDOWN"
        )

    def restart(self) -> None:

        self.logger.warning(
            "SYSTEM_RESTART"
        )

    def fatal(
        self,
        error: str
    ) -> None:

        self.logger.critical(
            f"FATAL_ERROR | {error}"
        )