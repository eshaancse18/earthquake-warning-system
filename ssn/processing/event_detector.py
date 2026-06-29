from datetime import datetime
from threading import RLock
from typing import Dict
from typing import List
from typing import Optional

from processing.stalta_detector import STALTADetector
from processing.pga_detector import PGADetector
from processing.frequency_analyzer import FrequencyAnalyzer
from processing.p_wave_detector import PWaveDetector

from logging_system.logger import EventLogger


class EventDetector:
    """
    Production Earthquake Detection Engine

    Responsibilities
    ----------------
    1. STA/LTA Trigger Detection
    2. PGA Validation
    3. Frequency Validation
    4. P-Wave Detection
    5. Confidence Scoring

    IMPORTANT

    This class DOES NOT manage event lifecycle.

    Event lifecycle is managed by:

        EventBuffer

    This class only answers:

        "Is this waveform likely an earthquake?"
    """

    def __init__(
        self,
        sampling_rate: int,
        stalta_threshold: float,
        pga_threshold: float,
        low_frequency: float,
        high_frequency: float,
        p_wave_trigger_ratio: float = 4.0,
        minimum_confidence: float = 0.75
    ):

        self.lock = RLock()

        self.logger = EventLogger()

        self.sampling_rate = sampling_rate

        self.minimum_confidence = (
            minimum_confidence
        )

        self.stalta_detector = (
            STALTADetector(
                sampling_rate=sampling_rate,
                sta_window_seconds=1.0,
                lta_window_seconds=10.0,
                trigger_on=stalta_threshold,
                trigger_off=(
                    stalta_threshold * 0.60
                )
            )
        )

        self.pga_detector = (
            PGADetector(
                sampling_rate=sampling_rate,
                pga_threshold=pga_threshold
            )
        )

        self.frequency_analyzer = (
            FrequencyAnalyzer(
                sampling_rate=sampling_rate,
                earthquake_low_hz=low_frequency,
                earthquake_high_hz=high_frequency
            )
        )

        self.p_wave_detector = (
            PWaveDetector(
                sampling_rate=sampling_rate,
                trigger_ratio=(
                    p_wave_trigger_ratio
                )
            )
        )

        self.event_counter = 0

        self.last_detection_time = None

        self.last_result = None

    def reset(
        self
    ) -> None:

        with self.lock:

            self.stalta_detector.reset()

            self.pga_detector.reset()

            self.p_wave_detector.reset()

            self.event_counter = 0

            self.last_detection_time = None

            self.last_result = None

    def process_sample(
        self,
        sample: float,
        timestamp: datetime
    ) -> Dict:

        with self.lock:

            stalta_result = (
                self.stalta_detector.update(
                    sample,
                    timestamp
                )
            )

            pga_result = (
                self.pga_detector.update(
                    sample,
                    timestamp
                )
            )

            p_wave_result = (
                self.p_wave_detector.update(
                    sample,
                    timestamp
                )
            )

            return {

                "stalta":
                    stalta_result,

                "pga":
                    pga_result,

                "p_wave":
                    p_wave_result
            }

    def evaluate_waveform(
        self,
        waveform: List[float],
        timestamp: datetime,
        station_id: str
    ) -> Dict:

        with self.lock:

            if len(waveform) < (
                self.sampling_rate * 5
            ):

                result = self._rejected(
                    "INSUFFICIENT_DATA"
                )

                self.last_result = result

                return result

            frequency_result = (
                self.frequency_analyzer.analyze(
                    waveform
                )
            )

            stalta_ratio = (
                self.stalta_detector
                .current_ratio()
            )

            pga_value = (
                self.pga_detector
                .current_pga()
            )

            p_wave_time = (
                self.p_wave_detector
                .last_detection()
            )

            stalta_triggered = (
                stalta_ratio
                >=
                self.stalta_detector
                .trigger_on
            )

            pga_triggered = (
                pga_value
                >=
                self.pga_detector
                .pga_threshold
            )

            frequency_valid = (
                frequency_result[
                    "earthquake_like"
                ]
            )

            p_wave_detected = (
                p_wave_time is not None
            )

            confidence = (
                self._confidence_score(
                    stalta_ratio,
                    pga_value,
                    frequency_result[
                        "confidence"
                    ],
                    self.p_wave_detector
                    .last_confidence
                )
            )

            print("\nCHECKS")
            print("stalta_ratio =", stalta_ratio)
            print("trigger_on =", self.stalta_detector.trigger_on)
            print("stalta_triggered =", stalta_triggered)

            print("pga_value =", pga_value)
            print("pga_threshold =", self.pga_detector.pga_threshold)
            print("pga_triggered =", pga_triggered)

            print("frequency_valid =", frequency_valid)
            print("p_wave_detected =", p_wave_detected)

            print("confidence =", confidence)
            print("minimum_confidence =", self.minimum_confidence)

            confirmed = (

                stalta_triggered

                and

                pga_triggered

                and

                frequency_valid

                and

                p_wave_detected

                and

                confidence >=
                self.minimum_confidence
            )

            if not confirmed:

                result = self._rejected(
                    self._rejection_reason(
                        stalta_triggered,
                        pga_triggered,
                        frequency_valid,
                        p_wave_detected,
                        confidence
                    )
                )

                self.last_result = result

                return result

            event_id = (
                self._generate_event_id(
                    station_id,
                    timestamp
                )
            )

            self.event_counter += 1

            self.last_detection_time = (
                timestamp
            )

            result = {

                "confirmed": True,

                "event_id":
                    event_id,

                "station_id":
                    station_id,

                "timestamp":
                    timestamp.isoformat(),

                "confidence":
                    confidence,

                "stalta_ratio":
                    stalta_ratio,

                "pga":
                    pga_value,

                "frequency":
                    frequency_result,

                "p_wave_time":
                    (
                        p_wave_time.isoformat()
                        if p_wave_time
                        else None
                    )
            }

            self.last_result = result

            self.logger.event_detected(
                event_id=event_id,
                station_id=station_id,
                pga=pga_value,
                stalta_ratio=stalta_ratio
            )

            self.logger.event_confirmed(
                event_id=event_id,
                station_id=station_id,
                confidence=confidence
            )

            return result

    def _confidence_score(
        self,
        stalta_ratio: float,
        pga_value: float,
        fft_confidence: float,
        p_wave_confidence: float
    ) -> float:

        stalta_score = min(
            stalta_ratio / 6.0,
            1.0
        )

        pga_score = min(
            pga_value / 0.20,
            1.0
        )

        confidence = (

            stalta_score * 0.25

            +

            pga_score * 0.25

            +

            fft_confidence * 0.20

            +

            p_wave_confidence * 0.30
        )

        return max(
            0.0,
            min(confidence, 1.0)
        )

    def _rejection_reason(
        self,
        stalta_triggered: bool,
        pga_triggered: bool,
        frequency_valid: bool,
        p_wave_detected: bool,
        confidence: float
    ) -> str:

        if not stalta_triggered:
            return "STALTA_REJECT"

        if not pga_triggered:
            return "PGA_REJECT"

        if not frequency_valid:
            return "FFT_REJECT"

        if not p_wave_detected:
            return "PWAVE_REJECT"

        if confidence < (
            self.minimum_confidence
        ):
            return "LOW_CONFIDENCE"

        return "UNKNOWN"

    def _generate_event_id(
        self,
        station_id: str,
        timestamp: datetime
    ) -> str:

        return (

            f"{station_id}_"
            f"{timestamp.strftime('%Y%m%d%H%M%S%f')}"
        )

    def _rejected(
        self,
        reason: str
    ) -> Dict:

        return {

            "confirmed": False,

            "reason": reason,

            "frequency": {
                "earthquake_like": False,
                "dominant_frequency": 0.0,
                "energy_ratio": 0.0,
                "confidence": 0.0
            },

            "pga": 0.0,

            "stalta_ratio": 0.0,

            "p_wave_time": None
        }

    def statistics(
        self
    ) -> Dict:

        with self.lock:

            return {

                "event_counter":
                    self.event_counter,

                "last_detection_time":
                    self.last_detection_time,

                "last_result":
                    self.last_result,

                "stalta_ratio":
                    self.stalta_detector
                    .current_ratio(),

                "pga":
                    self.pga_detector
                    .current_pga(),

                "p_wave_confidence":
                    self.p_wave_detector
                    .last_confidence
            }

    def get_last_event(
        self
    ) -> Optional[Dict]:

        with self.lock:

            return self.last_result

    def is_detection_ready(
        self
    ) -> bool:

        with self.lock:

            return (
                self.stalta_detector
                .current_ratio()
                is not None
            )