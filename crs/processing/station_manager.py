"""
Station Manager

Maintains the health and status of all SSNs
connected to the Central Receiving Server.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict

from database.database import database
from logging_system.logger import logger


class StationManager:
    """
    Tracks station status and health.
    """

    def __init__(self) -> None:

        self.stations: Dict[str, dict] = {}

        self.timeout = timedelta(seconds=30)

    # --------------------------------------------------

    def handle_health_report(
        self,
        report: dict
    ) -> None:
        """
        Process a health packet received from an SSN.
        """

        station_id = report["station_id"]

        now = datetime.utcnow()

        self.stations[station_id] = {

            "last_seen": now,

            "cpu_usage": report.get("cpu_usage"),

            "memory_usage": report.get("memory_usage"),

            "disk_usage": report.get("disk_usage"),

            "cpu_temperature": report.get("cpu_temperature"),

            "gps_locked": report.get("gps_locked"),

            "sensor_status": report.get("sensor_status"),

            "mqtt_connected": report.get("mqtt_connected")

        }

        self._update_database(
            station_id,
            report
        )

        logger.info(
            f"Health updated: {station_id}"
        )

    # --------------------------------------------------
# postgres sql
    # def _update_database(
    #     self,
    #     station_id: str,
    #     report: dict
    # ) -> None:
    #     """
    #     Save latest health information.
    #     """

    #     database.execute(
    #         """
    #         INSERT INTO station_health
    #         (
    #             station_id,
    #             cpu_usage,
    #             memory_usage,
    #             disk_usage,
    #             cpu_temperature,
    #             gps_locked,
    #             sensor_status,
    #             mqtt_connected,
    #             timestamp
    #         )
    #         VALUES
    #         (
    #             %s,%s,%s,%s,%s,%s,%s,%s,NOW()
    #         )
    #         """,
    #         (
    #             station_id,

    #             report.get("cpu_usage"),

    #             report.get("memory_usage"),

    #             report.get("disk_usage"),

    #             report.get("cpu_temperature"),

    #             report.get("gps_locked"),

    #             report.get("sensor_status"),

    #             report.get("mqtt_connected")
    #         )
    #     )

    # --------------------------------------------------

    def _update_database(
    self,
    station_id: str,
    report: dict
    ) -> None:
        """
        Save latest health information.
        """

        database.execute(
            """
            INSERT INTO station_health
            (
                station_id,
                cpu_usage,
                memory_usage,
                disk_usage,
                cpu_temperature,
                gps_locked,
                sensor_status,
                mqtt_connected,
                timestamp
            )
            VALUES
            (
                ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP
            )
            """,
            (
                station_id,
                report.get("cpu_usage"),
                report.get("memory_usage"),
                report.get("disk_usage"),
                report.get("cpu_temperature"),
                report.get("gps_locked"),
                report.get("sensor_status"),
                report.get("mqtt_connected")
            )
        )

    def get_station(
        self,
        station_id: str
    ) -> dict | None:

        return self.stations.get(station_id)

    # --------------------------------------------------

    def get_all_stations(
        self
    ) -> Dict[str, dict]:

        return self.stations

    # --------------------------------------------------

    def check_timeouts(
        self
    ) -> None:
        """
        Mark stations as offline if they have not
        sent a recent health packet.
        """

        now = datetime.utcnow()

        for station_id, info in self.stations.items():

            if now - info["last_seen"] > self.timeout:

                logger.warning(
                    f"{station_id} is OFFLINE"
                )


station_manager = StationManager()