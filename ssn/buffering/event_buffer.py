from datetime import datetime
from threading import RLock
from typing import Dict
from typing import List
from typing import Any
import uuid
import copy


class EventBuffer:
    """
    Production Event Buffer

    Responsibilities
    ----------------
    1. Preserve pre-event waveform
    2. Preserve event waveform
    3. Preserve post-event waveform
    4. Build final event record
    5. Export CRS transmission packet
    """

    def __init__(
        self,
        pre_event_seconds: int,
        event_seconds: int,
        post_event_seconds: int,
        sampling_rate: int
    ):

        if pre_event_seconds <= 0:
            raise ValueError(
                "pre_event_seconds must be > 0"
            )

        if event_seconds <= 0:
            raise ValueError(
                "event_seconds must be > 0"
            )

        if post_event_seconds <= 0:
            raise ValueError(
                "post_event_seconds must be > 0"
            )

        if sampling_rate <= 0:
            raise ValueError(
                "sampling_rate must be > 0"
            )

        self.pre_event_seconds = (
            pre_event_seconds
        )

        self.event_seconds = (
            event_seconds
        )

        self.post_event_seconds = (
            post_event_seconds
        )

        self.sampling_rate = (
            sampling_rate
        )

        self.lock = RLock()

        self.reset()

    def reset(
        self
    ) -> None:

        with self.lock:

            self.event_id = str(
                uuid.uuid4()
            )

            self.event_active = False

            self.event_confirmed = False

            self.event_start_time = None

            self.event_end_time = None

            self.pre_event_samples = []

            self.event_samples = []

            self.post_event_samples = []

            self.metadata = {}

    def start_event(
        self,
        event_timestamp: datetime,
        pre_event_snapshot: List[
            Dict[str, Any]
        ],
        metadata: Dict[str, Any]
    ) -> None:

        with self.lock:

            if self.event_active:

                return

            self.event_id = str(
                uuid.uuid4()
            )

            self.event_active = True

            self.event_confirmed = False

            self.event_start_time = (
                event_timestamp
            )

            self.event_end_time = None

            self.pre_event_samples = (
                copy.deepcopy(
                    pre_event_snapshot
                )
            )

            self.event_samples = []

            self.post_event_samples = []

            self.metadata = (
                copy.deepcopy(
                    metadata
                )
            )

    def stop_event(
        self,
        event_timestamp: datetime
    ) -> None:

        with self.lock:

            if not self.event_active:

                return

            self.event_end_time = (
                event_timestamp
            )

            self.event_confirmed = True

            self.event_active = False

    def append_event_sample(
        self,
        timestamp: datetime,
        value: float
    ) -> None:

        with self.lock:

            if not self.event_active:

                return

            self.event_samples.append(
                {
                    "timestamp":
                        timestamp,

                    "value":
                        float(value)
                }
            )

    def append_post_event_sample(
        self,
        timestamp: datetime,
        value: float
    ) -> None:

        with self.lock:

            self.post_event_samples.append(
                {
                    "timestamp":
                        timestamp,

                    "value":
                        float(value)
                }
            )

    def is_active(
        self
    ) -> bool:

        with self.lock:

            return self.event_active

    def is_confirmed(
        self
    ) -> bool:

        with self.lock:

            return self.event_confirmed

    def total_samples(
        self
    ) -> int:

        with self.lock:

            return (

                len(
                    self.pre_event_samples
                )

                +

                len(
                    self.event_samples
                )

                +

                len(
                    self.post_event_samples
                )
            )

    def get_waveform(
        self
    ) -> List[Dict]:

        with self.lock:

            waveform = []

            waveform.extend(
                copy.deepcopy(
                    self.pre_event_samples
                )
            )

            waveform.extend(
                copy.deepcopy(
                    self.event_samples
                )
            )

            waveform.extend(
                copy.deepcopy(
                    self.post_event_samples
                )
            )

            return waveform

    def peak_amplitude(
        self
    ) -> float:

        waveform = (
            self.get_waveform()
        )

        if not waveform:

            return 0.0

        return max(
            abs(
                sample["value"]
            )
            for sample in waveform
        )

    def duration_seconds(
        self
    ) -> float:

        with self.lock:

            if (
                self.event_start_time
                is None
            ):

                return 0.0

            end_time = (
                self.event_end_time
                if self.event_end_time
                else self.event_start_time
            )

            return (
                end_time
                -
                self.event_start_time
            ).total_seconds()

    def build_event_record(
        self
    ) -> Dict[str, Any]:

        with self.lock:

            waveform = (
                self.get_waveform()
            )

            return {

                "event_id":
                    self.event_id,

                "event_start_time":
                    (
                        self.event_start_time
                        .isoformat()
                        if self.event_start_time
                        else None
                    ),

                "event_end_time":
                    (
                        self.event_end_time
                        .isoformat()
                        if self.event_end_time
                        else None
                    ),

                "event_duration_seconds":
                    self.duration_seconds(),

                "peak_amplitude":
                    self.peak_amplitude(),

                "metadata":
                    copy.deepcopy(
                        self.metadata
                    ),

                "pre_event_samples":
                    len(
                        self.pre_event_samples
                    ),

                "event_samples":
                    len(
                        self.event_samples
                    ),

                "post_event_samples":
                    len(
                        self.post_event_samples
                    ),

                "total_samples":
                    len(
                        waveform
                    ),

                "waveform":
                    waveform
            }

    def export_for_transmission(
        self
    ) -> Dict[str, Any]:

        with self.lock:

            waveform = (
                self.get_waveform()
            )

            compact_waveform = []

            for sample in waveform:

                compact_waveform.append(
                    {
                        "t":
                            sample[
                                "timestamp"
                            ].isoformat(),

                        "v":
                            sample[
                                "value"
                            ]
                    }
                )

            return {

                "event_id":
                    self.event_id,

                "event_start_time":
                    (
                        self.event_start_time
                        .isoformat()
                        if self.event_start_time
                        else None
                    ),

                "event_end_time":
                    (
                        self.event_end_time
                        .isoformat()
                        if self.event_end_time
                        else None
                    ),

                "metadata":
                    copy.deepcopy(
                        self.metadata
                    ),

                "waveform":
                    compact_waveform
            }

    def get_event_summary(
        self
    ) -> Dict[str, Any]:

        with self.lock:

            return {

                "event_id":
                    self.event_id,

                "active":
                    self.event_active,

                "confirmed":
                    self.event_confirmed,

                "duration_seconds":
                    self.duration_seconds(),

                "peak_amplitude":
                    self.peak_amplitude(),

                "pre_event_count":
                    len(
                        self.pre_event_samples
                    ),

                "event_count":
                    len(
                        self.event_samples
                    ),

                "post_event_count":
                    len(
                        self.post_event_samples
                    ),

                "total_count":
                    self.total_samples()
            }

    def discard(
        self
    ) -> None:

        self.reset()

    def __repr__(
        self
    ) -> str:

        return (

            f"EventBuffer("
            f"event_id={self.event_id}, "
            f"active={self.event_active}, "
            f"confirmed={self.event_confirmed}, "
            f"samples={self.total_samples()}"
            f")"
        )