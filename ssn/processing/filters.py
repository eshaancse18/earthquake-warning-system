import numpy as np
from scipy.signal import butter
from scipy.signal import filtfilt
from scipy.signal import detrend
from typing import List
from typing import Union


class SignalFilter:
    """
    Production-grade seismic signal filtering.

    Features:
    - DC removal
    - Detrending
    - Low-pass filtering
    - High-pass filtering
    - Band-pass filtering
    - Normalization
    - RMS calculation

    Used before:
    - STA/LTA
    - PGA
    - Frequency analysis
    """

    def __init__(self, sampling_rate: int):

        if sampling_rate <= 0:
            raise ValueError(
                "sampling_rate must be greater than zero"
            )

        self.sampling_rate = sampling_rate

        self.nyquist_frequency = (
            sampling_rate / 2.0
        )

    def remove_dc(
        self,
        signal: Union[List[float], np.ndarray]
    ) -> np.ndarray:

        data = np.asarray(
            signal,
            dtype=np.float64
        )

        if data.size == 0:
            return data

        return data - np.mean(data)

    def remove_trend(
        self,
        signal: Union[List[float], np.ndarray]
    ) -> np.ndarray:

        data = np.asarray(
            signal,
            dtype=np.float64
        )

        if data.size < 2:
            return data

        return detrend(data)

    def normalize(
        self,
        signal: Union[List[float], np.ndarray]
    ) -> np.ndarray:

        data = np.asarray(
            signal,
            dtype=np.float64
        )

        if data.size == 0:
            return data

        maximum = np.max(
            np.abs(data)
        )

        if maximum == 0:
            return data

        return data / maximum

    def low_pass(
        self,
        signal: Union[List[float], np.ndarray],
        cutoff_frequency: float,
        order: int = 4
    ) -> np.ndarray:

        if cutoff_frequency <= 0:
            raise ValueError(
                "cutoff_frequency must be positive"
            )

        if cutoff_frequency >= self.nyquist_frequency:
            raise ValueError(
                "cutoff_frequency exceeds Nyquist frequency"
            )

        data = np.asarray(
            signal,
            dtype=np.float64
        )

        if data.size < (order * 3):
            return data

        normalized_cutoff = (
            cutoff_frequency /
            self.nyquist_frequency
        )

        b, a = butter(
            order,
            normalized_cutoff,
            btype="low"
        )

        return filtfilt(
            b,
            a,
            data
        )

    def high_pass(
        self,
        signal: Union[List[float], np.ndarray],
        cutoff_frequency: float,
        order: int = 4
    ) -> np.ndarray:

        if cutoff_frequency <= 0:
            raise ValueError(
                "cutoff_frequency must be positive"
            )

        if cutoff_frequency >= self.nyquist_frequency:
            raise ValueError(
                "cutoff_frequency exceeds Nyquist frequency"
            )

        data = np.asarray(
            signal,
            dtype=np.float64
        )

        if data.size < (order * 3):
            return data

        normalized_cutoff = (
            cutoff_frequency /
            self.nyquist_frequency
        )

        b, a = butter(
            order,
            normalized_cutoff,
            btype="high"
        )

        return filtfilt(
            b,
            a,
            data
        )

    def band_pass(
        self,
        signal: Union[List[float], np.ndarray],
        low_cutoff: float,
        high_cutoff: float,
        order: int = 4
    ) -> np.ndarray:

        if low_cutoff <= 0:
            raise ValueError(
                "low_cutoff must be positive"
            )

        if high_cutoff <= low_cutoff:
            raise ValueError(
                "high_cutoff must be greater than low_cutoff"
            )

        if high_cutoff >= self.nyquist_frequency:
            raise ValueError(
                "high_cutoff exceeds Nyquist frequency"
            )

        data = np.asarray(
            signal,
            dtype=np.float64
        )

        if data.size < (order * 3):
            return data

        normalized_low = (
            low_cutoff /
            self.nyquist_frequency
        )

        normalized_high = (
            high_cutoff /
            self.nyquist_frequency
        )

        b, a = butter(
            order,
            [normalized_low, normalized_high],
            btype="band"
        )

        return filtfilt(
            b,
            a,
            data
        )

    def rms(
        self,
        signal: Union[List[float], np.ndarray]
    ) -> float:

        data = np.asarray(
            signal,
            dtype=np.float64
        )

        if data.size == 0:
            return 0.0

        return float(
            np.sqrt(
                np.mean(
                    np.square(data)
                )
            )
        )

    def peak_amplitude(
        self,
        signal: Union[List[float], np.ndarray]
    ) -> float:

        data = np.asarray(
            signal,
            dtype=np.float64
        )

        if data.size == 0:
            return 0.0

        return float(
            np.max(
                np.abs(data)
            )
        )

    def preprocess(
        self,
        signal: Union[List[float], np.ndarray],
        low_cutoff: float,
        high_cutoff: float
    ) -> np.ndarray:
        """
        Complete preprocessing chain.

        Steps:
        1. DC removal
        2. Detrend
        3. Band-pass filter
        4. Normalize
        """

        data = np.asarray(
            signal,
            dtype=np.float64
        )

        if data.size == 0:
            return data

        data = self.remove_dc(data)

        data = self.remove_trend(data)

        data = self.band_pass(
            data,
            low_cutoff,
            high_cutoff
        )

        data = self.normalize(data)

        return data

    def signal_energy(
        self,
        signal: Union[List[float], np.ndarray]
    ) -> float:

        data = np.asarray(
            signal,
            dtype=np.float64
        )

        if data.size == 0:
            return 0.0

        return float(
            np.sum(
                np.square(data)
            )
        )

    def signal_mean(
        self,
        signal: Union[List[float], np.ndarray]
    ) -> float:

        data = np.asarray(
            signal,
            dtype=np.float64
        )

        if data.size == 0:
            return 0.0

        return float(
            np.mean(data)
        )

    def signal_std(
        self,
        signal: Union[List[float], np.ndarray]
    ) -> float:

        data = np.asarray(
            signal,
            dtype=np.float64
        )

        if data.size == 0:
            return 0.0

        return float(
            np.std(data)
        )