from __future__ import annotations

import queue
import threading
import uuid
from datetime import datetime
from typing import Dict


class SimulationTrigger(threading.Thread):
    """
    Manual earthquake simulator.

    Whenever the user presses ENTER,
    a simulated earthquake event is placed
    into the SensorManager event_queue.

    The EventForwarder will automatically
    publish it through MQTT.
    """

    def __init__(
        self,
        station_id: str,
        event_queue: queue.Queue
    ):

        super().__init__(
            name="SIMULATION_THREAD",
            daemon=True
        )

        self.station_id = station_id
        self.event_queue = event_queue
        self.stop_event = threading.Event()

    def stop(self):

        self.stop_event.set()

    def build_event(self) -> Dict:

        return {

            "event_id": str(uuid.uuid4()),

            "station_id": self.station_id,

            "timestamp": datetime.utcnow().isoformat(),

            "latitude": 28.6139,

            "longitude": 77.2090,

            "elevation": 216,

            "pga": 0.32,

            "sta_lta": 6.8,

            "p_wave_confidence": 0.96,

            "waveform_path": "simulation",

            "metadata": {

                "source": "SIMULATOR",

                "magnitude": 5.7

            }

        }

    def run(self):

        print()
        print("=" * 60)
        print("SIMULATION MODE ENABLED")
        print("Press ENTER to simulate an earthquake.")
        print("=" * 60)

        while not self.stop_event.is_set():

            input()

            event = self.build_event()

            self.event_queue.put(event)

            print()
            print("Earthquake simulated.")
            print(event["event_id"])
            print()