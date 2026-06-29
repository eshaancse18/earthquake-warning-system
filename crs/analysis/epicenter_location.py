"""
Epicenter Locator

Estimates the epicenter of a confirmed earthquake
using station observations.

Current implementation:
    Weighted geographic centroid.

Future implementation:
    Arrival-time inversion using P-wave and S-wave data.
"""

from __future__ import annotations

from typing import Tuple

from processing.event_cluster import EventCluster
from logging_system.logger import logger


class EpicenterLocator:
    """
    Estimate earthquake epicenter.
    """

    def estimate(
        self,
        cluster: EventCluster
    ) -> Tuple[float, float, float]:
        """
        Returns

        latitude,
        longitude,
        depth
        """

        events = cluster.get_events()

        if not events:
            raise ValueError(
                "Cluster contains no events."
            )

        total_weight = 0.0

        weighted_lat = 0.0

        weighted_lon = 0.0

        for event in events:

            weight = max(
                event["pga"],
                0.01
            )

            weighted_lat += (
                event["latitude"] * weight
            )

            weighted_lon += (
                event["longitude"] * weight
            )

            total_weight += weight

        latitude = weighted_lat / total_weight

        longitude = weighted_lon / total_weight

        # Placeholder until travel-time inversion
        depth = 10.0

        logger.info(

            "Epicenter estimated "

            f"Lat={latitude:.5f}, "

            f"Lon={longitude:.5f}, "

            f"Depth={depth:.2f} km"

        )

        return (

            latitude,

            longitude,

            depth

        )