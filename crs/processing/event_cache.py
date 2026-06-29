"""
Event Cache

Maintains active earthquake event clusters.

Responsibilities:
- Store active event clusters
- Match incoming events to existing clusters
- Create new clusters when needed
- Remove expired clusters
"""

from __future__ import annotations

from datetime import timedelta
from typing import Dict, List

from config.config import config
from logging_system.logger import logger
from processing.event_cluster import EventCluster


class EventCache:
    """
    Stores active earthquake event clusters.
    """

    def __init__(self) -> None:

        self.clusters: List[EventCluster] = []

        self.time_window = timedelta(
            seconds=config.get(
                "voting",
                "maximum_time_difference_seconds"
            )
        )

    # --------------------------------------------------

    def add_event(
        self,
        event: Dict
    ) -> None:
        """
        Add an event to an existing cluster or
        create a new cluster.
        """

        self.remove_expired_clusters()

        cluster = self.find_matching_cluster(event)

        if cluster is not None:

            cluster.add_event(event)

            logger.info(
                f"Added {event['station_id']} "
                f"to existing cluster."
            )

        else:

            new_cluster = EventCluster(event)

            self.clusters.append(new_cluster)

            logger.info(
                f"Created new cluster "
                f"for {event['station_id']}."
            )

    # --------------------------------------------------

    def find_matching_cluster(
        self,
        event: Dict
    ) -> EventCluster | None:
        """
        Find a cluster whose latest event
        is within the configured time window.

        Future versions can also compare
        geographical distance.
        """

        for cluster in self.clusters:

            delta = abs(

                event["timestamp"]

                - cluster.latest_timestamp()

            )

            if delta <= self.time_window:

                return cluster

        return None

    # --------------------------------------------------

    def remove_expired_clusters(
        self
    ) -> None:
        """
        Remove clusters that have not received
        updates within the configured time window.
        """

        active_clusters = []

        for cluster in self.clusters:

            latest = cluster.latest_timestamp()

            newest_allowed = latest + self.time_window

            if event_time := self._current_reference_time():

                if newest_allowed >= event_time:

                    active_clusters.append(cluster)

                else:

                    logger.info(
                        "Expired cluster removed."
                    )

        self.clusters = active_clusters

    # --------------------------------------------------

    def _current_reference_time(self):
        """
        Returns the newest timestamp among
        all active clusters.

        This avoids relying on local system
        time and instead follows incoming
        seismic event timestamps.
        """

        if not self.clusters:

            return None

        return max(

            cluster.latest_timestamp()

            for cluster in self.clusters

        )

    # --------------------------------------------------

    def get_clusters(
        self
    ) -> List[EventCluster]:

        return self.clusters

    # --------------------------------------------------

    def cluster_count(
        self
    ) -> int:

        return len(self.clusters)

    # --------------------------------------------------

    def clear(self) -> None:

        self.clusters.clear()

        logger.info(
            "Event cache cleared."
        )