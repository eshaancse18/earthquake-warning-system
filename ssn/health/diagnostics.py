import os
import sqlite3
import threading
import time
from datetime import datetime
from typing import Dict
from typing import List
from typing import Any


class Diagnostics:

    """
    System Diagnostics Engine

    Performs:

    1. Sensor Diagnostics
    2. GPS Diagnostics
    3. MQTT Diagnostics
    4. Database Diagnostics
    5. Storage Diagnostics
    6. Thread Diagnostics
    7. Memory Diagnostics
    8. Startup Validation
    """

    def __init__(
        self,
        sensor_reader,
        gps_reader,
        mqtt_client,
        local_database,
        waveform_storage,
        retry_manager=None
    ):

        self.sensor_reader = sensor_reader

        self.gps_reader = gps_reader

        self.mqtt_client = mqtt_client

        self.local_database = local_database

        self.waveform_storage = waveform_storage

        self.retry_manager = retry_manager

        self.last_run_time = None

    def run_all_checks(
        self
    ) -> Dict[str, Any]:

        report = {

            "timestamp":
                datetime.utcnow().isoformat(),

            "sensor":
                self.sensor_diagnostics(),

            "gps":
                self.gps_diagnostics(),

            "mqtt":
                self.mqtt_diagnostics(),

            "database":
                self.database_diagnostics(),

            "storage":
                self.storage_diagnostics(),

            "threads":
                self.thread_diagnostics(),

            "memory":
                self.memory_diagnostics()
        }

        self.last_run_time = (
            datetime.utcnow()
        )

        return report

    def sensor_diagnostics(
        self
    ) -> Dict[str, Any]:

        try:

            healthy = (
                self.sensor_reader
                .is_healthy()
            )

            stats = (
                self.sensor_reader
                .statistics()
            )

            return {

                "healthy":
                    healthy,

                "statistics":
                    stats
            }

        except Exception as error:

            return {

                "healthy":
                    False,

                "error":
                    str(error)
            }

    def gps_diagnostics(
        self
    ) -> Dict[str, Any]:

        try:

            healthy = (
                self.gps_reader
                .is_healthy()
            )

            stats = (
                self.gps_reader
                .statistics()
            )

            return {

                "healthy":
                    healthy,

                "statistics":
                    stats
            }

        except Exception as error:

            return {

                "healthy":
                    False,

                "error":
                    str(error)
            }

    def mqtt_diagnostics(
        self
    ) -> Dict[str, Any]:

        try:

            healthy = (
                self.mqtt_client
                .is_healthy()
            )

            stats = (
                self.mqtt_client
                .statistics()
            )

            return {

                "healthy":
                    healthy,

                "statistics":
                    stats
            }

        except Exception as error:

            return {

                "healthy":
                    False,

                "error":
                    str(error)
            }

    def database_diagnostics(
        self
    ) -> Dict[str, Any]:

        try:

            connection = sqlite3.connect(
                self.local_database.database_path
            )

            cursor = connection.cursor()

            cursor.execute(
                "SELECT 1"
            )

            cursor.fetchone()

            connection.close()

            return {

                "healthy":
                    True,

                "database_path":
                    self.local_database.database_path,

                "event_count":
                    self.local_database
                    .event_count(),

                "pending_packets":
                    self.local_database
                    .pending_packet_count()
            }

        except Exception as error:

            return {

                "healthy":
                    False,

                "error":
                    str(error)
            }

    def storage_diagnostics(
        self
    ) -> Dict[str, Any]:

        try:

            stats = (
                self.waveform_storage
                .statistics()
            )

            return {

                "healthy":
                    True,

                "statistics":
                    stats
            }

        except Exception as error:

            return {

                "healthy":
                    False,

                "error":
                    str(error)
            }

    def thread_diagnostics(
        self
    ) -> Dict[str, Any]:

        try:

            active_threads = (
                threading.enumerate()
            )

            thread_names = []

            for thread in active_threads:

                thread_names.append(
                    thread.name
                )

            return {

                "healthy":
                    True,

                "active_threads":
                    len(
                        active_threads
                    ),

                "thread_names":
                    thread_names
            }

        except Exception as error:

            return {

                "healthy":
                    False,

                "error":
                    str(error)
            }

    def memory_diagnostics(
        self
    ) -> Dict[str, Any]:

        try:

            import psutil

            process = (
                psutil.Process(
                    os.getpid()
                )
            )

            memory = (
                process.memory_info()
            )

            return {

                "healthy":
                    True,

                "rss_bytes":
                    memory.rss,

                "vms_bytes":
                    memory.vms
            }

        except Exception as error:

            return {

                "healthy":
                    False,

                "error":
                    str(error)
            }

    def startup_validation(
        self
    ) -> Dict[str, Any]:

        report = (
            self.run_all_checks()
        )

        failures = []

        for key, value in report.items():

            if key == "timestamp":

                continue

            if not value.get(
                "healthy",
                False
            ):

                failures.append(
                    key
                )

        return {

            "startup_passed":
                len(failures) == 0,

            "failed_components":
                failures,

            "report":
                report
        }

    def system_health_score(
        self
    ) -> float:

        report = (
            self.run_all_checks()
        )

        total = 0

        passed = 0

        for key, value in report.items():

            if key == "timestamp":

                continue

            total += 1

            if value.get(
                "healthy",
                False
            ):

                passed += 1

        if total == 0:

            return 0.0

        return round(
            passed / total,
            2
        )