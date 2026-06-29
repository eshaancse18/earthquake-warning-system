"""
Alert Manager

Responsible for generating alerts after an
earthquake has been confirmed.

Current Targets:
- Console
- Log
- MQTT
- Database

Future Targets:
- SMS
- Email
- Delhi Metro Control
- Mobile App
"""

from __future__ import annotations

import json

import paho.mqtt.publish as publish

from config.config import config
from logging_system.logger import logger


class AlertManager:

    def __init__(self):

        self.broker = config.get(
            "mqtt",
            "broker"
        )

        self.port = config.get(
            "mqtt",
            "port"
        )

        self.topic = config.get(
            "mqtt",
            "alert_topic"
        )

    # ----------------------------------------------

    def publish_alert(
        self,
        event_id: int,
        magnitude: float,
        latitude: float,
        longitude: float,
        confidence: float
    ) -> None:

        payload = {

            "event_id": event_id,

            "magnitude": magnitude,

            "latitude": latitude,

            "longitude": longitude,

            "confidence": confidence

        }

        try:

            publish.single(

                topic=self.topic,

                payload=json.dumps(payload),

                hostname=self.broker,

                port=self.port

            )

            logger.info(

                f"Alert published "

                f"Event={event_id}"

            )

        except Exception:

            logger.exception(

                "Failed to publish alert."

            )

    # ----------------------------------------------

    def metro_warning(
        self,
        magnitude: float
    ) -> bool:

        threshold = config.get(
            "alert",
            "minimum_magnitude"
        )

        return magnitude >= threshold

    # ----------------------------------------------

    def notify_console(
        self,
        event_id: int,
        magnitude: float
    ) -> None:

        print()

        print("=" * 60)

        print("EARTHQUAKE DETECTED")

        print(f"Event ID : {event_id}")

        print(f"Magnitude : {magnitude:.2f}")

        print("=" * 60)

        print()


alert_manager = AlertManager()