from collections import deque
from datetime import datetime
from threading import Lock
from typing import Dict
import numpy as np
STANDARD_GRAVITY = 9.80665

class PGADetector:
    """
    Peak Ground Acceleration Detector.

    PGA = maximum absolute acceleration
    observed during a time window.

    This detector maintains a rolling
    acceleration window and continuously
    computes:

    - Instantaneous PGA
    - Rolling PGA
    - Event Trigger
    - Severity Level

    Used together with:
    - STA/LTA
    - Frequency Validation
    - CRS Voting
    """

    def __init__(
        self,
        sampling_rate: int,
        pga_threshold: float,
        rolling_window_seconds: float = 1.0
    ):

        if sampling_rate <= 0:
            raise ValueError(
                "sampling_rate must be > 0"
            )

        if pga_threshold <= 0:
            raise ValueError(
                "pga_threshold must be > 0"
            )

        if rolling_window_seconds <= 0:
            raise ValueError(
                "rolling_window_seconds must be > 0"
            )

        self.sampling_rate = sampling_rate

        self.pga_threshold = pga_threshold

        self.rolling_window_seconds = (
            rolling_window_seconds
        )

        self.window_size = int(
            sampling_rate *
            rolling_window_seconds
        )

        self.samples = deque(
            maxlen=self.window_size
        )

        self.event_active = False

        self.last_pga = 0.0

        self.last_trigger_time = None

        self.lock = Lock()

    def reset(self) -> None:

        with self.lock:

            self.samples.clear()

            self.event_active = False

            self.last_pga = 0.0

            self.last_trigger_time = None

    def update(
        self,
        acceleration: float,
        timestamp: datetime
    ) -> Dict:

        with self.lock:

            acceleration_g = (
                float(acceleration)
                /
                STANDARD_GRAVITY
            )

            self.samples.append(
                acceleration_g
            )

            if len(self.samples) == 0:

                return {
                    "ready": False,
                    "triggered": False,
                    "pga": 0.0
                }

            pga = float(
                np.max(
                    np.abs(
                        np.asarray(
                            self.samples,
                            dtype=np.float64
                        )
                    )
                )
            )

            self.last_pga = pga

            triggered = False

            if (
                not self.event_active
                and pga >= self.pga_threshold
            ):

                self.event_active = True

                triggered = True

                self.last_trigger_time = (
                    timestamp
                )

            released = False

            if (
                self.event_active
                and pga < (
                    self.pga_threshold * 0.7
                )
            ):

                self.event_active = False

                released = True

            return {
                "ready": True,
                "triggered": triggered,
                "released": released,
                "event_active": self.event_active,
                "pga": pga,
                "threshold":
                    self.pga_threshold,
                "timestamp":
                    timestamp,
                "severity":
                    self._severity_level(pga)
            }

    def _severity_level(
        self,
        pga: float
    ) -> str:

        if pga < 0.02:
            return "LOW"

        if pga < 0.05:
            return "MODERATE"

        if pga < 0.10:
            return "HIGH"

        if pga < 0.20:
            return "SEVERE"

        return "EXTREME"

    def current_pga(self) -> float:

        with self.lock:
            return self.last_pga

    def is_event_active(self) -> bool:

        with self.lock:
            return self.event_active

    def statistics(self) -> Dict:

        with self.lock:

            return {
                "sampling_rate":
                    self.sampling_rate,

                "window_size":
                    self.window_size,

                "rolling_window_seconds":
                    self.rolling_window_seconds,

                "threshold":
                    self.pga_threshold,

                "current_pga":
                    self.last_pga,

                "event_active":
                    self.event_active,

                "last_trigger_time":
                    self.last_trigger_time
            }

    def process_batch(
        self,
        samples,
        timestamps
    ):

        if len(samples) != len(timestamps):

            raise ValueError(
                "samples and timestamps length mismatch"
            )

        results = []

        for sample, timestamp in zip(
            samples,
            timestamps
        ):

            results.append(
                self.update(
                    sample,
                    timestamp
                )
            )

        return results