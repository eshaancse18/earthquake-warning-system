"""
Station Simulator

Creates virtual station events from a real SSN event.

Purpose:
- Demonstrate a multi-station earthquake warning system
  using only one physical sensor.
"""

from __future__ import annotations

import copy
import json
import random
from datetime import timedelta

import paho.mqtt.publish as publish

from config.config import config
from logging_system.logger import logger


class StationSimulator:
    """
    Simulates additional SSNs.
    """

    def __init__(self) -> None:

        self.virtual_stations = [

            "SSN_002",

            "SSN_003",

            "SSN_004",

            "SSN_005"

        ]

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
            "event_topic"
        )

    # --------------------------------------------------

    def simulate(
        self,
        real_event: dict
    ) -> None:
        """
        Generate virtual station reports.
        """

        for station_id in self.virtual_stations:

            event = copy.deepcopy(real_event)

            event["station_id"] = station_id

            # ----------------------------
            # Timestamp jitter
            # ----------------------------

            event["timestamp"] = (

                event["timestamp"]

                +

                timedelta(

                    milliseconds=random.randint(
                        -80,
                        80
                    )

                )

            ).isoformat()

            # ----------------------------
            # Small sensor variations
            # ----------------------------

            event["pga"] *= random.uniform(
                0.95,
                1.05
            )

            event["sta_lta"] *= random.uniform(
                0.97,
                1.03
            )

            event["p_wave_confidence"] = min(

                1.0,

                event["p_wave_confidence"]

                *

                random.uniform(
                    0.97,
                    1.02
                )

            )

            # ----------------------------
            # Slight location offsets
            # (Prototype only)
            # ----------------------------

            event["latitude"] += random.uniform(
                -0.001,
                0.001
            )

            event["longitude"] += random.uniform(
                -0.001,
                0.001
            )

            try:

                publish.single(

                    topic=self.topic,

                    payload=json.dumps(event),

                    hostname=self.broker,

                    port=self.port

                )

                logger.info(

                    f"Virtual station "

                    f"{station_id} published."

                )

            except Exception:

                logger.exception(

                    f"Failed to publish "

                    f"{station_id}"

                )


station_simulator = StationSimulator()