from collections import deque
from datetime import datetime
from threading import Lock
from typing import Dict
from typing import Optional

import numpy as np


class PWaveDetector:
    """
    Production Grade P-Wave Detector

    Designed for:

    - Raspberry Pi
    - ADXL355
    - SSN Embedded Mini
    - Earthquake Early Warning

    Strategy
    --------

    Noise Window:
        Long-term background noise model

    Signal Window:
        Short-term signal energy

    Detection:
        Signal Energy / Noise Energy

    Trigger:
        ratio >= trigger_ratio

    Confidence:
        ratio normalized against trigger

    Cooldown:
        Prevent repeated triggers from
        the same seismic event.
    """

    def __init__(
        self,
        sampling_rate: int,
        noise_window_seconds: int = 20,
        signal_window_seconds: float = 1.0,
        trigger_ratio: float = 4.0,
        minimum_confidence: float = 0.70,
        cooldown_seconds: int = 5
    ):

        if sampling_rate <= 0:
            raise ValueError(
                "sampling_rate must be > 0"
            )

        if noise_window_seconds <= 0:
            raise ValueError(
                "noise_window_seconds must be > 0"
            )

        if signal_window_seconds <= 0:
            raise ValueError(
                "signal_window_seconds must be > 0"
            )

        self.sampling_rate = sampling_rate

        self.noise_window_seconds = (
            noise_window_seconds
        )

        self.signal_window_seconds = (
            signal_window_seconds
        )

        self.trigger_ratio = (
            trigger_ratio
        )

        self.minimum_confidence = (
            minimum_confidence
        )

        self.cooldown_seconds = (
            cooldown_seconds
        )

        self.noise_samples = int(
            sampling_rate *
            noise_window_seconds
        )

        self.signal_samples = int(
            sampling_rate *
            signal_window_seconds
        )

        self.noise_buffer = deque(
            maxlen=self.noise_samples
        )

        self.signal_buffer = deque(
            maxlen=self.signal_samples
        )

        self.lock = Lock()

        self.last_detection_time = None

        self.last_confidence = 0.0

        self.last_ratio = 0.0

        self.detection_count = 0

    def reset(self) -> None:

        with self.lock:

            self.noise_buffer.clear()

            self.signal_buffer.clear()

            self.last_detection_time = None

            self.last_confidence = 0.0

            self.last_ratio = 0.0

            self.detection_count = 0

    def _energy(
        self,
        value: float
    ) -> float:

        return float(
            value * value
        )

    def _noise_floor(
        self
    ) -> float:

        if len(
            self.noise_buffer
        ) < self.noise_samples:

            return 0.0

        return float(
            np.mean(
                np.asarray(
                    self.noise_buffer,
                    dtype=np.float64
                )
            )
        )

    def _signal_energy(
        self
    ) -> float:

        if len(
            self.signal_buffer
        ) == 0:

            return 0.0

        return float(
            np.mean(
                np.asarray(
                    self.signal_buffer,
                    dtype=np.float64
                )
            )
        )

    def _confidence_score(
        self,
        ratio: float
    ) -> float:

        confidence = min(
            ratio /
            self.trigger_ratio,
            1.0
        )

        return float(
            max(
                0.0,
                confidence
            )
        )

    def _cooldown_active(
        self,
        timestamp: datetime
    ) -> bool:

        if (
            self.last_detection_time
            is None
        ):
            return False

        elapsed = (
            timestamp
            -
            self.last_detection_time
        ).total_seconds()

        return (
            elapsed <
            self.cooldown_seconds
        )

    def update(
        self,
        sample: float,
        timestamp: datetime
    ) -> Dict:

        energy = self._energy(
            sample
        )

        with self.lock:

            self.signal_buffer.append(
                energy
            )

            if len(
                self.noise_buffer
            ) < self.noise_samples:

                self.noise_buffer.append(
                    energy
                )

                return {
                    "ready": False,
                    "p_wave_detected": False,
                    "confidence": 0.0,
                    "energy_ratio": 0.0
                }

            noise_floor = (
                self._noise_floor()
            )

            signal_energy = (
                self._signal_energy()
            )

            if noise_floor <= 1e-12:

                ratio = 0.0

            else:

                ratio = (
                    signal_energy /
                    noise_floor
                )

            confidence = (
                self._confidence_score(
                    ratio
                )
            )

            detected = (

                ratio >= self.trigger_ratio

                and

                confidence >=
                self.minimum_confidence

                and

                not self._cooldown_active(
                    timestamp
                )
            )

            if detected:

                self.last_detection_time = (
                    timestamp
                )

                self.last_confidence = (
                    confidence
                )

                self.last_ratio = (
                    ratio
                )

                self.detection_count += 1

            if ratio < (
                self.trigger_ratio * 0.5
            ):

                self.noise_buffer.append(
                    energy
                )

            return {

                "ready": True,

                "p_wave_detected":
                    detected,

                "p_wave_time":
                    timestamp.isoformat()
                    if detected
                    else None,

                "confidence":
                    confidence,

                "energy_ratio":
                    ratio,

                "noise_floor":
                    noise_floor,

                "signal_energy":
                    signal_energy
            }

    def estimate_warning_time(
        self,
        distance_km: float
    ) -> float:
        """
        Estimate warning time.

        P-wave velocity ≈ 6 km/s
        S-wave velocity ≈ 3.5 km/s
        """

        if distance_km <= 0:

            return 0.0

        p_arrival = (
            distance_km / 6.0
        )

        s_arrival = (
            distance_km / 3.5
        )

        return max(
            0.0,
            s_arrival - p_arrival
        )

    def statistics(
        self
    ) -> Dict:

        with self.lock:

            return {

                "sampling_rate":
                    self.sampling_rate,

                "noise_window_seconds":
                    self.noise_window_seconds,

                "signal_window_seconds":
                    self.signal_window_seconds,

                "trigger_ratio":
                    self.trigger_ratio,

                "minimum_confidence":
                    self.minimum_confidence,

                "last_detection_time":
                    self.last_detection_time,

                "last_confidence":
                    self.last_confidence,

                "last_ratio":
                    self.last_ratio,

                "detection_count":
                    self.detection_count,

                "noise_samples":
                    len(
                        self.noise_buffer
                    ),

                "signal_samples":
                    len(
                        self.signal_buffer
                    )
            }

    def is_p_wave_active(
        self
    ) -> bool:

        with self.lock:

            return (
                self.last_detection_time
                is not None
            )

    def last_detection(
        self
    ) -> Optional[datetime]:

        with self.lock:

            return (
                self.last_detection_time
            )