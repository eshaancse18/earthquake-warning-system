from collections import deque
from threading import Lock
from typing import List, Dict, Any
from datetime import datetime
import copy


class CircularBuffer:
    """
    Thread-safe circular buffer for continuous seismic acquisition.

    Stores:
    timestamp
    sensor value

    Automatically removes oldest samples when full.
    """

    def __init__(self, max_samples: int):

        if max_samples <= 0:
            raise ValueError(
                "max_samples must be greater than zero"
            )

        self._max_samples = max_samples

        self._buffer = deque(maxlen=max_samples)

        self._lock = Lock()

    @property
    def max_samples(self) -> int:
        return self._max_samples

    def append(
        self,
        timestamp: datetime,
        value: float
    ) -> None:

        sample = {
            "timestamp": timestamp,
            "value": float(value)
        }

        with self._lock:
            self._buffer.append(sample)

    def extend(
        self,
        samples: List[Dict[str, Any]]
    ) -> None:

        with self._lock:

            for sample in samples:

                if "timestamp" not in sample:
                    raise ValueError(
                        "Missing timestamp field"
                    )

                if "value" not in sample:
                    raise ValueError(
                        "Missing value field"
                    )

                self._buffer.append(
                    {
                        "timestamp": sample["timestamp"],
                        "value": float(sample["value"])
                    }
                )

    def clear(self) -> None:

        with self._lock:
            self._buffer.clear()

    def size(self) -> int:

        with self._lock:
            return len(self._buffer)

    def is_empty(self) -> bool:

        with self._lock:
            return len(self._buffer) == 0

    def is_full(self) -> bool:

        with self._lock:
            return len(self._buffer) == self._max_samples

    def latest(self):

        with self._lock:

            if not self._buffer:
                return None

            return copy.deepcopy(
                self._buffer[-1]
            )

    def oldest(self):

        with self._lock:

            if not self._buffer:
                return None

            return copy.deepcopy(
                self._buffer[0]
            )

    def get_all(self) -> List[Dict[str, Any]]:

        with self._lock:

            return copy.deepcopy(
                list(self._buffer)
            )

    def get_last_n_samples(
        self,
        count: int
    ) -> List[Dict[str, Any]]:

        if count <= 0:
            return []

        with self._lock:

            result = list(self._buffer)[-count:]

            return copy.deepcopy(result)

    def get_samples_between(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:

        if start_time > end_time:
            raise ValueError(
                "start_time cannot be greater than end_time"
            )

        with self._lock:

            results = []

            for sample in self._buffer:

                timestamp = sample["timestamp"]

                if start_time <= timestamp <= end_time:

                    results.append(
                        copy.deepcopy(sample)
                    )

            return results

    def statistics(self) -> Dict[str, Any]:

        with self._lock:

            count = len(self._buffer)

            if count == 0:

                return {
                    "count": 0,
                    "min": 0.0,
                    "max": 0.0,
                    "average": 0.0
                }

            values = [
                item["value"]
                for item in self._buffer
            ]

            minimum = min(values)

            maximum = max(values)

            average = sum(values) / count

            return {
                "count": count,
                "min": minimum,
                "max": maximum,
                "average": average
            }

    def snapshot(self) -> List[Dict[str, Any]]:
        """
        Returns a frozen copy of current buffer.

        Used when an earthquake is detected so
        pre-event waveform can be preserved.
        """

        with self._lock:

            return copy.deepcopy(
                list(self._buffer)
            )

    def __len__(self) -> int:

        return self.size()

    def __repr__(self) -> str:

        return (
            f"CircularBuffer("
            f"max_samples={self._max_samples}, "
            f"current_size={self.size()}"
            f")"
        )