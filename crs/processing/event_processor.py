"""
Event Processor

Coordinates processing of a confirmed earthquake.

Pipeline:

VotingResult
      │
      ▼
Epicenter Locator
      │
      ▼
Magnitude Estimator
      │
      ▼
Database Repository
      │
      ▼
Alert Manager
"""

from __future__ import annotations

from analysis.epicenter_locator import EpicenterLocator
from analysis.magnitude_estimator import MagnitudeEstimator
from alerting.alert_manager import alert_manager
from logging_system.logger import logger
from processing.voting_engine import VotingResult
from storage.event_repository import repository


class EventProcessor:
    """
    Processes confirmed earthquake events.
    """

    def __init__(self) -> None:

        self.epicenter_locator = EpicenterLocator()

        self.magnitude_estimator = MagnitudeEstimator()

    # --------------------------------------------------

    def process(
        self,
        result: VotingResult
    ) -> int:
        """
        Process a confirmed earthquake.

        Parameters
        ----------
        result
            Confirmed voting result.

        Returns
        -------
        int
            Database event ID.
        """

        if not result.confirmed:

            logger.info(
                "Cluster not confirmed. "
                "Skipping processing."
            )

            return -1

        logger.info(
            "Starting earthquake processing."
        )

        # ------------------------------------------
        # Estimate Epicenter
        # ------------------------------------------

        latitude, longitude, depth = (
            self.epicenter_locator.estimate(
                result.cluster
            )
        )

        # ------------------------------------------
        # Estimate Distance
        #
        # Placeholder:
        # In the current prototype we assume the
        # epicentral distance is approximately 20 km.
        # Future versions will compute this from
        # station geometry.
        # ------------------------------------------

        epicentral_distance = 20.0

        # ------------------------------------------
        # Estimate Magnitude
        # ------------------------------------------

        magnitude = (
            self.magnitude_estimator.estimate(
                result.cluster,
                epicentral_distance
            )
        )

        # ------------------------------------------
        # Save Event
        # ------------------------------------------

        event_id = repository.save_confirmed_event(

            result,

            latitude,

            longitude,

            depth,

            magnitude

        )

        repository.save_station_reports(

            event_id,

            result

        )

        # ------------------------------------------
        # Alerts
        # ------------------------------------------

        alert_manager.publish_alert(

            event_id,

            magnitude,

            latitude,

            longitude,

            result.confidence

        )

        if alert_manager.metro_warning(
            magnitude
        ):

            logger.warning(

                "METRO WARNING TRIGGERED"

            )

        alert_manager.notify_console(

            event_id,

            magnitude

        )

        logger.info(

            "Earthquake processing complete."

        )

        return event_id


event_processor = EventProcessor()