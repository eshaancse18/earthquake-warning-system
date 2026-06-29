import numpy as np
from scipy.fft import fft
from scipy.fft import fftfreq
from typing import Dict
from typing import List
from typing import Union
from threading import Lock


class FrequencyAnalyzer:
    """
    Frequency-domain validation engine.

    Purpose:
    --------
    Distinguish earthquakes from:

    - Metro movement
    - Cars
    - Construction
    - Machinery
    - Drilling
    - Electrical noise

    Uses FFT analysis.

    Produces:
    - Dominant frequency
    - Spectral energy
    - Earthquake confidence score
    """

    def __init__(
        self,
        sampling_rate: int,
        earthquake_low_hz: float = 0.5,
        earthquake_high_hz: float = 20.0
    ):

        if sampling_rate <= 0:
            raise ValueError(
                "sampling_rate must be > 0"
            )

        if earthquake_low_hz <= 0:
            raise ValueError(
                "earthquake_low_hz must be > 0"
            )

        if earthquake_high_hz <= earthquake_low_hz:
            raise ValueError(
                "earthquake_high_hz must be greater than earthquake_low_hz"
            )

        self.sampling_rate = sampling_rate

        self.earthquake_low_hz = earthquake_low_hz

        self.earthquake_high_hz = earthquake_high_hz

        self.lock = Lock()

    def dominant_frequency(
        self,
        signal: Union[List[float], np.ndarray]
    ) -> float:

        data = np.asarray(
            signal,
            dtype=np.float64
        )

        if len(data) < 4:
            return 0.0

        fft_values = fft(data)

        magnitudes = np.abs(
            fft_values
        )

        frequencies = fftfreq(
            len(data),
            1 / self.sampling_rate
        )

        positive_mask = frequencies > 0

        frequencies = frequencies[
            positive_mask
        ]

        magnitudes = magnitudes[
            positive_mask
        ]

        if len(magnitudes) == 0:
            return 0.0

        index = np.argmax(
            magnitudes
        )

        return float(
            frequencies[index]
        )

    def spectral_energy(
        self,
        signal: Union[List[float], np.ndarray]
    ) -> float:

        data = np.asarray(
            signal,
            dtype=np.float64
        )

        if len(data) == 0:
            return 0.0

        spectrum = np.abs(
            fft(data)
        )

        return float(
            np.sum(
                spectrum ** 2
            )
        )

    def earthquake_band_energy(
        self,
        signal: Union[List[float], np.ndarray]
    ) -> float:

        data = np.asarray(
            signal,
            dtype=np.float64
        )

        if len(data) < 4:
            return 0.0

        spectrum = np.abs(
            fft(data)
        )

        frequencies = fftfreq(
            len(data),
            1 / self.sampling_rate
        )

        mask = (
            (frequencies >= self.earthquake_low_hz)
            &
            (frequencies <= self.earthquake_high_hz)
        )

        return float(
            np.sum(
                spectrum[mask] ** 2
            )
        )

    def total_energy(
        self,
        signal: Union[List[float], np.ndarray]
    ) -> float:

        data = np.asarray(
            signal,
            dtype=np.float64
        )

        if len(data) < 4:
            return 0.0

        spectrum = np.abs(
            fft(data)
        )

        return float(
            np.sum(
                spectrum ** 2
            )
        )

    def energy_ratio(
        self,
        signal: Union[List[float], np.ndarray]
    ) -> float:

        band_energy = (
            self.earthquake_band_energy(
                signal
            )
        )

        total_energy = (
            self.total_energy(
                signal
            )
        )

        if total_energy <= 0:
            return 0.0

        return float(
            band_energy /
            total_energy
        )

    def confidence_score(
        self,
        signal: Union[List[float], np.ndarray]
    ) -> float:

        ratio = self.energy_ratio(
            signal
        )

        dominant = (
            self.dominant_frequency(
                signal
            )
        )

        score = 0.0

        if (
            self.earthquake_low_hz
            <= dominant
            <= self.earthquake_high_hz
        ):
            score += 0.5

        score += min(
            ratio,
            1.0
        ) * 0.5

        return float(
            max(
                0.0,
                min(score, 1.0)
            )
        )

    def validate_event(
        self,
        signal: Union[List[float], np.ndarray]
    ) -> Dict:

        dominant = self.dominant_frequency(
            signal
        )

        ratio = self.energy_ratio(
            signal
        )

        confidence = (
            self.confidence_score(
                signal
            )
        )

        earthquake_like = (
            confidence >= 0.60
        )

        return {
            "earthquake_like":
                earthquake_like,

            "dominant_frequency":
                dominant,

            "energy_ratio":
                ratio,

            "confidence":
                confidence
        }

    def analyze(
        self,
        signal: Union[List[float], np.ndarray]
    ) -> Dict:

        dominant = (
            self.dominant_frequency(
                signal
            )
        )

        spectral_energy = (
            self.spectral_energy(
                signal
            )
        )

        band_energy = (
            self.earthquake_band_energy(
                signal
            )
        )

        total_energy = (
            self.total_energy(
                signal
            )
        )

        ratio = (
            self.energy_ratio(
                signal
            )
        )

        confidence = (
            self.confidence_score(
                signal
            )
        )

        return {
            "dominant_frequency":
                dominant,

            "spectral_energy":
                spectral_energy,

            "earthquake_band_energy":
                band_energy,

            "total_energy":
                total_energy,

            "energy_ratio":
                ratio,

            "confidence":
                confidence,

            "earthquake_like":
                confidence >= 0.60
        }