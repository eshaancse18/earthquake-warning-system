import threading
from collections import deque

from services.mqtt_service import mqtt_service


class LiveData:

    def __init__(self):

        self.lock = threading.Lock()

        self.station_health = {}

        self.latest_event = None

        self.mqtt_logs = deque(maxlen=500)

    # -------------------------------------------------
    # Start MQTT
    # -------------------------------------------------

    def start(self):

        mqtt_service.register_health_callback(
            self._health_callback
        )

        mqtt_service.register_event_callback(
            self._event_callback
        )

        mqtt_service.connect()

        thread = threading.Thread(
            target=mqtt_service.start,
            daemon=True
        )

        thread.start()

    # -------------------------------------------------
    # Health Callback
    # -------------------------------------------------

    def _health_callback(self, packet):

        with self.lock:

            station_id = packet.get(
                "station_id",
                "UNKNOWN"
            )

            self.station_health[station_id] = packet

            self.mqtt_logs.appendleft({

                "topic": "health",

                "station": station_id,

                "packet": packet

            })

    # -------------------------------------------------
    # Event Callback
    # -------------------------------------------------

    def _event_callback(self, packet):

        with self.lock:

            self.latest_event = packet

            self.mqtt_logs.appendleft({

                "topic": "event",

                "station": packet.get(
                    "station_id",
                    "UNKNOWN"
                ),

                "packet": packet

            })

    # -------------------------------------------------
    # Public APIs
    # -------------------------------------------------

    def get_station_health(self):

        with self.lock:

            return dict(self.station_health)

    def get_latest_event(self):

        with self.lock:

            return self.latest_event

    def get_mqtt_logs(self):

        with self.lock:

            return list(self.mqtt_logs)

    def station_count(self):

        with self.lock:

            return len(self.station_health)

    def connected_station_ids(self):

        with self.lock:

            return list(
                self.station_health.keys()
            )


live_data = LiveData()