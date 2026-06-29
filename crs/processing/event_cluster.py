"""
Event Cluster

Represents one potential earthquake event.

A cluster contains all station detections that are
believed to correspond to the same seismic event.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List


class EventCluster:
    """
    Candidate earthquake event.
    """

    def __init__(
        self,
        first_event: Dict
    ) -> None:

        self.events: List[Dict] = [first_event]

        self.created_at: datetime = first_event["timestamp"]

        self.last_updated: datetime = first_event["timestamp"]

    # --------------------------------------------------

    def add_event(
        self,
        event: Dict
    ) -> None:
        """
        Add a station event to this cluster.
        """

        self.events.append(event)

        self.last_updated = event["timestamp"]

    # --------------------------------------------------

    def station_count(
        self
    ) -> int:
        """
        Number of unique stations contributing
        to this cluster.
        """

        stations = {

            event["station_id"]

            for event in self.events

        }

        return len(stations)

    # --------------------------------------------------

    def average_pga(
        self
    ) -> float:

        if not self.events:
            return 0.0

        return sum(

            event["pga"]

            for event in self.events

        ) / len(self.events)

    # --------------------------------------------------

    def average_sta_lta(
        self
    ) -> float:

        if not self.events:
            return 0.0

        return sum(

            event["sta_lta"]

            for event in self.events

        ) / len(self.events)

    # --------------------------------------------------

    def average_p_wave_confidence(
        self
    ) -> float:

        if not self.events:
            return 0.0

        return sum(

            event["p_wave_confidence"]

            for event in self.events

        ) / len(self.events)

    # --------------------------------------------------

    def latest_timestamp(
        self
    ) -> datetime:

        return max(

            event["timestamp"]

            for event in self.events

        )

    # --------------------------------------------------

    def earliest_timestamp(
        self
    ) -> datetime:

        return min(

            event["timestamp"]

            for event in self.events

        )

    # --------------------------------------------------

    def get_events(
        self
    ) -> List[Dict]:

        return self.events

    # --------------------------------------------------

    def __len__(
        self
    ) -> int:

        return len(self.events)

    # --------------------------------------------------

    def __repr__(
        self
    ) -> str:

        return (

            f"EventCluster("

            f"stations={self.station_count()}, "

            f"events={len(self.events)})"

        )