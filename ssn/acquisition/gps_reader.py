import threading
import time

from datetime import datetime
from datetime import timezone
from datetime import timedelta

from typing import Dict
from typing import Optional

import serial
import pynmea2

from logging_system.logger import GPSLogger
from utils.constants import GPSStatus


class GPSReader(threading.Thread):
    """
    Production GPS Time Synchronization Module

    Hardware
    --------
    u-blox NEO-M8N

    Responsibilities
    ----------------
    1. Read NMEA messages
    2. Maintain GPS lock state
    3. Provide UTC synchronized timestamps
    4. Provide location information
    5. Detect GPS failures
    6. Support earthquake event correlation
    7. Support CRS station synchronization
    """

    def __init__(
        self,
        serial_port: str,
        baud_rate: int
    ):

        super().__init__(
            name="GPS_THREAD",
            daemon=True
        )

        self.serial_port = serial_port

        self.baud_rate = baud_rate

        self.logger = GPSLogger()

        self.stop_event = threading.Event()

        self.data_lock = threading.RLock()

        self.serial_connection = None

        self.gps_status = (
            GPSStatus.DISCONNECTED
        )

        self.last_fix_time = None

        self.last_nmea_receive_time = None

        self.last_gps_timestamp = None

        self.latitude = None

        self.longitude = None

        self.altitude = None

        self.satellites = 0

        self.messages_received = 0

        self.parse_errors = 0

        self.reconnect_count = 0

        self.last_logged_status = (
            GPSStatus.DISCONNECTED
        )

        self._connect()

    def _utc_now(
        self
    ) -> datetime:

        return datetime.now(
            timezone.utc
        )

    def _connect(
        self
    ) -> None:

        try:

            self.serial_connection = (
                serial.Serial(
                    port=self.serial_port,
                    baudrate=self.baud_rate,
                    timeout=1
                )
            )

            with self.data_lock:

                self.gps_status = (
                    GPSStatus.SEARCHING
                )

            if (
                self.last_logged_status
                !=
                GPSStatus.SEARCHING
            ):

                self.logger.gps_searching()

                self.last_logged_status = (
                    GPSStatus.SEARCHING
                )

        except Exception as error:

            with self.data_lock:

                self.gps_status = (
                    GPSStatus.DISCONNECTED
                )

            if (
                self.last_logged_status
                !=
                GPSStatus.DISCONNECTED
            ):

                self.logger.gps_disconnected()

                self.last_logged_status = (
                    GPSStatus.DISCONNECTED
                )

            raise RuntimeError(
                f"GPS connection failed: {error}"
            )

    def stop(
        self
    ) -> None:

        self.stop_event.set()

    def _process_rmc(
        self,
        message
    ) -> None:

        try:

            if (
                hasattr(
                    message,
                    "status"
                )
                and
                message.status == "A"
            ):

                with self.data_lock:

                    previous_status = (
                        self.gps_status
                    )

                    self.last_fix_time = (
                        self._utc_now()
                    )

                    self.gps_status = (
                        GPSStatus.LOCKED
                    )

                if (
                    previous_status
                    !=
                    GPSStatus.LOCKED
                ):

                    self.logger.gps_locked()

                    self.last_logged_status = (
                        GPSStatus.LOCKED
                    )

                if (
                    message.datestamp
                    and
                    message.timestamp
                ):

                    gps_time = (
                        datetime.combine(
                            message.datestamp,
                            message.timestamp
                        )
                    )

                    gps_time = (
                        gps_time.replace(
                            tzinfo=timezone.utc
                        )
                    )

                    with self.data_lock:

                        self.last_gps_timestamp = (
                            gps_time
                        )

        except Exception:

            with self.data_lock:

                self.parse_errors += 1

    def _process_gga(
        self,
        message
    ) -> None:

        try:

            with self.data_lock:

                self.latitude = (
                    float(message.latitude)
                    if message.latitude
                    else None
                )

                self.longitude = (
                    float(message.longitude)
                    if message.longitude
                    else None
                )

                self.altitude = (
                    float(message.altitude)
                    if message.altitude
                    else None
                )

                self.satellites = (
                    int(message.num_sats)
                    if message.num_sats
                    else 0
                )

        except Exception:

            with self.data_lock:

                self.parse_errors += 1

    def _handle_message(
        self,
        raw_sentence: str
    ) -> None:

        try:

            message = (
                pynmea2.parse(
                    raw_sentence
                )
            )

            with self.data_lock:

                self.messages_received += 1

                self.last_nmea_receive_time = (
                    self._utc_now()
                )

            sentence_type = (
                message.sentence_type
            )

            if sentence_type == "RMC":

                self._process_rmc(
                    message
                )

            elif sentence_type == "GGA":

                self._process_gga(
                    message
                )

        except Exception:

            with self.data_lock:

                self.parse_errors += 1

    def get_timestamp(
        self
    ) -> datetime:
        """
        Returns GPS synchronized UTC time.

        If GPS lock becomes stale,
        fallback to local UTC clock.
        """

        with self.data_lock:

            gps_time = (
                self.last_gps_timestamp
            )

            fix_time = (
                self.last_fix_time
            )

            status = (
                self.gps_status
            )

        if (
            status == GPSStatus.LOCKED
            and
            gps_time is not None
            and
            fix_time is not None
        ):

            age = (
                self._utc_now()
                -
                fix_time
            ).total_seconds()

            if age > 10:

                return self._utc_now()

            elapsed = (
                self._utc_now()
                -
                fix_time
            )

            return (
                gps_time
                +
                elapsed
            )

        return self._utc_now()

    def get_location(
        self
    ) -> Dict:

        with self.data_lock:

            return {

                "latitude":
                    self.latitude,

                "longitude":
                    self.longitude,

                "altitude":
                    self.altitude,

                "satellites":
                    self.satellites
            }

    def get_latitude(
        self
    ) -> Optional[float]:

        with self.data_lock:

            return self.latitude

    def get_longitude(
        self
    ) -> Optional[float]:

        with self.data_lock:

            return self.longitude

    def get_altitude(
        self
    ) -> Optional[float]:

        with self.data_lock:

            return self.altitude

    def get_satellite_count(
        self
    ) -> int:

        with self.data_lock:

            return self.satellites

    def is_locked(
        self
    ) -> bool:

        with self.data_lock:

            return (
                self.gps_status
                ==
                GPSStatus.LOCKED
            )

    def lock_age_seconds(
        self
    ) -> Optional[float]:

        with self.data_lock:

            if self.last_fix_time is None:

                return None

            return (
                self._utc_now()
                -
                self.last_fix_time
            ).total_seconds()

    def gps_age_seconds(
        self
    ) -> Optional[float]:

        with self.data_lock:

            if (
                self.last_gps_timestamp
                is None
            ):

                return None

            return (
                self._utc_now()
                -
                self.last_gps_timestamp
            ).total_seconds()

    def is_healthy(
        self
    ) -> bool:

        with self.data_lock:

            status = (
                self.gps_status
            )

            last_fix = (
                self.last_fix_time
            )

            parse_errors = (
                self.parse_errors
            )

        if (
            status
            ==
            GPSStatus.DISCONNECTED
        ):

            return False

        if parse_errors > 100:

            return False

        if last_fix is None:

            return False

        age = (
            self._utc_now()
            -
            last_fix
        ).total_seconds()

        if age > 30:

            return False

        return True

    def statistics(
        self
    ) -> Dict:

        healthy = (
            self.is_healthy()
        )

        gps_age = (
            self.gps_age_seconds()
        )

        with self.data_lock:

            return {

                "gps_status":
                    self.gps_status.value,

                "satellites":
                    self.satellites,

                "latitude":
                    self.latitude,

                "longitude":
                    self.longitude,

                "altitude":
                    self.altitude,

                "messages_received":
                    self.messages_received,

                "parse_errors":
                    self.parse_errors,

                "last_fix_time":
                    self.last_fix_time,

                "last_gps_timestamp":
                    self.last_gps_timestamp,

                "gps_age_seconds":
                    gps_age,

                "reconnect_count":
                    self.reconnect_count,

                "healthy":
                    healthy
            }

    def reconnect(
        self
    ) -> bool:

        try:

            if self.serial_connection:

                try:

                    self.serial_connection.close()

                except Exception:

                    pass

            with self.data_lock:

                self.reconnect_count += 1

            self._connect()

            return True

        except Exception:

            return False

    def run(
        self
    ) -> None:

        while not self.stop_event.is_set():

            try:

                if (
                    self.serial_connection
                    is None
                ):

                    time.sleep(1)

                    continue

                raw_data = (
                    self.serial_connection
                    .readline()
                    .decode(
                        "ascii",
                        errors="ignore"
                    )
                    .strip()
                )

                if not raw_data:

                    continue

                self._handle_message(
                    raw_data
                )

            except Exception:

                with self.data_lock:

                    previous_status = (
                        self.gps_status
                    )

                    self.gps_status = (
                        GPSStatus.DISCONNECTED
                    )

                if (
                    previous_status
                    !=
                    GPSStatus.DISCONNECTED
                ):

                    self.logger.gps_disconnected()

                    self.last_logged_status = (
                        GPSStatus.DISCONNECTED
                    )

                time.sleep(5)

                self.reconnect()

        try:

            if self.serial_connection:

                self.serial_connection.close()

        except Exception:

            pass