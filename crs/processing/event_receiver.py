"""
Event Receiver

Receives validated MQTT event payloads
and forwards them to the EventManager.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from logging_system.logger import logger


class EventReceiver:

    REQUIRED_FIELDS = [

        "station_id",

        "timestamp",

        "pga",

        "sta_lta",

        "p_wave_confidence",

        "latitude",

        "longitude",

        "elevation"
    ]

    def __init__(
        self,
        event_manager
    ) -> None:

        self.event_manager = event_manager

    # --------------------------------------------------

    def handle_event(
        self,
        payload: dict[str, Any]
    ) -> None:

        if not self._validate(payload):

            logger.warning(
                "Rejected invalid payload."
            )

            return

        event = self._normalize(payload)

        logger.info(

            f"Validated event "

            f"from {event['station_id']}"

        )

        self.event_manager.process_event(
            event
        )

    # --------------------------------------------------

    def _validate(
        self,
        payload: dict
    ) -> bool:

        for field in self.REQUIRED_FIELDS:

            if field not in payload:

                logger.error(
                    f"Missing field {field}"
                )

                return False

        return True

    # --------------------------------------------------

    def _normalize(
        self,
        payload: dict
    ) -> dict:

        timestamp = payload["timestamp"]

        if isinstance(timestamp, str):

            timestamp = datetime.fromisoformat(
                timestamp
            )

        return {

            "station_id":
                payload["station_id"],

            "timestamp":
                timestamp,

            "latitude":
                float(payload["latitude"]),

            "longitude":
                float(payload["longitude"]),

            "elevation":
                float(payload["elevation"]),

            "pga":
                float(payload["pga"]),

            "sta_lta":
                float(payload["sta_lta"]),

            "p_wave_confidence":
                float(
                    payload["p_wave_confidence"]
                ),

            "waveform_path":
                payload.get(
                    "waveform_path"
                ),

            "metadata":
                payload.get(
                    "metadata",
                    {}
                )
        }