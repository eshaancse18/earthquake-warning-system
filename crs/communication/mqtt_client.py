"""
MQTT Client for the Central Receiving Server (CRS).

Responsibilities:
- Connect to the MQTT broker
- Subscribe to configured topics
- Receive messages
- Forward payloads to registered callbacks
"""

from __future__ import annotations

import json
from typing import Callable, Optional

import paho.mqtt.client as mqtt

from config.config import config
from logging_system.logger import logger


class MQTTClient:
    """
    Central MQTT client used by the CRS.
    """

    def __init__(self) -> None:

        self.client = mqtt.Client()

        username = config.get("mqtt", "username")
        password = config.get("mqtt", "password")

        if username:
            self.client.username_pw_set(
                username=username,
                password=password
            )

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self.event_callback: Optional[
            Callable[[dict], None]
        ] = None

        self.health_callback: Optional[
            Callable[[dict], None]
        ] = None

    # --------------------------------------------------
    # Callback Registration
    # --------------------------------------------------

    def register_event_callback(
        self,
        callback: Callable[[dict], None]
    ) -> None:

        self.event_callback = callback

    def register_health_callback(
        self,
        callback: Callable[[dict], None]
    ) -> None:

        self.health_callback = callback

    # --------------------------------------------------
    # Connection
    # --------------------------------------------------

    def connect(self) -> None:

        logger.info("Connecting to MQTT broker...")

        self.client.connect(
            host=config.get("mqtt", "broker"),
            port=config.get("mqtt", "port"),
            keepalive=config.get("mqtt", "keepalive")
        )

    def start(self) -> None:

        logger.info("Starting MQTT loop...")

        self.client.loop_forever()

    # --------------------------------------------------
    # MQTT Callbacks
    # --------------------------------------------------

    def _on_connect(
        self,
        client,
        userdata,
        flags,
        rc
    ) -> None:

        if rc != 0:

            logger.error(
                "Failed to connect to MQTT broker "
                f"(code={rc})"
            )

            return

        logger.info("Connected to MQTT broker.")

        event_topic = config.get(
            "mqtt",
            "event_topic"
        )

        health_topic = config.get(
            "mqtt",
            "health_topic"
        )

        qos = config.get("mqtt", "qos")

        client.subscribe(event_topic, qos=qos)
        client.subscribe(health_topic, qos=qos)

        logger.info(
            "Subscribed to MQTT topics."
        )

    def _on_disconnect(
        self,
        client,
        userdata,
        rc
    ) -> None:

        logger.warning(
            "Disconnected from MQTT broker."
        )

    def _on_message(
        self,
        client,
        userdata,
        msg
    ) -> None:

        try:

            payload = json.loads(
                msg.payload.decode()
            )

        except Exception:

            logger.exception(
                "Invalid JSON received."
            )

            return

        if msg.topic == config.get(
        "mqtt",
        "event_topic"
    ):

            logger.info(
                f"Event packet received from "
                f"{payload.get('station_id')}"
            )

            event_payload = payload.get("payload", {})

            if self.event_callback:
                self.event_callback(event_payload)

        elif msg.topic == config.get(
            "mqtt",
            "health_topic"
        ):

            logger.info(
                f"Health report received from "
                f"{payload.get('station_id')}"
            )

            if self.health_callback:
                self.health_callback(payload)