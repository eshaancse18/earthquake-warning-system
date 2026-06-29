import os
import time
import socket
import threading
from datetime import datetime
from typing import Dict
from typing import Any

import psutil

from logging_system.logger import HealthLogger
from communication.packet_builder import PacketBuilder


class HealthMonitor(threading.Thread):
    """
    Production Health Monitoring Thread

    Responsibilities:
    ----------------
    1. CPU Usage Monitoring
    2. RAM Usage Monitoring
    3. Disk Usage Monitoring
    4. CPU Temperature Monitoring
    5. Network Monitoring
    6. GPS Health Monitoring
    7. MQTT Health Monitoring
    8. Sensor Health Monitoring
    9. Thread Health Monitoring

    Reports are generated periodically and
    pushed to MQTT transmission queue.
    """

    def __init__(
        self,
        station_id: str,
        mqtt_client,
        gps_reader,
        sensor_reader,
        database,
        report_interval_seconds: int
    ):

        super().__init__(
            name="HEALTH_THREAD",
            daemon=True
        )

        self.station_id = station_id

        self.mqtt_client = mqtt_client

        self.gps_reader = gps_reader

        self.sensor_reader = sensor_reader

        self.database = database

        self.report_interval_seconds = (
            report_interval_seconds
        )

        self.logger = HealthLogger()

        self.stop_event = threading.Event()

        self.start_time = time.time()

        self.reports_sent = 0

    def stop(self) -> None:

        self.stop_event.set()

    def _cpu_usage(self) -> float:

        return float(
            psutil.cpu_percent(
                interval=1
            )
        )

    def _ram_usage(self) -> float:

        return float(
            psutil.virtual_memory().percent
        )

    def _disk_usage(self) -> float:

        return float(
            psutil.disk_usage(
                "/"
            ).percent
        )

    def _cpu_temperature(self) -> float:

        try:

            thermal_file = (
                "/sys/class/thermal/"
                "thermal_zone0/temp"
            )

            if os.path.exists(
                thermal_file
            ):

                with open(
                    thermal_file,
                    "r",
                    encoding="utf-8"
                ) as file:

                    value = (
                        float(
                            file.read().strip()
                        )
                    )

                    return value / 1000.0

        except Exception:

            pass

        return 0.0

    def _network_status(self) -> str:

        try:

            socket.create_connection(
                (
                    "8.8.8.8",
                    53
                ),
                timeout=2
            )

            return "CONNECTED"

        except Exception:

            return "DISCONNECTED"

    def _gps_status(self) -> str:

        try:

            if self.gps_reader is None:

                return "UNAVAILABLE"

            if self.gps_reader.is_locked():

                return "LOCKED"

            return "SEARCHING"

        except Exception:

            return "ERROR"

    def _mqtt_status(self) -> str:

        try:

            if self.mqtt_client.connected:

                return "CONNECTED"

            return "DISCONNECTED"

        except Exception:

            return "ERROR"

    def _sensor_status(self) -> str:

        try:

            if self.sensor_reader.is_healthy():

                return "HEALTHY"

            return "FAULT"

        except Exception:

            return "ERROR"

    def _uptime_seconds(self) -> int:

        return int(
            time.time()
            -
            self.start_time
        )

    def _thread_count(self) -> int:

        return threading.active_count()

    def _build_health_report(
        self
    ) -> Dict[str, Any]:

        report = {
            "station_id":
                self.station_id,

            "timestamp":
                datetime.utcnow()
                .isoformat(),

            "cpu_usage":
                self._cpu_usage(),

            "ram_usage":
                self._ram_usage(),

            "disk_usage":
                self._disk_usage(),

            "temperature":
                self._cpu_temperature(),

            "gps_status":
                self._gps_status(),

            "network_status":
                self._network_status(),

            "mqtt_status":
                self._mqtt_status(),

            "sensor_status":
                self._sensor_status(),

            "thread_count":
                self._thread_count(),

            "uptime_seconds":
                self._uptime_seconds()
        }

        return report

    def _transmit_report(
        self,
        report: Dict[str, Any]
    ) -> None:

        packet = (
            PacketBuilder
            .build_health_packet(
                station_id=self.station_id,

                cpu_usage=report[
                    "cpu_usage"
                ],

                ram_usage=report[
                    "ram_usage"
                ],

                disk_usage=report[
                    "disk_usage"
                ],

                temperature=report[
                    "temperature"
                ],

                gps_status=report[
                    "gps_status"
                ],

                network_status=report[
                    "network_status"
                ],

                uptime_seconds=report[
                    "uptime_seconds"
                ]
            )
        )

        self.mqtt_client.publish_health(
            packet
        )

    def run(self) -> None:

        while not self.stop_event.is_set():

            try:

                report = (
                    self._build_health_report()
                )

                self.database.save_health_report(
                    report
                )

                self._transmit_report(
                    report
                )

                self.logger.report(
                    cpu_usage=report[
                        "cpu_usage"
                    ],

                    ram_usage=report[
                        "ram_usage"
                    ],

                    disk_usage=report[
                        "disk_usage"
                    ],

                    temperature=report[
                        "temperature"
                    ]
                )

                self.reports_sent += 1

            except Exception as error:

                self.logger.logger.exception(
                    (
                        "Health monitoring "
                        f"failure: {error}"
                    )
                )

            self.stop_event.wait(
                self.report_interval_seconds
            )

    def statistics(
        self
    ) -> Dict[str, Any]:

        return {
            "reports_sent":
                self.reports_sent,

            "uptime_seconds":
                self._uptime_seconds(),

            "report_interval":
                self.report_interval_seconds
        }

    def current_snapshot(
        self
    ) -> Dict[str, Any]:

        return self._build_health_report()