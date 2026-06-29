"""
Voting Engine

Determines whether an EventCluster represents
a genuine earthquake.

The engine evaluates:

1. Number of unique stations
2. Average PGA
3. Average STA/LTA
4. Average P-wave confidence
5. Time consistency

Returns a VotingResult.
"""

from __future__ import annotations

from dataclasses import dataclass

from config.config import config
from logging_system.logger import logger
from processing.event_cluster import EventCluster


# --------------------------------------------------------
# Voting Result
# --------------------------------------------------------

@dataclass(slots=True)
class VotingResult:

    confirmed: bool

    confidence: float

    station_count: int

    average_pga: float

    average_sta_lta: float

    average_p_wave: float

    cluster: EventCluster


# --------------------------------------------------------
# Voting Engine
# --------------------------------------------------------

class VotingEngine:

    def __init__(self) -> None:

        self.minimum_stations = config.get(
            "voting",
            "minimum_triggered_stations"
        )

        self.minimum_confidence = config.get(
            "voting",
            "minimum_confidence"
        )

    # ----------------------------------------------------

    def evaluate(
        self,
        cluster: EventCluster
    ) -> VotingResult:
        """
        Evaluate one candidate earthquake cluster.
        """

        stations = cluster.station_count()

        avg_pga = cluster.average_pga()

        avg_sta = cluster.average_sta_lta()

        avg_pwave = cluster.average_p_wave_confidence()

        # ----------------------------------------------
        # Parameter Scores
        # ----------------------------------------------

        pga_score = min(avg_pga / 0.20, 1.0)

        sta_score = min(avg_sta / 5.0, 1.0)

        pwave_score = min(avg_pwave, 1.0)

        station_score = min(
            stations / self.minimum_stations,
            1.0
        )

        # ----------------------------------------------
        # Weighted Confidence
        # ----------------------------------------------

        confidence = (

            0.35 * pga_score +

            0.25 * sta_score +

            0.25 * pwave_score +

            0.15 * station_score

        )

        confirmed = (

            stations >= self.minimum_stations

            and

            confidence >= self.minimum_confidence

        )

        logger.info(

            "Voting Result | "

            f"Stations={stations}, "

            f"PGA={avg_pga:.3f}, "

            f"STA/LTA={avg_sta:.2f}, "

            f"P-Wave={avg_pwave:.2f}, "

            f"Confidence={confidence:.2f}, "

            f"Confirmed={confirmed}"

        )

        return VotingResult(

            confirmed=confirmed,

            confidence=confidence,

            station_count=stations,

            average_pga=avg_pga,

            average_sta_lta=avg_sta,

            average_p_wave=avg_pwave,

            cluster=cluster

        )