import numpy as np
from collections import deque
from datetime import datetime
from typing import Dict
from threading import Lock


class STALTADetector:
    """
    Production-grade STA/LTA detector.

    STA = Short Term Average
    LTA = Long Term Average

    Used to detect sudden increases in seismic energy.

    Trigger ON:
        ratio >= trigger_on

    Trigger OFF:
        ratio <= trigger_off
    """

    def __init__(
        self,
        sampling_rate: int,
        sta_window_seconds: float,
        lta_window_seconds: float,
        trigger_on: float,
        trigger_off: float
    ):

        if sampling_rate <= 0:
            raise ValueError(
                "sampling_rate must be > 0"
            )

        if sta_window_seconds <= 0:
            raise ValueError(
                "sta_window_seconds must be > 0"
            )

        if lta_window_seconds <= 0:
            raise ValueError(
                "lta_window_seconds must be > 0"
            )

        if lta_window_seconds <= sta_window_seconds:
            raise ValueError(
                "LTA window must be larger than STA window"
            )

        if trigger_on <= 0:
            raise ValueError(
                "trigger_on must be > 0"
            )

        if trigger_off <= 0:
            raise ValueError(
                "trigger_off must be > 0"
            )

        self.sampling_rate = sampling_rate

        self.sta_window_seconds = sta_window_seconds

        self.lta_window_seconds = lta_window_seconds

        self.trigger_on = trigger_on

        self.trigger_off = trigger_off

        self.sta_samples = int(
            sampling_rate * sta_window_seconds
        )

        self.lta_samples = int(
            sampling_rate * lta_window_seconds
        )

        self.sta_buffer = deque(
            maxlen=self.sta_samples
        )

        self.lta_buffer = deque(
            maxlen=self.lta_samples
        )

        self.event_active = False

        self.last_ratio = 0.0

        self.last_sta = 0.0

        self.last_lta = 0.0

        self.last_trigger_time = None

        self.lock = Lock()

    def reset(self) -> None:

        with self.lock:

            self.sta_buffer.clear()

            self.lta_buffer.clear()

            self.event_active = False

            self.last_ratio = 0.0

            self.last_sta = 0.0

            self.last_lta = 0.0

            self.last_trigger_time = None

    def _signal_energy(
        self,
        value: float
    ) -> float:

        return float(
            value * value
        )

    def update(
        self,
        sample: float,
        timestamp: datetime
    ) -> Dict:

        energy = self._signal_energy(
            sample
        )

        with self.lock:

            self.sta_buffer.append(
                energy
            )

            self.lta_buffer.append(
                energy
            )

            if len(self.lta_buffer) < self.lta_samples:

                return {
                    "ready": False,
                    "triggered": False,
                    "released": False,
                    "ratio": 0.0,
                    "sta": 0.0,
                    "lta": 0.0
                }

            sta = float(
                np.mean(
                    self.sta_buffer
                )
            )

            lta = float(
                np.mean(
                    self.lta_buffer
                )
            )

            if lta <= 1e-12:
                ratio = 0.0
            else:
                ratio = sta / lta

            triggered = False

            released = False

            if (
                not self.event_active
                and ratio >= self.trigger_on
            ):

                self.event_active = True

                triggered = True

                self.last_trigger_time = (
                    timestamp
                )

            elif (
                self.event_active
                and ratio <= self.trigger_off
            ):

                self.event_active = False

                released = True

            self.last_sta = sta

            self.last_lta = lta

            self.last_ratio = ratio

            return {
                "ready": True,
                "triggered": triggered,
                "released": released,
                "ratio": ratio,
                "sta": sta,
                "lta": lta,
                "event_active": self.event_active,
                "timestamp": timestamp
            }

    def current_ratio(self) -> float:

        with self.lock:
            return self.last_ratio

    def current_sta(self) -> float:

        with self.lock:
            return self.last_sta

    def current_lta(self) -> float:

        with self.lock:
            return self.last_lta

    def is_event_active(self) -> bool:

        with self.lock:
            return self.event_active

    def statistics(self) -> Dict:

        with self.lock:

            return {
                "sampling_rate":
                    self.sampling_rate,

                "sta_window_seconds":
                    self.sta_window_seconds,

                "lta_window_seconds":
                    self.lta_window_seconds,

                "sta_samples":
                    self.sta_samples,

                "lta_samples":
                    self.lta_samples,

                "current_ratio":
                    self.last_ratio,

                "current_sta":
                    self.last_sta,

                "current_lta":
                    self.last_lta,

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

            result = self.update(
                sample,
                timestamp
            )

            results.append(
                result
            )

        return results