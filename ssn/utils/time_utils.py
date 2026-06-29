from datetime import datetime
from datetime import timezone
from datetime import timedelta

from typing import Optional
from typing import Dict

import time


class TimeUtils:

    """
    Production Time Utility Module

    Responsibilities
    ----------------
    1. UTC Time Management
    2. GPS Time Validation
    3. Event Correlation Timing
    4. Latency Measurement
    5. Timestamp Conversion
    6. Station Synchronization
    7. Watchdog Timing
    8. Monotonic Timing
    """

    @staticmethod
    def utc_now() -> datetime:

        return datetime.now(
            timezone.utc
        )

    @staticmethod
    def utc_iso() -> str:

        return (
            TimeUtils.utc_now()
            .isoformat()
        )

    @staticmethod
    def ensure_utc(
        dt: datetime
    ) -> datetime:

        if dt.tzinfo is None:

            return dt.replace(
                tzinfo=timezone.utc
            )

        return dt.astimezone(
            timezone.utc
        )

    @staticmethod
    def datetime_to_epoch_ms(
        dt: datetime
    ) -> int:

        dt = TimeUtils.ensure_utc(
            dt
        )

        return int(
            dt.timestamp() * 1000
        )

    @staticmethod
    def datetime_to_epoch_us(
        dt: datetime
    ) -> int:

        dt = TimeUtils.ensure_utc(
            dt
        )

        return int(
            dt.timestamp() * 1000000
        )

    @staticmethod
    def epoch_ms_to_datetime(
        epoch_ms: int
    ) -> datetime:

        return datetime.fromtimestamp(
            epoch_ms / 1000.0,
            timezone.utc
        )

    @staticmethod
    def epoch_us_to_datetime(
        epoch_us: int
    ) -> datetime:

        return datetime.fromtimestamp(
            epoch_us / 1000000.0,
            timezone.utc
        )

    @staticmethod
    def parse_iso_timestamp(
        timestamp: str
    ) -> datetime:

        parsed = (
            datetime.fromisoformat(
                timestamp
            )
        )

        return (
            TimeUtils.ensure_utc(
                parsed
            )
        )

    @staticmethod
    def time_difference_ms(
        t1: datetime,
        t2: datetime
    ) -> float:

        t1 = TimeUtils.ensure_utc(
            t1
        )

        t2 = TimeUtils.ensure_utc(
            t2
        )

        difference = (
            t2 - t1
        )

        return (
            difference.total_seconds()
            * 1000.0
        )

    @staticmethod
    def time_difference_us(
        t1: datetime,
        t2: datetime
    ) -> float:

        t1 = TimeUtils.ensure_utc(
            t1
        )

        t2 = TimeUtils.ensure_utc(
            t2
        )

        difference = (
            t2 - t1
        )

        return (
            difference.total_seconds()
            * 1000000.0
        )

    @staticmethod
    def station_arrival_delay_ms(
        first_station_time: datetime,
        second_station_time: datetime
    ) -> float:

        return abs(
            TimeUtils.time_difference_ms(
                first_station_time,
                second_station_time
            )
        )

    @staticmethod
    def calculate_event_latency_ms(
        event_time: datetime,
        processing_time: datetime
    ) -> float:

        event_time = (
            TimeUtils.ensure_utc(
                event_time
            )
        )

        processing_time = (
            TimeUtils.ensure_utc(
                processing_time
            )
        )

        latency = (

            processing_time
            -
            event_time

        ).total_seconds() * 1000.0

        return max(
            0.0,
            latency
        )

    @staticmethod
    def calculate_transmission_latency_ms(
        sent_time: datetime,
        received_time: datetime
    ) -> float:

        sent_time = (
            TimeUtils.ensure_utc(
                sent_time
            )
        )

        received_time = (
            TimeUtils.ensure_utc(
                received_time
            )
        )

        latency = (

            received_time
            -
            sent_time

        ).total_seconds() * 1000.0

        return max(
            0.0,
            latency
        )

    @staticmethod
    def gps_time_valid(
        gps_time: Optional[datetime],
        max_age_seconds: int = 5
    ) -> bool:

        if gps_time is None:

            return False

        gps_time = (
            TimeUtils.ensure_utc(
                gps_time
            )
        )

        now = (
            TimeUtils.utc_now()
        )

        age = abs(
            (
                now - gps_time
            ).total_seconds()
        )

        return (
            age <= max_age_seconds
        )

    @staticmethod
    def correlation_window_match(
        event_time_1: datetime,
        event_time_2: datetime,
        window_ms: int
    ) -> bool:

        delta = abs(
            TimeUtils.time_difference_ms(
                event_time_1,
                event_time_2
            )
        )

        return (
            delta <= window_ms
        )

    @staticmethod
    def build_timing_metadata(
        event_time: datetime,
        processing_time: datetime,
        station_id: str
    ) -> Dict:

        event_time = (
            TimeUtils.ensure_utc(
                event_time
            )
        )

        processing_time = (
            TimeUtils.ensure_utc(
                processing_time
            )
        )

        return {

            "station_id":
                station_id,

            "event_time":
                event_time.isoformat(),

            "processing_time":
                processing_time.isoformat(),

            "event_epoch_ms":
                TimeUtils.datetime_to_epoch_ms(
                    event_time
                ),

            "processing_epoch_ms":
                TimeUtils.datetime_to_epoch_ms(
                    processing_time
                ),

            "latency_ms":
                TimeUtils.calculate_event_latency_ms(
                    event_time,
                    processing_time
                )
        }

    @staticmethod
    def add_milliseconds(
        timestamp: datetime,
        milliseconds: int
    ) -> datetime:

        return timestamp + timedelta(
            milliseconds=milliseconds
        )

    @staticmethod
    def add_microseconds(
        timestamp: datetime,
        microseconds: int
    ) -> datetime:

        return timestamp + timedelta(
            microseconds=microseconds
        )

    @staticmethod
    def floor_to_second(
        timestamp: datetime
    ) -> datetime:

        return timestamp.replace(
            microsecond=0
        )

    @staticmethod
    def floor_to_minute(
        timestamp: datetime
    ) -> datetime:

        return timestamp.replace(
            second=0,
            microsecond=0
        )

    @staticmethod
    def timestamp_for_filename(
        timestamp: datetime
    ) -> str:

        timestamp = (
            TimeUtils.ensure_utc(
                timestamp
            )
        )

        return timestamp.strftime(
            "%Y%m%d_%H%M%S_%f"
        )

    @staticmethod
    def current_uptime_seconds(
        start_time: datetime
    ) -> float:

        start_time = (
            TimeUtils.ensure_utc(
                start_time
            )
        )

        return (

            TimeUtils.utc_now()

            -

            start_time

        ).total_seconds()

    @staticmethod
    def monotonic_seconds() -> float:

        return time.monotonic()

    @staticmethod
    def monotonic_milliseconds() -> int:

        return int(
            time.monotonic()
            * 1000
        )

    @staticmethod
    def monotonic_microseconds() -> int:

        return int(
            time.monotonic()
            * 1000000
        )