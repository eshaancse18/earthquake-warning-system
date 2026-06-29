import json
import logging
import os
import threading
from datetime import datetime
from typing import Dict
from typing import Any
from logging.handlers import RotatingFileHandler


class EventLogger:
    """
    Dedicated Earthquake Event Logger

    Separate from:

    - System Logs
    - Health Logs
    - MQTT Logs

    Stores:

    - Event Detection
    - Event Confirmation
    - Event Rejection
    - Voting Results
    - Waveform Metadata
    """

    def __init__(
        self,
        log_directory: str = "logs/events"
    ):

        self.log_directory = (
            os.path.abspath(
                log_directory
            )
        )

        os.makedirs(
            self.log_directory,
            exist_ok=True
        )

        self.lock = threading.Lock()

        self.logger = logging.getLogger(
            "EVENT_LOGGER"
        )

        self.logger.setLevel(
            logging.INFO
        )

        if not self.logger.handlers:

            log_file = os.path.join(
                self.log_directory,
                "events.log"
            )

            handler = (
                RotatingFileHandler(
                    filename=log_file,
                    maxBytes=50 * 1024 * 1024,
                    backupCount=20,
                    encoding="utf-8"
                )
            )

            formatter = logging.Formatter(
                (
                    "%(asctime)s | "
                    "%(levelname)s | "
                    "%(message)s"
                )
            )

            handler.setFormatter(
                formatter
            )

            self.logger.addHandler(
                handler
            )

    def event_detected(
        self,
        event_id: str,
        station_id: str,
        pga: float,
        stalta_ratio: float
    ) -> None:

        payload = {

            "action":
                "EVENT_DETECTED",

            "event_id":
                event_id,

            "station_id":
                station_id,

            "pga":
                pga,

            "stalta_ratio":
                stalta_ratio,

            "timestamp":
                datetime.utcnow()
                .isoformat()
        }

        self._write(
            payload
        )

    def event_confirmed(
        self,
        event_id: str,
        station_id: str,
        confidence: float
    ) -> None:

        payload = {

            "action":
                "EVENT_CONFIRMED",

            "event_id":
                event_id,

            "station_id":
                station_id,

            "confidence":
                confidence,

            "timestamp":
                datetime.utcnow()
                .isoformat()
        }

        self._write(
            payload
        )

    def event_rejected(
        self,
        station_id: str,
        reason: str,
        confidence: float
    ) -> None:

        payload = {

            "action":
                "EVENT_REJECTED",

            "station_id":
                station_id,

            "reason":
                reason,

            "confidence":
                confidence,

            "timestamp":
                datetime.utcnow()
                .isoformat()
        }

        self._write(
            payload
        )

    def waveform_saved(
        self,
        event_id: str,
        csv_path: str,
        json_path: str
    ) -> None:

        payload = {

            "action":
                "WAVEFORM_SAVED",

            "event_id":
                event_id,

            "csv_path":
                csv_path,

            "json_path":
                json_path,

            "timestamp":
                datetime.utcnow()
                .isoformat()
        }

        self._write(
            payload
        )

    def packet_transmitted(
        self,
        event_id: str,
        packet_id: str
    ) -> None:

        payload = {

            "action":
                "PACKET_TRANSMITTED",

            "event_id":
                event_id,

            "packet_id":
                packet_id,

            "timestamp":
                datetime.utcnow()
                .isoformat()
        }

        self._write(
            payload
        )

    def packet_failed(
        self,
        event_id: str,
        reason: str
    ) -> None:

        payload = {

            "action":
                "PACKET_FAILED",

            "event_id":
                event_id,

            "reason":
                reason,

            "timestamp":
                datetime.utcnow()
                .isoformat()
        }

        self._write(
            payload
        )

    def voting_result(
        self,
        event_id: str,
        station_count: int,
        vote_result: bool
    ) -> None:

        payload = {

            "action":
                "VOTING_RESULT",

            "event_id":
                event_id,

            "station_count":
                station_count,

            "vote_result":
                vote_result,

            "timestamp":
                datetime.utcnow()
                .isoformat()
        }

        self._write(
            payload
        )

    def custom_event(
        self,
        event_type: str,
        data: Dict[str, Any]
    ) -> None:

        payload = {

            "action":
                event_type,

            "data":
                data,

            "timestamp":
                datetime.utcnow()
                .isoformat()
        }

        self._write(
            payload
        )

    def _write(
        self,
        payload: Dict[str, Any]
    ) -> None:

        with self.lock:

            self.logger.info(
                json.dumps(
                    payload,
                    ensure_ascii=False
                )
            )

    def statistics(
        self
    ) -> Dict[str, Any]:

        log_file = os.path.join(
            self.log_directory,
            "events.log"
        )

        file_size = 0

        if os.path.exists(
            log_file
        ):

            file_size = (
                os.path.getsize(
                    log_file
                )
            )

        return {

            "log_directory":
                self.log_directory,

            "log_file":
                log_file,

            "file_size_bytes":
                file_size
        }