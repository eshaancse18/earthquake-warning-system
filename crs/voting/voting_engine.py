import threading
import time

from typing import Dict
from typing import Optional

from voting.station_correlation import (
    StationCorrelation
)

from voting.earthquake_confirmation import (
    EarthquakeConfirmation
)

from alerting.alert_generator import (
    AlertGenerator
)

from database.postgres import (
    PostgresDatabase
)


class VotingEngine(threading.Thread):
    """
    CRS Voting Engine

    Responsibilities
    ----------------

    1. Receive event reports
    2. Correlate stations
    3. Confirm earthquakes
    4. Store earthquakes
    5. Generate alerts

    Configuration
    -------------

    Minimum Stations = 3

    Voting Window = 10 sec
    """

    def __init__(
        self,
        database: PostgresDatabase,
        alert_generator: AlertGenerator
    ):

        super().__init__(
            name="VOTING_ENGINE",
            daemon=True
        )

        self.database = database

        self.alert_generator = (
            alert_generator
        )

        self.correlation = (
            StationCorrelation(
                voting_window_seconds=10,
                minimum_stations=3
            )
        )

        self.confirmation = (
            EarthquakeConfirmation()
        )

        self.stop_event = (
            threading.Event()
        )

        self.last_processed_report = None

        self.confirmed_earthquakes = 0

        self.rejected_candidates = 0

        self.last_earthquake = None

    # ==========================================================
    # INPUT
    # ==========================================================

    def add_event_report(
        self,
        report: Dict
    ) -> None:

        self.correlation.add_event(
            report
        )

    # ==========================================================
    # PROCESS
    # ==========================================================

    def _process_candidate(
        self
    ) -> Optional[Dict]:

        candidate = (
            self.correlation
            .candidate_event()
        )

        if not candidate.get(
            "confirmed",
            False
        ):

            return None

        earthquake = (
            self.confirmation
            .confirm(
                candidate
            )
        )

        if not earthquake.get(
            "confirmed",
            False
        ):

            self.rejected_candidates += 1

            return None

        self.database.save_earthquake(

            earthquake_id=
            earthquake[
                "earthquake_id"
            ],

            confidence=
            earthquake[
                "confidence"
            ],

            station_count=
            earthquake[
                "station_count"
            ],

            magnitude=
            earthquake[
                "magnitude"
            ],

            latitude=
            earthquake[
                "epicenter_latitude"
            ],

            longitude=
            earthquake[
                "epicenter_longitude"
            ],

            metadata=
            earthquake
        )

        self.alert_generator.generate(
            earthquake
        )

        self.confirmed_earthquakes += 1

        self.last_earthquake = (
            earthquake
        )

        return earthquake

    # ==========================================================
    # THREAD
    # ==========================================================

    def run(
        self
    ) -> None:

        while not self.stop_event.is_set():

            try:

                self._process_candidate()

            except Exception:

                pass

            time.sleep(
                1
            )

    def stop(
        self
    ) -> None:

        self.stop_event.set()

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

        return {

            "confirmed_earthquakes":
                self.confirmed_earthquakes,

            "rejected_candidates":
                self.rejected_candidates,

            "last_earthquake":
                self.last_earthquake,

            "correlation":
                self.correlation
                .statistics(),

            "confirmation":
                self.confirmation
                .statistics()
        }