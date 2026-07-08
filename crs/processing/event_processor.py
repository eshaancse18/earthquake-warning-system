# """
# Event Processor

# Coordinates processing of a confirmed earthquake.

# Pipeline:

# VotingResult
#       │
#       ▼
# Epicenter Locator
#       │
#       ▼
# Magnitude Estimator
#       │
#       ▼
# Database Repository
#       │
#       ▼
# Alert Manager
# """

# from __future__ import annotations

# from analysis.epicenter_locator import EpicenterLocator
# from analysis.magnitude_estimator import MagnitudeEstimator
# from alerting.alert_manager import alert_manager
# from logging_system.logger import logger
# from processing.voting_engine import VotingResult
# from storage.event_repository import repository


# class EventProcessor:
#     """
#     Processes confirmed earthquake events.
#     """

#     def __init__(self) -> None:

#         self.epicenter_locator = EpicenterLocator()

#         self.magnitude_estimator = MagnitudeEstimator()

#     # --------------------------------------------------

#     def process(
#         self,
#         result: VotingResult
#     ) -> int:
#         """
#         Process a confirmed earthquake.

#         Parameters
#         ----------
#         result
#             Confirmed voting result.

#         Returns
#         -------
#         int
#             Database event ID.
#         """

#         if not result.confirmed:

#             logger.info(
#                 "Cluster not confirmed. "
#                 "Skipping processing."
#             )

#             return -1

#         logger.info(
#             "Starting earthquake processing."
#         )

#         # ------------------------------------------
#         # Estimate Epicenter
#         # ------------------------------------------

#         latitude, longitude, depth = (
#             self.epicenter_locator.estimate(
#                 result.cluster
#             )
#         )

#         # ------------------------------------------
#         # Estimate Distance
#         #
#         # Placeholder:
#         # In the current prototype we assume the
#         # epicentral distance is approximately 20 km.
#         # Future versions will compute this from
#         # station geometry.
#         # ------------------------------------------

#         epicentral_distance = 20.0

#         # ------------------------------------------
#         # Estimate Magnitude
#         # ------------------------------------------

#         magnitude = (
#             self.magnitude_estimator.estimate(
#                 result.cluster,
#                 epicentral_distance
#             )
#         )

#         # ------------------------------------------
#         # Save Event
#         # ------------------------------------------

#         event_id = repository.save_confirmed_event(

#             result,

#             latitude,

#             longitude,

#             depth,

#             magnitude

#         )

#         repository.save_station_reports(

#             event_id,

#             result

#         )

#         # ------------------------------------------
#         # Alerts
#         # ------------------------------------------

#         alert_manager.publish_alert(

#             event_id,

#             magnitude,

#             latitude,

#             longitude,

#             result.confidence

#         )

#         if alert_manager.metro_warning(
#             magnitude
#         ):

#             logger.warning(

#                 "METRO WARNING TRIGGERED"

#             )

#         alert_manager.notify_console(

#             event_id,

#             magnitude

#         )

#         logger.info(

#             "Earthquake processing complete."

#         )

#         return event_id


# event_processor = EventProcessor()



from threading import Lock
from datetime import datetime


class EventProcessor:
    """
    Processes confirmed earthquake events and
    stores the latest event for dashboard access.
    """

    def __init__(self):

        self.lock = Lock()

        self.latest_event = None

        self.event_history = []

    # --------------------------------------------------
    # Process Event
    # --------------------------------------------------

    def process_event(self, event):

        """
        Called by the voting engine after an
        earthquake has been confirmed.
        """

        with self.lock:

            event_record = {

                "event_id": event.get(
                    "event_id",
                    ""
                ),

                "station_id": event.get(
                    "station_id",
                    ""
                ),

                "latitude": event.get(
                    "latitude",
                    0.0
                ),

                "longitude": event.get(
                    "longitude",
                    0.0
                ),

                "magnitude": event.get(
                    "magnitude",
                    0.0
                ),

                "confidence": event.get(
                    "confidence",
                    0
                ),

                "timestamp": event.get(
                    "timestamp",
                    datetime.utcnow().isoformat()
                ),

                "status": "Confirmed"
            }

            self.latest_event = event_record

            self.event_history.append(
                event_record
            )

            print(
                f"[EVENT] "
                f"M {event_record['magnitude']} "
                f"confirmed."
            )

    # --------------------------------------------------
    # Latest Event
    # --------------------------------------------------

    def get_latest_event(self):

        with self.lock:

            return self.latest_event

    # --------------------------------------------------
    # Event History
    # --------------------------------------------------

    def get_event_history(self):

        with self.lock:

            return list(self.event_history)

    # --------------------------------------------------
    # Total Events
    # --------------------------------------------------

    def total_events(self):

        with self.lock:

            return len(
                self.event_history
            )

    # --------------------------------------------------
    # Clear Events
    # --------------------------------------------------

    def clear(self):

        with self.lock:

            self.latest_event = None

            self.event_history.clear()


event_processor = EventProcessor()