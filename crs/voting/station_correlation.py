from datetime import datetime
from datetime import timedelta
from threading import RLock
from typing import Dict
from typing import List
from typing import Optional
from math import radians
from math import sin
from math import cos
from math import sqrt
from math import atan2


class StationCorrelation:
    """
    CRS Station Correlation Engine

    Delhi Metro Configuration
    -------------------------

    Minimum Stations : 3

    Voting Window    : 10 seconds

    Correlation Radius : 5 km

    Purpose
    -------
    Determines whether reports from multiple
    SSN stations represent the same earthquake.
    """

    EARTH_RADIUS_KM = 6371.0

    def __init__(
        self,
        voting_window_seconds: int = 10,
        minimum_stations: int = 3,
        correlation_radius_km: float = 5.0
    ):

        self.voting_window = timedelta(
            seconds=voting_window_seconds
        )

        self.minimum_stations = (
            minimum_stations
        )

        self.correlation_radius_km = (
            correlation_radius_km
        )

        self.lock = RLock()

        self.events: List[Dict] = []

    # ==========================================================
    # DISTANCE
    # ==========================================================

    def _distance_km(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:

        lat1 = radians(lat1)
        lon1 = radians(lon1)

        lat2 = radians(lat2)
        lon2 = radians(lon2)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            sin(dlat / 2) ** 2
            +
            cos(lat1)
            *
            cos(lat2)
            *
            sin(dlon / 2) ** 2
        )

        c = 2 * atan2(
            sqrt(a),
            sqrt(1 - a)
        )

        return (
            self.EARTH_RADIUS_KM * c
        )

    # ==========================================================
    # EVENT MANAGEMENT
    # ==========================================================

    def add_event(
        self,
        report: Dict
    ) -> None:

        with self.lock:

            self.events.append(
                report
            )

            self._cleanup()

    def _cleanup(
        self
    ) -> None:

        cutoff = (
            datetime.utcnow()
            -
            self.voting_window
        )

        self.events = [

            event

            for event in self.events

            if event["received_at"]
            >= cutoff
        ]

    # ==========================================================
    # CORRELATION
    # ==========================================================

    def _correlated(
        self,
        reference: Dict,
        candidate: Dict
    ) -> bool:

        time_delta = abs(
            (
                candidate["received_at"]
                -
                reference["received_at"]
            ).total_seconds()
        )

        if (
            time_delta
            >
            self.voting_window.total_seconds()
        ):
            return False

        lat1 = reference.get(
            "latitude"
        )

        lon1 = reference.get(
            "longitude"
        )

        lat2 = candidate.get(
            "latitude"
        )

        lon2 = candidate.get(
            "longitude"
        )

        if (
            lat1 is None
            or lon1 is None
            or lat2 is None
            or lon2 is None
        ):
            return True

        distance = self._distance_km(
            lat1,
            lon1,
            lat2,
            lon2
        )

        return (
            distance
            <=
            self.correlation_radius_km
        )

    # ==========================================================
    # FIND CANDIDATE
    # ==========================================================

    def candidate_event(
        self
    ) -> Dict:

        with self.lock:

            self._cleanup()

            if not self.events:

                return {
                    "confirmed": False
                }

            reference = self.events[0]

            correlated = []

            unique_stations = set()

            for event in self.events:

                if not self._correlated(
                    reference,
                    event
                ):
                    continue

                station_id = event[
                    "station_id"
                ]

                if (
                    station_id
                    in
                    unique_stations
                ):
                    continue

                unique_stations.add(
                    station_id
                )

                correlated.append(
                    event
                )

            station_count = len(
                unique_stations
            )

            if (
                station_count
                <
                self.minimum_stations
            ):
                return {
                    "confirmed": False
                }

            confidence = min(
                1.0,
                station_count / 5.0
            )

            return {

                "confirmed": True,

                "station_count":
                    station_count,

                "confidence":
                    confidence,

                "events":
                    correlated
            }

    # ==========================================================
    # HELPERS
    # ==========================================================

    def clear(
        self
    ) -> None:

        with self.lock:

            self.events.clear()

    def event_count(
        self
    ) -> int:

        with self.lock:

            return len(
                self.events
            )

    # ==========================================================
    # STATS
    # ==========================================================

    def statistics(
        self
    ) -> Dict:

        with self.lock:

            return {

                "buffered_events":
                    len(self.events),

                "minimum_stations":
                    self.minimum_stations,

                "window_seconds":
                    self.voting_window.total_seconds(),

                "correlation_radius_km":
                    self.correlation_radius_km
            }