"""
Event Manager

Coordinates earthquake event processing.

Pipeline:

Validated Event
        │
        ▼
    Event Cache
        │
        ▼
   Voting Engine
        │
        ▼
Confirmed Event ?
        │
   Yes / No
        │
        ▼
Return VotingResult
"""

from __future__ import annotations

from typing import Optional

from logging_system.logger import logger
from processing.event_cache import EventCache
from processing.event_cluster import EventCluster
from processing.voting_engine import (
    VotingEngine,
    VotingResult,
)


class EventManager:
    """
    Central coordinator for earthquake event processing.
    """

    def __init__(self) -> None:

        self.cache = EventCache()

        self.voting_engine = VotingEngine()

    # --------------------------------------------------

    def process_event(
        self,
        event: dict
    ) -> Optional[VotingResult]:
        """
        Process one validated station event.

        Parameters
        ----------
        event : dict
            Validated event received from EventReceiver.

        Returns
        -------
        VotingResult | None
            Voting result if a cluster was evaluated.
        """

        logger.info(
            f"Processing event from "
            f"{event['station_id']}"
        )

        # ------------------------------------------

        self.cache.add_event(event)

        # ------------------------------------------

        for cluster in self.cache.get_clusters():

            result = self.voting_engine.evaluate(
                cluster
            )

            if result.confirmed:

                logger.info(
                    "Earthquake confirmed."
                )

                return result

        return None

    # --------------------------------------------------

    def get_active_clusters(
        self
    ) -> list[EventCluster]:

        return self.cache.get_clusters()

    # --------------------------------------------------

    def cluster_count(
        self
    ) -> int:

        return self.cache.cluster_count()

    # --------------------------------------------------

    def clear_cache(
        self
    ) -> None:

        self.cache.clear()

        logger.info(
            "Event cache cleared."
        )