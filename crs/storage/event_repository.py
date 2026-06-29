"""
Event Repository

Provides database operations for earthquake
events and station reports.
"""

from __future__ import annotations

from typing import Optional

from database.database import database
from logging_system.logger import logger
from processing.voting_engine import VotingResult


class EventRepository:
    """
    Repository responsible for persisting
    earthquake events and related station data.
    """

    # --------------------------------------------------

    def save_confirmed_event(
        self,
        result: VotingResult,
        latitude: float,
        longitude: float,
        depth: float,
        magnitude: float
    ) -> int:
        """
        Save a confirmed earthquake event.

        Returns
        -------
        int
            Database event_id.
        """

        query = """
        INSERT INTO events
        (
            origin_time,
            estimated_latitude,
            estimated_longitude,
            estimated_depth,
            estimated_magnitude,
            confidence,
            confirmed
        )
        VALUES
        (
            NOW(),
            %s,
            %s,
            %s,
            %s,
            %s,
            TRUE
        )
        RETURNING event_id;
        """

        row = database.fetch_one(
            query,
            (
                latitude,
                longitude,
                depth,
                magnitude,
                result.confidence,
            )
        )

        event_id = row["event_id"]

        logger.info(
            f"Saved earthquake event #{event_id}"
        )

        return event_id

    # --------------------------------------------------

    def save_station_reports(
        self,
        event_id: int,
        result: VotingResult
    ) -> None:
        """
        Save all station observations that
        contributed to the earthquake.
        """

        query = """
        INSERT INTO station_events
        (
            event_id,
            station_id,
            detection_time,
            pga,
            sta_lta,
            p_wave_confidence,
            local_confidence,
            waveform_path
        )
        VALUES
        (
            %s,%s,%s,%s,%s,%s,%s,%s
        );
        """

        for event in result.cluster.get_events():

            database.execute(

                query,

                (

                    event_id,

                    event["station_id"],

                    event["timestamp"],

                    event["pga"],

                    event["sta_lta"],

                    event["p_wave_confidence"],

                    result.confidence,

                    event.get("waveform_path")

                )

            )

        logger.info(
            f"Stored {len(result.cluster)} "
            f"station reports."
        )

    # --------------------------------------------------

    def get_event(
        self,
        event_id: int
    ) -> Optional[dict]:

        return database.fetch_one(

            """
            SELECT *
            FROM events
            WHERE event_id=%s
            """,

            (event_id,)

        )

    # --------------------------------------------------

    def list_events(self) -> list[dict]:

        return database.fetch_all(

            """
            SELECT *
            FROM events
            ORDER BY origin_time DESC
            """

        )


repository = EventRepository()