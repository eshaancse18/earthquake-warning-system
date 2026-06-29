#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import gc
import os
import queue
import sqlite3
import sys
import tempfile
import threading
import time
import traceback
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np


def find_project_root(start: Path) -> Path:
    for candidate in [start] + list(start.parents):
        if (candidate / "config" / "config.yaml").exists() and (
            candidate / "logging_system"
        ).exists():
            return candidate
    raise RuntimeError(
        "Could not locate project root. Run this script inside the SSN project tree."
    )


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = find_project_root(SCRIPT_PATH.parent)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.station_config import get_config, initialize_config

from acquisition.sensor_manager import SensorManager
from buffering.circular_buffer import CircularBuffer
from buffering.event_buffer import EventBuffer
from buffering.waveform_storage import WaveformStorage
from communication.packet_builder import PacketBuilder
from processing.event_detector import EventDetector
from processing.frequency_analyzer import FrequencyAnalyzer
from processing.pga_detector import PGADetector
from processing.p_wave_detector import PWaveDetector
from processing.stalta_detector import STALTADetector

try:
    from storage.local_database import LocalDatabase
except ImportError:
    from database.local_database import LocalDatabase

try:
    from health.diagnostics import Diagnostics
except ImportError:
    from monitoring.diagnostics import Diagnostics


STATION_ID = "SSN_001"
TEST_SAMPLING_RATE = 100
PRE_EVENT_SECONDS = 6
BURST_SECONDS = 4
POST_EVENT_SECONDS = 4


@dataclass(frozen=True)
class CaseDefinition:
    name: str
    kind: str
    expected_event: bool
    seed: int


CASES = [
    CaseDefinition("Noise", "noise", False, 101),
    CaseDefinition("Metro", "metro", False, 202),
    CaseDefinition("Construction", "construction", False, 303),
    CaseDefinition("Earthquake", "earthquake", True, 404),
]


class IntegrationError(RuntimeError):
    pass


class FakeGPSReader:
    def __init__(self, start_time: Optional[datetime] = None, step_seconds: float = 0.01):
        self._current_time = start_time or datetime.now(timezone.utc)
        self._step = timedelta(seconds=step_seconds)
        self._locked = True
        self._healthy = True
        self._calls = 0

    def is_locked(self) -> bool:
        return self._locked

    def is_healthy(self) -> bool:
        return self._healthy

    def get_timestamp(self) -> datetime:
        ts = self._current_time
        self._current_time = self._current_time + self._step
        self._calls += 1
        return ts

    def statistics(self) -> Dict[str, Any]:
        return {
            "gps_status": "LOCKED" if self._locked else "DISCONNECTED",
            "satellites": 10,
            "latitude": 28.6139,
            "longitude": 77.2090,
            "altitude": 216.0,
            "messages_received": self._calls,
            "parse_errors": 0,
            "last_fix_time": self._current_time,
            "last_gps_timestamp": self._current_time,
            "gps_age_seconds": 0.0,
            "reconnect_count": 0,
            "healthy": self._healthy,
        }


class FakeMQTTClient:
    def __init__(self):
        self.connected = True
        self.last_health_packet = None
        self._sent = 0
        self._failed = 0

    def is_healthy(self) -> bool:
        return self.connected

    def statistics(self) -> Dict[str, Any]:
        return {
            "connected": self.connected,
            "messages_sent": self._sent,
            "messages_failed": self._failed,
        }

    def publish_health(self, packet: Dict[str, Any]) -> None:
        self.last_health_packet = packet
        self._sent += 1


def check(condition: bool, message: str) -> None:
    if not condition:
        raise IntegrationError(message)


def wait_for(condition: Callable[[], bool], timeout_seconds: float, poll_seconds: float = 0.05) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if condition():
            return True
        time.sleep(poll_seconds)
    return condition()


def count_sqlite_rows(database_path: Path, table_name: str) -> int:
    with sqlite3.connect(str(database_path)) as connection:
        cursor = connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row = cursor.fetchone()
        return int(row[0]) if row else 0


def make_envelope(length: int, sampling_rate: int, rise_seconds: float = 0.2) -> np.ndarray:
    if length <= 0:
        return np.array([], dtype=np.float64)

    rise = max(1, int(rise_seconds * sampling_rate))
    if 2 * rise >= length:
        return np.hanning(length).astype(np.float64)

    env = np.ones(length, dtype=np.float64)
    up = np.linspace(0.0, 1.0, rise, endpoint=False, dtype=np.float64)
    down = np.linspace(1.0, 0.0, rise, endpoint=False, dtype=np.float64)
    env[:rise] = up
    env[-rise:] = down
    return env


def add_burst(
    series: np.ndarray,
    start_index: int,
    end_index: int,
    sampling_rate: int,
    components: List[tuple[float, float, float]],
) -> None:
    segment_length = end_index - start_index
    if segment_length <= 0:
        return

    t = np.arange(segment_length, dtype=np.float64) / float(sampling_rate)
    env = make_envelope(segment_length, sampling_rate)
    burst = np.zeros(segment_length, dtype=np.float64)

    for frequency, amplitude, phase in components:
        burst += amplitude * np.sin((2.0 * np.pi * frequency * t) + phase)

    series[start_index:end_index] += burst * env


def build_scalar_series(
    kind: str,
    sampling_rate: int,
    pre_event_seconds: int = PRE_EVENT_SECONDS,
    burst_seconds: int = BURST_SECONDS,
    post_event_seconds: int = POST_EVENT_SECONDS,
    seed: int = 0,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    total_seconds = pre_event_seconds + burst_seconds + post_event_seconds
    total_samples = total_seconds * sampling_rate

    series = rng.normal(0.0, 0.004, total_samples).astype(np.float64)

    if kind == "noise":
        return series

    start = pre_event_seconds * sampling_rate
    end = (pre_event_seconds + burst_seconds) * sampling_rate

    if kind == "metro":
        add_burst(
            series,
            start,
            end,
            sampling_rate,
            [
                (30.0, 0.015, 0.0),
                (24.0, 0.010, 0.30),
            ],
        )
    elif kind == "construction":
        add_burst(
            series,
            start,
            end,
            sampling_rate,
            [
                (24.0, 0.030, 0.0),
                (18.0, 0.020, 0.40),
            ],
        )
    elif kind == "earthquake":
        add_burst(
            series,
            start,
            end,
            sampling_rate,
            [
                (4.0, 0.45, 0.0),
                (7.0, 0.20, 0.25),
            ],
        )
    else:
        raise ValueError(f"Unknown case kind: {kind}")

    return series


def build_xyz_samples(
    kind: str,
    sampling_rate: int,
    pre_event_seconds: int = PRE_EVENT_SECONDS,
    burst_seconds: int = BURST_SECONDS,
    post_event_seconds: int = POST_EVENT_SECONDS,
    seed: int = 0,
) -> List[Dict[str, float]]:
    rng = np.random.default_rng(seed)
    total_seconds = pre_event_seconds + burst_seconds + post_event_seconds
    total_samples = total_seconds * sampling_rate

    ax = rng.normal(0.0, 0.004, total_samples).astype(np.float64)
    ay = rng.normal(0.0, 0.004, total_samples).astype(np.float64)
    az = (9.81 + rng.normal(0.0, 0.004, total_samples)).astype(np.float64)

    if kind != "noise":
        start = pre_event_seconds * sampling_rate
        end = (pre_event_seconds + burst_seconds) * sampling_rate

        if kind == "metro":
            add_burst(
                ax,
                start,
                end,
                sampling_rate,
                [
                    (30.0, 0.015, 0.0),
                ],
            )
            add_burst(
                ay,
                start,
                end,
                sampling_rate,
                [
                    (28.0, 0.012, 0.30),
                ],
            )
            add_burst(
                az,
                start,
                end,
                sampling_rate,
                [
                    (30.0, 0.008, 0.60),
                ],
            )
        elif kind == "construction":
            add_burst(
                ax,
                start,
                end,
                sampling_rate,
                [
                    (24.0, 0.025, 0.0),
                ],
            )
            add_burst(
                ay,
                start,
                end,
                sampling_rate,
                [
                    (20.0, 0.020, 0.40),
                ],
            )
            add_burst(
                az,
                start,
                end,
                sampling_rate,
                [
                    (22.0, 0.015, 0.20),
                ],
            )
        elif kind == "earthquake":
            add_burst(
                ax,
                start,
                end,
                sampling_rate,
                [
                    (4.0, 0.15, 0.0),
                    (6.0, 0.05, 0.20),
                ],
            )
            add_burst(
                ay,
                start,
                end,
                sampling_rate,
                [
                    (4.0, 0.12, 0.40),
                ],
            )
            add_burst(
                az,
                start,
                end,
                sampling_rate,
                [
                    (4.0, 0.80, 0.10),
                    (7.0, 0.20, 0.60),
                ],
            )
        else:
            raise ValueError(f"Unknown case kind: {kind}")

    samples = []
    for i in range(total_samples):
        samples.append(
            {
                "ax": float(ax[i]),
                "ay": float(ay[i]),
                "az": float(az[i]),
            }
        )
    return samples


def make_timestamps(start_time: datetime, sample_count: int, sampling_rate: int) -> List[datetime]:
    return [
        start_time + timedelta(seconds=(i / float(sampling_rate)))
        for i in range(sample_count)
    ]


def make_json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: make_json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [make_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [make_json_safe(item) for item in value]
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    return value


def compact_event_record_for_packet(event_record: Dict[str, Any]) -> Dict[str, Any]:
    compact = copy.deepcopy(event_record)
    waveform = compact.get("waveform", [])
    compact["waveform"] = []
    for sample in waveform:
        if isinstance(sample, dict):
            timestamp = sample.get("timestamp")
            if hasattr(timestamp, "isoformat"):
                timestamp_value = timestamp.isoformat()
            else:
                timestamp_value = str(timestamp)
            compact["waveform"].append(
                {
                    "t": timestamp_value,
                    "v": float(sample.get("value", 0.0)),
                }
            )
    return compact


def build_test_detector(sampling_rate: int) -> EventDetector:
    config = get_config()

    detector = EventDetector(
        sampling_rate=sampling_rate,
        stalta_threshold=0.0005,
        pga_threshold=0.01,
        low_frequency=config.sensor.frequency_low,
        high_frequency=config.sensor.frequency_high,
        p_wave_trigger_ratio=4.0,
        minimum_confidence=0.40,
)

    detector.minimum_confidence = 0.40
    detector.stalta_detector = STALTADetector(
        sampling_rate=sampling_rate,
        sta_window_seconds=0.5,
        lta_window_seconds=5.0,
        trigger_on=0.0005,
        trigger_off=0.00025,
    )
    detector.pga_detector = PGADetector(
        sampling_rate=sampling_rate,
        pga_threshold=0.01,
        rolling_window_seconds=1.0,
    )
    detector.p_wave_detector = PWaveDetector(
        sampling_rate=sampling_rate,
        noise_window_seconds=5,
        signal_window_seconds=0.5,
        trigger_ratio=4.0,
        minimum_confidence=0.40,
        cooldown_seconds=2,
    )

    return detector


def smoke_test_packet_builder() -> None:
    print("\n[1/5] PacketBuilder smoke test")

    dummy_event_record = {
        "event_id": "EVT_TEST_001",
        "event_start_time": "2026-01-01T00:00:00+00:00",
        "event_end_time": "2026-01-01T00:00:05+00:00",
        "event_duration_seconds": 5.0,
        "peak_amplitude": 0.42,
        "metadata": {
            "station_id": STATION_ID,
            "confidence": 0.91,
            "pga": 0.42,
            "stalta_ratio": 4.8,
            "p_wave_time": "2026-01-01T00:00:01+00:00",
            "event_start_time": "2026-01-01T00:00:00+00:00",
        },
        "pre_event_samples": 10,
        "event_samples": 20,
        "post_event_samples": 10,
        "total_samples": 40,
        "waveform": [
            {"t": "2026-01-01T00:00:00+00:00", "v": 0.01},
            {"t": "2026-01-01T00:00:00.010000+00:00", "v": 0.02},
        ],
    }

    event_packet = PacketBuilder.build_event_packet(
        station_id=STATION_ID,
        event_record=dummy_event_record,
    )
    health_packet = PacketBuilder.build_health_packet(
        station_id=STATION_ID,
        cpu_usage=12.5,
        ram_usage=33.3,
        disk_usage=44.4,
        temperature=39.0,
        gps_status="LOCKED",
        network_status="CONNECTED",
        uptime_seconds=1234,
    )
    heartbeat_packet = PacketBuilder.build_heartbeat_packet(STATION_ID)
    error_packet = PacketBuilder.build_error_packet(
        station_id=STATION_ID,
        error_type="SIMULATED",
        error_message="PacketBuilder smoke test",
    )
    system_packet = PacketBuilder.build_system_packet(
        station_id=STATION_ID,
        message="System online",
        severity="INFO",
    )

    for packet_name, packet in [
        ("EVENT", event_packet),
        ("HEALTH", health_packet),
        ("HEARTBEAT", heartbeat_packet),
        ("ERROR", error_packet),
        ("SYSTEM", system_packet),
    ]:
        check(PacketBuilder.validate_packet(packet), f"{packet_name} packet failed validation")

    serialized = PacketBuilder.serialize(event_packet)
    round_trip = PacketBuilder.deserialize(serialized)
    check(round_trip["packet_type"] == PacketBuilder.EVENT_PACKET, "Event packet round-trip failed")
    check(round_trip["station_id"] == STATION_ID, "Event packet station_id lost during round-trip")
    check("payload" in round_trip, "Event packet payload missing after round-trip")

    print("  PacketBuilder: PASS")


def smoke_test_detectors() -> None:
    print("\n[2/5] Detector smoke tests")
    sampling_rate = TEST_SAMPLING_RATE

    for case in CASES:
        detector = build_test_detector(sampling_rate)
        scalar_series = build_scalar_series(
            case.kind,
            sampling_rate,
            seed=case.seed,
        )
        timestamps = make_timestamps(
            datetime.now(timezone.utc),
            len(scalar_series),
            sampling_rate,
        )

        for sample, timestamp in zip(scalar_series, timestamps):
            detector.process_sample(float(sample), timestamp)

        print(
            "DEBUG:",
            "stalta=", detector.stalta_detector.current_ratio(),
            "pga=", detector.pga_detector.current_pga(),
            "pwave_conf=", detector.p_wave_detector.last_confidence,
            "pwave_time=", detector.p_wave_detector.last_detection(),
        )

        result = detector.evaluate_waveform(
            waveform=scalar_series.tolist(),
            timestamp=timestamps[-1],
            station_id=STATION_ID,
        )

        print(
            f"  {case.name:12s} | confirmed={result.get('confirmed')} | "
            f"pga={result.get('pga', 0.0):.4f} | "
            f"stalta={result.get('stalta_ratio', 0.0):.4f} | "
            f"freq_like={result.get('frequency', {}).get('earthquake_like')}"
        )

        if case.expected_event:
            check(result.get("confirmed") is True, f"{case.name} should be confirmed")
            check(detector.event_counter == 1, f"{case.name} should increment event counter once")
            check(
                result.get("frequency", {}).get("earthquake_like") is True,
                f"{case.name} should be classified as earthquake-like by FFT",
            )
        else:
            check(result.get("confirmed") is False, f"{case.name} should not be confirmed")
            check(detector.event_counter == 0, f"{case.name} should not increment event counter")
            check(
                result.get("frequency", {}).get("earthquake_like") is False,
                f"{case.name} should not be earthquake-like by FFT",
            )

    print("  EventDetector / STALTA / PGA / PWave / FFT: PASS")
# -----------------------------------------------------------------------------------------------------------------------------------

# def print_event_record(event_record: Dict[str, Any]) -> None:
#     print("\n" + "=" * 120)
#     print("EVENT RECORD")
#     print("=" * 120)

#     print(f"Event ID              : {event_record.get('event_id')}")
#     print(f"Station ID            : {event_record.get('station_id')}")
#     print(f"Start Time            : {event_record.get('event_start_time')}")
#     print(f"End Time              : {event_record.get('event_end_time')}")
#     print(f"Duration              : {event_record.get('event_duration_seconds')} sec")
#     print(f"Peak Amplitude        : {event_record.get('peak_amplitude')}")

#     print("\nSTATISTICS")
#     print("-" * 120)

#     print(f"Pre Event Samples     : {event_record.get('pre_event_samples')}")
#     print(f"Event Samples         : {event_record.get('event_samples')}")
#     print(f"Post Event Samples    : {event_record.get('post_event_samples')}")
#     print(f"Total Samples         : {event_record.get('total_samples')}")

#     metadata = event_record.get("metadata", {})

#     print("\nMETADATA")
#     print("-" * 120)

#     for key, value in metadata.items():
#         print(f"{key:<30}: {value}")

#     waveform = event_record.get("waveform", [])

#     print("\nWAVEFORM")
#     print("-" * 120)
#     print(f"{'No':<8}{'Timestamp':<40}{'Value':>20}")
#     print("-" * 120)

#     for i, sample in enumerate(waveform, start=1):

#         timestamp = sample.get("timestamp")
#         value = sample.get("value", 0.0)

#         print(
#             f"{i:<8}"
#             f"{str(timestamp):<40}"
#             f"{value:>20.6f}"
#         )

#     print("-" * 120)
#     print(f"Displayed Samples : {len(waveform)}")
#     print("=" * 120)
# -----------------------------------------------------------------------------------------------------------------------------------

def run_station_pipeline_case(case: CaseDefinition) -> None:
    print(f"\n[3/5] Station pipeline case: {case.name}")

    sampling_rate = TEST_SAMPLING_RATE
    station_id = STATION_ID

    with tempfile.TemporaryDirectory(prefix=f"eeew_{case.kind}_") as temp_dir:
        case_root = Path(temp_dir)
        db_path = case_root / "local_events.db"
        waveform_dir = case_root / "waveforms"
        waveform_dir.mkdir(parents=True, exist_ok=True)

        local_db = LocalDatabase(str(db_path))
        db = local_db

        waveform_storage = WaveformStorage(str(waveform_dir))
        sample_queue: queue.Queue = queue.Queue(maxsize=50000)
        event_queue: queue.Queue = queue.Queue(maxsize=1000)

        gps_reader = FakeGPSReader(
            start_time=datetime.now(timezone.utc),
            step_seconds=1.0 / float(sampling_rate),
        )
        fake_mqtt = FakeMQTTClient()

        circular_buffer = CircularBuffer(max_samples=sampling_rate * 20)
        event_buffer = EventBuffer(
            pre_event_seconds=5,
            event_seconds=4,
            post_event_seconds=4,
            sampling_rate=sampling_rate,
        )
        event_detector = build_test_detector(sampling_rate)

        sensor_manager = SensorManager(
            station_id=station_id,
            sample_queue=sample_queue,
            event_queue=event_queue,
            gps_reader=gps_reader,
            circular_buffer=circular_buffer,
            event_buffer=event_buffer,
            waveform_storage=waveform_storage,
            event_detector=event_detector,
            sampling_rate=sampling_rate,
        )

        sensor_manager.required_post_event_samples = sampling_rate * 1
        sensor_manager.gravity_window = deque(maxlen=sampling_rate * 5)
        sensor_manager.waveform_window = deque(maxlen=sampling_rate * 8)

        sensor_manager.start()

        samples = build_xyz_samples(
            case.kind,
            sampling_rate,
            seed=case.seed,
        )

        fake_health_report = {
            "station_id": station_id,
            "cpu_usage": 11.0,
            "ram_usage": 22.0,
            "disk_usage": 33.0,
            "temperature": 44.0,
            "gps_status": "LOCKED",
            "network_status": "CONNECTED",
            "uptime_seconds": 55,
        }

        try:
            for sample in samples:
                sample_queue.put(sample)

            processed_ok = wait_for(
                lambda: sensor_manager.get_processed_samples() >= len(samples),
                timeout_seconds=15.0,
            )
            time.sleep(6)
            check(processed_ok, f"{case.name}: SensorManager did not process all samples in time")

            if case.expected_event:
                confirmed_ok = wait_for(
                lambda: sensor_manager.get_confirmed_events() >= 1,
                timeout_seconds=10.0,
                )
                print(
                    "AFTER WAIT:",
                    "confirmed=", sensor_manager.get_confirmed_events(),
                    "queue_empty=", event_queue.empty(),
                    "queue_size=", event_queue.qsize(),
                )
            
                check(confirmed_ok, f"{case.name}: confirmed event did not appear in time")
            else:
                time.sleep(0.75)

            check(
                sensor_manager.is_healthy(),
                f"{case.name}: SensorManager should be healthy during live processing",
            )

            check(
                gps_reader.is_healthy(),
                f"{case.name}: Fake GPS should be healthy",
            )

            diagnostics = Diagnostics(
                sensor_reader=sensor_manager,
                gps_reader=gps_reader,
                mqtt_client=fake_mqtt,
                local_database=local_db,
                waveform_storage=waveform_storage,
            )
            startup_report = diagnostics.startup_validation()
            print("\nSTARTUP REPORT")
            print(json.dumps(make_json_safe(startup_report), indent=2))
            check(
                startup_report["startup_passed"] is True,
                f"{case.name}: diagnostics startup validation failed",
            )

            if case.expected_event:
                check(
                    sensor_manager.get_confirmed_events() == 1,
                    f"{case.name}: exactly one confirmed event expected",
                )
                event_ready = wait_for(
                    lambda: not event_queue.empty(),
                    timeout_seconds=10.0,
                )

                check(
                    event_ready,
                    f"{case.name}: confirmed event did not get finalized into the event queue",
                )

                event_record = event_queue.get(timeout=2.0)
                print("\nEVENT RECORD KEYS")
                print(event_record.keys())

                check(
                    event_queue.empty(),
                    f"{case.name}: only one event should be generated for a single burst",
                )

# -----------------------------------------------------------------------------------------------------------------------------------
                print("\nEVENT RECORD FROM QUEUE")
                print(json.dumps(make_json_safe(event_record), indent=2))
# -----------------------------------------------------------------------------------------------------------------------------------

                # print_event_record(event_record)

                
                
                check(
                    event_record["station_id"] == station_id,
                    f"{case.name}: station id mismatch"
                )
                # check(
                #     len(event_record.get("waveform", [])) > 0,
                #     f"{case.name}: event waveform should not be empty",
                # )
                print("HAS WAVEFORM =", "waveform" in event_record)

                if "waveform" in event_record:
                    check(
                        len(event_record["waveform"]) > 0,
                        f"{case.name}: event waveform should not be empty",
                    )

                # if event_record["metadata"].get("event_id") != event_record.get("event_id"):
                #     print(
                #         "  [WARN] EventBuffer regenerates event_id during start_event(). "
                #         "The detector event_id and stored event_id differ."
                #     )
                print("\nEVENT BUFFER ACTIVE =", event_buffer.is_active())

                print("WAVEFORM STORAGE STATS")
                print(waveform_storage.statistics())

                print("WAVEFORM FILES")
                print(waveform_storage.list_waveforms())

                waveform_files_before = waveform_storage.list_waveforms()
                check(
                    len(waveform_files_before) >= 1,
                    f"{case.name}: waveform files should exist after event finalization",
                )

                loaded_json = waveform_storage.load_event_json(waveform_files_before[0])
                check(
                    loaded_json["event_id"] == event_record["event_id"],
                    f"{case.name}: stored waveform JSON event_id mismatch",
                )

                db.save_event(event_record)
                db.save_health_report(fake_health_report)
                db.write_system_log("INFO", f"{case.name} integration smoke test")

                check(
                    local_db.event_count() == 1,
                    f"{case.name}: LocalDatabase should contain exactly one event",
                )
                check(
                    count_sqlite_rows(db_path, "health_reports") >= 1,
                    f"{case.name}: health report should be stored in LocalDatabase",
                )
                check(
                    count_sqlite_rows(db_path, "system_logs") >= 1,
                    f"{case.name}: system log should be stored in LocalDatabase",
                )

                latest_event = local_db.latest_event()
                check(
                    latest_event is not None and latest_event["event_id"] == event_record["event_id"],
                    f"{case.name}: latest stored event mismatch",
                )

                compact_record = compact_event_record_for_packet(event_record)
                packet = PacketBuilder.build_event_packet(
                    station_id=station_id,
                    event_record=compact_record,
                )
                check(
                    PacketBuilder.validate_packet(packet),
                    f"{case.name}: event packet failed validation",
                )

                serialized_packet = PacketBuilder.serialize(packet)
                restored_packet = PacketBuilder.deserialize(serialized_packet)
                check(
                    restored_packet["packet_type"] == PacketBuilder.EVENT_PACKET,
                    f"{case.name}: restored packet type mismatch",
                )
                check(
                    restored_packet["station_id"] == station_id,
                    f"{case.name}: restored packet station_id mismatch",
                )

                db.save_outgoing_packet(
                    packet_id=packet["packet_id"],
                    packet_type=packet["packet_type"],
                    topic="earthquake/events",
                    payload=packet,
                )
                check(
                    local_db.pending_packet_count() == 1,
                    f"{case.name}: pending packet count should be 1 after save",
                )
                db.mark_packet_transmitted(packet["packet_id"])
                check(
                    local_db.pending_packet_count() == 0,
                    f"{case.name}: pending packet count should be 0 after mark transmitted",
                )

                packet_size = PacketBuilder.packet_size_bytes(packet)
                check(packet_size > 0, f"{case.name}: packet size should be positive")

            else:
                check(
                    sensor_manager.get_confirmed_events() == 0,
                    f"{case.name}: no events should be confirmed",
                )
                check(
                    event_queue.empty(),
                    f"{case.name}: event queue should remain empty",
                )
                db.save_health_report(fake_health_report)
                db.write_system_log("INFO", f"{case.name} integration smoke test")
                check(
                    local_db.event_count() == 0,
                    f"{case.name}: LocalDatabase should not contain any events",
                )
                check(
                    waveform_storage.statistics()["waveform_count"] == 0,
                    f"{case.name}: no waveform files should be saved",
                )
                check(
                    count_sqlite_rows(db_path, "health_reports") >= 1,
                    f"{case.name}: health report should still be stored",
                )
                check(
                    count_sqlite_rows(db_path, "system_logs") >= 1,
                    f"{case.name}: system log should still be stored",
                )

            diagnostics_after = Diagnostics(
                sensor_reader=sensor_manager,
                gps_reader=gps_reader,
                mqtt_client=fake_mqtt,
                local_database=local_db,
                waveform_storage=waveform_storage,
            )
            report = diagnostics_after.run_all_checks()
            check(report["sensor"]["healthy"], f"{case.name}: sensor diagnostics unhealthy")
            check(report["gps"]["healthy"], f"{case.name}: GPS diagnostics unhealthy")
            check(report["mqtt"]["healthy"], f"{case.name}: MQTT diagnostics unhealthy")
            check(report["database"]["healthy"], f"{case.name}: database diagnostics unhealthy")
            check(report["storage"]["healthy"], f"{case.name}: storage diagnostics unhealthy")

            if case.expected_event:
                check(
                    report["database"]["event_count"] == 1,
                    f"{case.name}: diagnostics should report one stored event",
                )
                check(
                    report["database"]["pending_packets"] == 0,
                    f"{case.name}: diagnostics should report zero pending packets",
                )
                check(
                    report["storage"]["statistics"]["waveform_count"] >= 1,
                    f"{case.name}: diagnostics should report stored waveform files",
                )
            else:
                check(
                    report["database"]["event_count"] == 0,
                    f"{case.name}: diagnostics should report zero stored events",
                )
                check(
                    report["database"]["pending_packets"] == 0,
                    f"{case.name}: diagnostics should report zero pending packets",
                )

            print(
                f"  {case.name:12s} | processed={sensor_manager.get_processed_samples()} | "
                f"confirmed={sensor_manager.get_confirmed_events()} | "
                f"rejected={sensor_manager.get_rejected_events()} | "
                f"healthy={sensor_manager.is_healthy()}"
            )

            print("LOCAL DB TYPE =", type(local_db))

            if hasattr(local_db, "close"):
                print("CLOSING DATABASE")
                local_db.close()
            else:
                print("NO CLOSE METHOD FOUND")

        finally:
            sensor_manager.stop()
            sensor_manager.join(timeout=5.0)

        # import gc
        # import os
        # import time

        gc.collect()
        time.sleep(1)

        print("TRYING MANUAL DELETE...")

        try:
            os.remove(db_path)
            print("MANUAL DELETE SUCCESS")
        except Exception as e:
            print("MANUAL DELETE FAILED:", e)

        check(
            not sensor_manager.is_alive(),
            f"{case.name}: SensorManager thread did not stop cleanly",
        )

        print(f"  {case.name}: PASS")

from pathlib import Path
import sys

log_dir = Path("test_logs")
log_dir.mkdir(exist_ok=True)

log_file = log_dir / "integration_test_output.txt"

sys.stdout = open(log_file, "w", encoding="utf-8")
sys.stderr = sys.stdout




def run_all_tests() -> None:
    config_path = PROJECT_ROOT / "config" / "config.yaml"
    check(config_path.exists(), f"Missing config file: {config_path}")

    initialize_config(str(config_path))
    config = get_config()

    print("Earthquake Warning System - Full SSN Test Harness")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Using config:  {config_path}")
    print(f"Station ID:    {config.station.station_id}")
    print(f"Test sampling rate: {TEST_SAMPLING_RATE} Hz")
    print(
        "Config sampling rate:",
        config.sensor.sampling_rate,
        "(test harness runs at a reduced rate for speed)",
    )

    smoke_test_packet_builder()
    smoke_test_detectors()

    for case in CASES:
        run_station_pipeline_case(case)

    print("\nAll tests passed.")


def main() -> int:
    try:
        run_all_tests()
        return 0
    except Exception as exc:
        print("\nTEST FAILED")
        print(f"{type(exc).__name__}: {exc}")
        traceback.print_exc()
        return 1

    finally:
     sys.stdout.close()


if __name__ == "__main__":
    raise SystemExit(main())