import math
import queue
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import numpy as np

from buffering.circular_buffer import CircularBuffer
from buffering.event_buffer import EventBuffer
from buffering.waveform_storage import WaveformStorage
from processing.event_detector import EventDetector
from logging_system.logger import get_logger, EventLogger


class SensorManager(threading.Thread):
    """
    Production Sensor Manager

    Responsibilities
    ----------------
    1. Receive ADXL355 samples
    2. Apply GPS timestamps
    3. Compute vector magnitude
    4. Remove gravity component
    5. Maintain circular buffer
    6. Run EventDetector
    7. Manage EventBuffer lifecycle
    8. Store waveform files
    9. Forward confirmed events
    10. Provide health metrics
    """

    def __init__(
        self,
        station_id: str,
        sample_queue: queue.Queue,
        event_queue: queue.Queue,
        gps_reader,
        circular_buffer: CircularBuffer,
        event_buffer: EventBuffer,
        waveform_storage: WaveformStorage,
        event_detector: EventDetector,
        sampling_rate: int,
    ):
        super().__init__(
            name="SENSOR_MANAGER_THREAD",
            daemon=True,
        )

        self.station_id = station_id
        self.sample_queue = sample_queue
        self.event_queue = event_queue
        self.gps_reader = gps_reader
        self.circular_buffer = circular_buffer
        self.event_buffer = event_buffer
        self.waveform_storage = waveform_storage
        self.event_detector = event_detector
        self.sampling_rate = sampling_rate

        self.logger = get_logger("SensorManager")
        self.event_logger = EventLogger()

        self.stop_event = threading.Event()

        self.processed_samples = 0
        self.confirmed_events = 0
        self.rejected_events = 0
        self.failed_events = 0

        self.last_sample_timestamp = None
        self.last_processing_time = None
        self.event_start_index = None

        self.current_event_active = False
        self.current_event_metadata = None
        self.post_event_counter = 0

        self.required_post_event_samples = sampling_rate * 30

        self.gravity_window = deque(maxlen=sampling_rate * 20)
        self.waveform_window = deque(maxlen=sampling_rate * 20)

        self.health_lock = threading.Lock()

    def stop(self) -> None:
        self.stop_event.set()

    def _utc_now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _gps_timestamp(self) -> datetime:
        try:
            if self.gps_reader is not None and self.gps_reader.is_locked():
                return self.gps_reader.get_timestamp()
        except Exception:
            pass

        return self._utc_now()

    def _calculate_magnitude(
        self,
        ax: float,
        ay: float,
        az: float,
    ) -> float:
        return math.sqrt(
            (ax * ax) +
            (ay * ay) +
            (az * az)
        )

    def _estimate_gravity(self, magnitude: float) -> float:
        self.gravity_window.append(magnitude)

        if len(self.gravity_window) < (self.sampling_rate * 5):
            return 9.81

        return float(np.mean(self.gravity_window))

    def _remove_gravity(self, magnitude: float) -> float:
        gravity = self._estimate_gravity(magnitude)
        return magnitude - gravity

    def _create_seismic_value(self, sample: Dict[str, Any]) -> float:
        ax = float(sample["ax"])
        ay = float(sample["ay"])
        az = float(sample["az"])

        magnitude = self._calculate_magnitude(ax, ay, az)
        seismic_value = self._remove_gravity(magnitude)
        return seismic_value

    def _start_event(
        self,
        timestamp: datetime,
        metadata: Dict[str, Any],
    ) -> None:

        print("START_EVENT CALLED")
        # self.confirmed_events += 1  

        snapshot = self.circular_buffer.snapshot()

        self.event_buffer.start_event(
            event_timestamp=timestamp,
            pre_event_snapshot=snapshot,
            metadata=metadata,
        )

        self.current_event_active = True
        self.event_start_index = self.processed_samples
#         self.event_queue.put(
#     {
#         "event_id": metadata["event_id"],
#         "station_id": self.station_id,
#         "confirmed": True,
#         "confidence": metadata["confidence"],
#         "pga": metadata["pga"],
#         "stalta_ratio": metadata["stalta_ratio"],
#     }
# )

        print("ACTIVE SET TO TRUE")
        print("current_event_active =", self.current_event_active)




        
        self.current_event_metadata = metadata
        self.post_event_counter = 0


        self.logger.info(
            (
                "EVENT_STARTED | "
                f"event_id={metadata['event_id']}"
            )
        )

    def _append_active_event_sample(
        self,
        timestamp: datetime,
        seismic_value: float,
    ) -> None:
        self.event_buffer.append_event_sample(
            timestamp=timestamp,
            value=seismic_value,
        )

    def _append_post_event_sample(
        self,
        timestamp: datetime,
        seismic_value: float,
    ) -> None:
        self.event_buffer.append_post_event_sample(
            timestamp=timestamp,
            value=seismic_value,
        )

    def _save_waveform(
        self,
        event_record: Dict[str, Any],
    ) -> Dict[str, str]:
        paths = self.waveform_storage.save_event(event_record)

        self.logger.info(
            (
                "WAVEFORM_SAVED | "
                f"event_id={event_record['event_id']} | "
                f"json={paths['json_path']} | "
                f"csv={paths['csv_path']}"
            )
        )

        return paths
    
    def _finish_event(
        self,
        timestamp: datetime
    ) -> None:

        print("FINISH_EVENT CALLED")

        try:
            self.event_buffer.stop_event(
                event_timestamp=timestamp
            )

            record = (
                self.event_buffer
                .build_event_record()
            )

            if self.current_event_metadata:

                metadata = record.get(
                    "metadata",
                    {}
                )

                metadata.update(
                    self.current_event_metadata
                )

                record["metadata"] = metadata

            print("EVENT RECORD KEYS")
            print(record.keys())

            print("HAS WAVEFORM =",
                "waveform" in record)

            self._save_waveform(record)
            record["station_id"] = self.station_id
            record["confirmed"] = True
            record["confidence"] = self.current_event_metadata.get("confidence")
            record["pga"] = self.current_event_metadata.get("pga")
            record["stalta_ratio"] = self.current_event_metadata.get("stalta_ratio")
            self.event_queue.put(
                record,
                timeout=5
            )
            print("EVENT ADDED TO QUEUE")
            print("QUEUE SIZE =", self.event_queue.qsize())
            print("CONFIRMED EVENTS =", self.confirmed_events)

            print(
                    "BEFORE INCREMENT",
                    self.confirmed_events
                )

            self.confirmed_events += 1

            print(
                "AFTER INCREMENT",
                self.confirmed_events
            )

            self.current_event_active = False

            self.current_event_metadata = None

            self.post_event_counter = 0

            self.event_buffer.reset()

            self.logger.info(
                "EVENT_FINISHED | "
                f"event_id={record['event_id']}"
            )

        except Exception as error:

            self.failed_events += 1

            self.logger.exception(
                "EVENT_FINALIZATION_FAILED | "
                f"{error}"
            )
    # def _finish_event(self, timestamp: datetime) -> None:
    #     print("FINISH_EVENT CALLED")
    #     try:
    #         self.event_buffer.stop_event(
    #             event_timestamp=timestamp
    #         )

    #         record = self.event_buffer.build_event_record()

    #         if self.current_event_metadata is not None:
    #             metadata = record.get("metadata", {})
    #             metadata.update(self.current_event_metadata)
    #             record["metadata"] = metadata

    #         self._save_waveform(record)

    #         self.event_queue.put(
    #             record,
    #             timeout=5,
    #         )
    #         self.confirmed_events += 1

    #         self.current_event_active = False
    #         self.current_event_metadata = None
    #         self.post_event_counter = 0

    #         self.event_buffer.reset()

    #         self.logger.info(
    #             (
    #                 "EVENT_FINISHED | "
    #                 f"event_id={record['event_id']}"
    #             )
    #         )

    #     except Exception as error:
    #         self.failed_events += 1
    #         self.logger.exception(
    #             (
    #                 "EVENT_FINALIZATION_FAILED | "
    #                 f"{error}"
    #             )
    #         )

    def _build_event_metadata(
        self,
        detection_result: Dict[str, Any],
        timestamp: datetime,
    ) -> Dict[str, Any]:
        return {
            "event_id": detection_result["event_id"],
            "station_id": self.station_id,
            "confidence": detection_result["confidence"],
            "pga": detection_result["pga"],
            "stalta_ratio": detection_result["stalta_ratio"],
            "p_wave_time": detection_result["p_wave_time"],
            "event_start_time": timestamp.isoformat(),
        }

    def _evaluate_detection(
        self,
        timestamp: datetime,
    ) -> Optional[Dict[str, Any]]:
        if len(self.waveform_window) < (self.sampling_rate * 5):
            return None

        waveform = list(self.waveform_window)

        result = self.event_detector.evaluate_waveform(
            waveform=waveform,
            timestamp=timestamp,
            station_id=self.station_id,
        )

        return result

    def _process_detector(
        self,
        timestamp: datetime,
        seismic_value: float,
    ) -> None:

        self.event_detector.process_sample(
            seismic_value,
            timestamp,
        )

        self.waveform_window.append(
            seismic_value
        )

        detection_result = self._evaluate_detection(
            timestamp
        )

        if detection_result is None:
            return

        print(
            "confirmed =",
            detection_result.get("confirmed", False),
            "active =",
            self.current_event_active
        )

        if (
            detection_result.get("confirmed", False)
            and not self.current_event_active
        ):

            # IMPORTANT
            # self.confirmed_events += 1

            # print(
            #     "CONFIRMED_EVENTS =",
            #     self.confirmed_events
            # )

            metadata = self._build_event_metadata(
                detection_result,
                timestamp,
            )

            self._start_event(
                timestamp=timestamp,
                metadata=metadata,
            )

            return

        if not detection_result.get("confirmed", False):
            self.rejected_events += 1

    def _process_active_event(
        self,
        timestamp: datetime,
        seismic_value: float,
    ) -> None:

        if not self.current_event_active:
            return

        self._append_active_event_sample(
            timestamp,
            seismic_value,
        )
        print(
            "EVENT AGE =",
            self.processed_samples -
            self.event_start_index
        )

        stalta_active = (
            self.event_detector
            .stalta_detector
            .is_event_active()
        )

        pga_active = (
            self.event_detector
            .pga_detector
            .is_event_active()
        )

        detector_active = (
            stalta_active or pga_active
        )

        print(
            "ACTIVE_CHECK",
            "stalta=", stalta_active,
            "ratio=", self.event_detector.stalta_detector.current_ratio(),
            "pga=", pga_active,
            "pga_val=", self.event_detector.pga_detector.current_pga(),
            "post=", self.post_event_counter,
        )

        if detector_active:

            active_duration = (
                self.processed_samples -
                self.event_start_index
            )

            if active_duration > (
                self.sampling_rate * 5
            ):
                print("FORCED EVENT FINALIZATION")
                self._finish_event(timestamp)
                return

            return

        self.post_event_counter += 1

        # Store post-event sample FIRST
        self._append_post_event_sample(
            timestamp,
            seismic_value,
        )

        if (
            self.post_event_counter >=
            self.required_post_event_samples
        ):
            print(
                "FINALIZING EVENT",
                "post=",
                self.post_event_counter,
                "required=",
                self.required_post_event_samples,
            )

            self._finish_event(timestamp)   

    # def _process_active_event(
    #     self,
    #     timestamp: datetime,
    #     seismic_value: float,
    # ) -> None:
    #     if not self.current_event_active:
    #         return

    #     self._append_active_event_sample(
    #         timestamp,
    #         seismic_value,
    #     )
        

    #     stalta_active = self.event_detector.stalta_detector.is_event_active()
    #     pga_active = self.event_detector.pga_detector.is_event_active()

    #     detector_active = stalta_active or pga_active
    #     print(
    #         "ACTIVE_CHECK",
    #         "stalta=", stalta_active,
    #         "pga=", pga_active,
    #         "pga_val=", self.event_detector.pga_detector.current_pga(),
    #         "post=", self.post_event_counter,
    #     )
    #     print(
    #         "ACTIVE_CHECK",
    #         stalta_active,
    #         pga_active,
    #         self.post_event_counter,
    #     )

    #     if detector_active:
    #         self.post_event_counter = 0
    #         return

    #     self.post_event_counter += 1
    #     if self.post_event_counter >= self.required_post_event_samples:
    #         print("FINALIZING EVENT")
    #         self._finish_event(timestamp)

    #     self._append_post_event_sample(
    #         timestamp,
    #         seismic_value,
    #     )

    #     # if self.post_event_counter >= self.required_post_event_samples:
    #     #     self._finish_event(timestamp)

    def run(self) -> None:
        self.logger.info(
            (
                "SENSOR_MANAGER_STARTED | "
                f"station_id={self.station_id}"
            )
        )

        while not self.stop_event.is_set():
            try:
                sample = self.sample_queue.get(timeout=1)

                timestamp = self._gps_timestamp()

                seismic_value = self._create_seismic_value(sample)

                self.circular_buffer.append(
                    timestamp=timestamp,
                    value=seismic_value,
                )

                self._process_detector(
                    timestamp,
                    seismic_value,
                )

                self._process_active_event(
                    timestamp,
                    seismic_value,
                )

                self.processed_samples += 1
                self.last_sample_timestamp = timestamp
                self.last_processing_time = self._utc_now()

            except queue.Empty:
                continue

            except Exception as error:
                self.logger.exception(
                    (
                        "SENSOR_MANAGER_ERROR | "
                        f"{error}"
                    )
                )
        if self.current_event_active:
            self._finish_event(self._utc_now())     

        if self.current_event_active:
            print("FORCE FINALIZING ACTIVE EVENT")
            self._finish_event(
                self._utc_now()
        )       

        self.logger.info(
            (
                "SENSOR_MANAGER_STOPPED | "
                f"station_id={self.station_id}"
            )
        )

    def statistics(self) -> Dict[str, Any]:
        with self.health_lock:
            gps_locked = False
            gps_healthy = False

            try:
                if self.gps_reader:
                    gps_locked = self.gps_reader.is_locked()
                    gps_healthy = self.gps_reader.is_healthy()
            except Exception:
                pass

            queue_depth = 0

            try:
                queue_depth = self.sample_queue.qsize()
            except Exception:
                pass

            return {
                "station_id": self.station_id,
                "processed_samples": self.processed_samples,
                "confirmed_events": self.confirmed_events,
                "rejected_events": self.rejected_events,
                "failed_events": self.failed_events,
                "event_active": self.current_event_active,
                "gps_locked": gps_locked,
                "gps_healthy": gps_healthy,
                "sample_queue_depth": queue_depth,
                "waveform_window_size": len(self.waveform_window),
                "gravity_window_size": len(self.gravity_window),
                "last_sample_timestamp": self.last_sample_timestamp,
                "last_processing_time": self.last_processing_time,
            }

    def is_healthy(self) -> bool:
        try:
            if self.sample_queue.qsize() > 5000:
                return False
        except Exception:
            pass

        if self.last_processing_time is not None:
            age = (
                self._utc_now() -
                self.last_processing_time
            ).total_seconds()

            if age > 10:
                return False

        try:
            if self.gps_reader is not None:
                if not self.gps_reader.is_healthy():
                    return False
        except Exception:
            return False

        return True

    def get_last_processing_time(self) -> Optional[datetime]:
        return self.last_processing_time

    def get_processed_samples(self) -> int:
        return self.processed_samples

    def get_confirmed_events(self) -> int:

        print(
            "GET_CONFIRMED_EVENTS =",
            self.confirmed_events
        )

        return self.confirmed_events

    def get_rejected_events(self) -> int:
        return self.rejected_events

    def get_failed_events(self) -> int:
        return self.failed_events