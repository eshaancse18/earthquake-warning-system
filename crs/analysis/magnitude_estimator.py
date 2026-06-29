"""
Magnitude Estimator

Estimates earthquake magnitude using the
measured Peak Ground Acceleration (PGA).

NOTE:
This implementation is intended for a prototype.
It can later be replaced by a proper
Ground Motion Prediction Equation (GMPE).
"""

from __future__ import annotations

import math

from config.config import config
from logging_system.logger import logger
from processing.event_cluster import EventCluster


class MagnitudeEstimator:
    """
    Estimates earthquake magnitude.
    """

    def estimate(
        self,
        cluster: EventCluster,
        epicentral_distance_km: float
    ) -> float:
        """
        Estimate magnitude.

        Parameters
        ----------
        cluster
            Confirmed event cluster.

        epicentral_distance_km
            Estimated distance from epicenter.
        """

        avg_pga = cluster.average_pga()

        avg_pga = max(avg_pga, 0.001)

        attenuation = config.get(
            "magnitude",
            "attenuation_factor"
        )

        magnitude = (

            math.log10(avg_pga * 100)

            +

            attenuation *

            math.log10(
                max(
                    epicentral_distance_km,
                    1.0
                )
            )

            +

            1.5

        )

        magnitude = round(magnitude, 2)

        logger.info(

            "Estimated Magnitude "

            f"M={magnitude}"

        )

        return magnitude