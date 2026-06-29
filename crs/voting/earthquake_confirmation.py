import uuid

from datetime import datetime
from threading import RLock
from typing import Dict
from typing import List


class EarthquakeConfirmation:
    """
    CRS Earthquake Confirmation Engine

    Responsibilities
    ----------------

    1. Confirm candidate earthquakes
    2. Estimate magnitude
    3. Estimate epicenter
    4. Calculate confidence
    5. Build CRS earthquake record
    """

    def __init__(self):

        self.lock = RLock()

        self.confirmed_count = 0

        self.rejected_count = 0

    # ==========================================================
    # MAGNITUDE
    # ==========================================================

    def _estimate_magnitude(
        self,
        events: List[Dict]
    ) -> float:

        if not events:

            return 0.0

        pga_values = []

        for event in events:

            pga = event.get(
                "pga",
                0.0
            )

            try:

                pga_values.append(
                    float(pga)
                )

            except Exception:

                pass

        if not pga_values:

            return 0.0

        average_pga = (
            sum(pga_values)
            /
            len(pga_values)
        )

        # Initial lab approximation

        magnitude = (
            2.0
            +
            (
                average_pga * 20.0
            )
        )

        return round(
            magnitude,
            2
        )

    # ==========================================================
    # EPICENTER
    # ==========================================================

    def _estimate_epicenter(
        self,
        events: List[Dict]
    ) -> Dict:

        latitudes = []

        longitudes = []

        for event in events:

            latitude = event.get(
                "latitude"
            )

            longitude = event.get(
                "longitude"
            )

            if (
                latitude is not None
                and
                longitude is not None
            ):

                latitudes.append(
                    latitude
                )

                longitudes.append(
                    longitude
                )

        if not latitudes:

            return {

                "latitude": None,

                "longitude": None
            }

        return {

            "latitude":
                round(
                    sum(latitudes)
                    /
                    len(latitudes),
                    6
                ),

            "longitude":
                round(
                    sum(longitudes)
                    /
                    len(longitudes),
                    6
                )
        }

    # ==========================================================
    # CONFIDENCE
    # ==========================================================

    def _confidence(
        self,
        station_count: int
    ) -> float:

        confidence = min(
            1.0,
            station_count / 5.0
        )

        return round(
            confidence,
            2
        )

    # ==========================================================
    # CONFIRM
    # ==========================================================

    def confirm(
        self,
        candidate: Dict
    ) -> Dict:

        with self.lock:

            if not candidate.get(
                "confirmed",
                False
            ):

                self.rejected_count += 1

                return {

                    "confirmed":
                        False
                }

            events = candidate[
                "events"
            ]

            station_count = candidate[
                "station_count"
            ]

            magnitude = (
                self._estimate_magnitude(
                    events
                )
            )

            epicenter = (
                self._estimate_epicenter(
                    events
                )
            )

            confidence = (
                self._confidence(
                    station_count
                )
            )

            earthquake = {

                "earthquake_id":
                    str(
                        uuid.uuid4()
                    ),

                "confirmed":
                    True,

                "confirmed_at":
                    datetime.utcnow()
                    .isoformat(),

                "station_count":
                    station_count,

                "confidence":
                    confidence,

                "magnitude":
                    magnitude,

                "epicenter_latitude":
                    epicenter[
                        "latitude"
                    ],

                "epicenter_longitude":
                    epicenter[
                        "longitude"
                    ],

                "events":
                    events
            }

            self.confirmed_count += 1

            return earthquake

    # ==========================================================
    # HEALTH
    # ==========================================================

    def is_healthy(
        self
    ) -> bool:

        return True

    # ==========================================================
    # STATS
    # ==========================================================

    def statistics(
        self
    ) -> Dict:

        with self.lock:

            return {

                "confirmed_count":
                    self.confirmed_count,

                "rejected_count":
                    self.rejected_count
            }