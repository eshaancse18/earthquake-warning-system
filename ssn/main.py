from __future__ import annotations

import os
import queue
import random
import signal
import sys
import threading
import time
from simulation.simulation_trigger import SimulationTrigger
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------
# Project bootstrap
# ---------------------------------------------------------------------


def find_project_root(start: Path) -> Path:
    for candidate in [start] + list(start.parents):
        if (candidate / "config" / "config.yaml").exists() and (
            candidate / "logging_system"
        ).exists():
            return candidate
    raise RuntimeError(
        "Could not locate project root. "
        "Run this script from inside the SSN project tree."
    )


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = find_project_root(SCRIPT_PATH.parent)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------
# Optional hardware imports
# ---------------------------------------------------------------------

ADXL355Reader = None
GPSReader = None

try:
    from acquisition.adxl355_reader import ADXL355Reader as _ADXL355Reader
    ADXL355Reader = _ADXL355Reader
except Exception:
    ADXL355Reader = None

try:
    from acquisition.gps_reader import GPSReader as _GPSReader
    GPSReader = _GPSReader
except Exception:
    GPSReader = None

# ---------------------------------------------------------------------
# Core project imports
# ---------------------------------------------------------------------

from acquisition.sensor_manager import SensorManager
from buffering.circular_buffer import CircularBuffer
from buffering.event_buffer import EventBuffer
from buffering.waveform_storage import WaveformStorage
from communication.mqtt_client import MQTTClient
from communication.packet_builder import PacketBuilder
from config.station_config import ConfigurationError, get_config, initialize_config
try:
    from health.health_monitor import HealthMonitor  # optional reference only
except Exception:
    HealthMonitor = None
from logging_system.logger import get_logger, initialize_logging
from processing.event_detector import EventDetector
from storage.local_database import LocalDatabase
from utils.time_utils import TimeUtils


# ---------------------------------------------------------------------
# Fallback devices for Windows / demo mode
# ---------------------------------------------------------------------

class NullGPSReader:
    def __init__(self) -> None:
        self._start = TimeUtils.utc_now()

    def start(self) -> None:
        return

    def stop(self) -> None:
        return

    def is_locked(self) -> bool:
        return True

    def is_healthy(self) -> bool:
        return True

    def get_timestamp(self) -> datetime:
        return TimeUtils.utc_now()

    def statistics(self) -> Dict[str, Any]:
        return {
            "gps_status": "LOCKED",
            "satellites": 0,
            "latitude": None,
            "longitude": None,
            "altitude": None,
            "messages_received": 0,
            "parse_errors": 0,
            "last_fix_time": self._start,
            "last_gps_timestamp": TimeUtils.utc_now(),
            "gps_age_seconds": 0.0,
            "reconnect_count": 0,
            "healthy": True,
        }


class SimulatedSensorReader(threading.Thread):
    """
    Generates ADXL355-like samples when the real sensor is unavailable.
    The sample format matches SensorManager expectations:
        {"ax": float, "ay": float, "az": float, "magnitude": float}
    """

    def __init__(
        self,
        sample_queue: queue.Queue,
        sampling_rate: int,
        event_after_seconds: float = 25.0,
        burst_duration_seconds: float = 10.0,
    ) -> None:
        super().__init__(name="SIMULATED_ADC_READER_THREAD", daemon=True)
        self.sample_queue = sample_queue
        self.sampling_rate = sampling_rate
        self.sample_interval = 1.0 / sampling_rate
        self.event_after_seconds = event_after_seconds
        self.burst_duration_seconds = burst_duration_seconds
        self.stop_event = threading.Event()
        self.samples_read = 0
        self.read_errors = 0
        self.last_sample_monotonic = time.monotonic()
        self.started_at = time.monotonic()

    def stop(self) -> None:
        self.stop_event.set()

    def is_healthy(self) -> bool:
        if self.read_errors > 100:
            return False
        return (time.monotonic() - self.last_sample_monotonic) <= 5.0

    def statistics(self) -> Dict[str, Any]:
        return {
            "samples_read": self.samples_read,
            "read_errors": self.read_errors,
            "sampling_rate": self.sampling_rate,
            "last_sample_age_seconds": time.monotonic() - self.last_sample_monotonic,
            "mode": "simulated",
        }

    def _make_sample(self, now_s: float) -> Dict[str, float]:
        # Baseline around Earth's gravity with tiny noise.
        ax = random.uniform(-0.02, 0.02)
        ay = random.uniform(-0.02, 0.02)
        az = 9.81 + random.uniform(-0.02, 0.02)

        elapsed = time.monotonic() - self.started_at
        in_burst = self.event_after_seconds <= elapsed <= (
            self.event_after_seconds + self.burst_duration_seconds
        )

        if in_burst:
            # Seismic burst: stronger deviation + oscillation.
            burst = 2.8 + 1.2 * random.random()
            ax += burst * random.choice([-1.0, 1.0]) * (0.4 + random.random())
            ay += burst * random.choice([-1.0, 1.0]) * (0.3 + random.random())
            az += burst * (0.8 + random.random())

        magnitude = (ax * ax + ay * ay + az * az) ** 0.5
        return {"ax": ax, "ay": ay, "az": az, "magnitude": magnitude}

    def run(self) -> None:
        next_sample_time = time.perf_counter()
        while not self.stop_event.is_set():
            try:
                sample = self._make_sample(time.monotonic())
                self.sample_queue.put(sample, timeout=1)
                self.samples_read += 1
                self.last_sample_monotonic = time.monotonic()
            except queue.Full:
                self.read_errors += 1
            except Exception:
                self.read_errors += 1
            next_sample_time += self.sample_interval
            sleep_time = next_sample_time - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                next_sample_time = time.perf_counter()


# ---------------------------------------------------------------------
# Runtime services
# ---------------------------------------------------------------------

class EventForwarder(threading.Thread):
    """
    Pulls confirmed event records from SensorManager and pushes them to:
    - local SQLite database
    - MQTT broker via MQTTClient
    """

    def __init__(
        self,
        event_queue: queue.Queue,
        mqtt_client: MQTTClient,
        database: LocalDatabase,
        logger_name: str = "EventForwarder",
    ) -> None:
        super().__init__(name="EVENT_FORWARDER_THREAD", daemon=True)
        self.event_queue = event_queue
        self.mqtt_client = mqtt_client
        self.database = database
        self.stop_event = threading.Event()
        self.logger = get_logger(logger_name)
        self.events_forwarded = 0
        self.events_failed = 0

    def stop(self) -> None:
        self.stop_event.set()

    def run(self) -> None:
        self.logger.info("Event forwarder started.")
        while not self.stop_event.is_set():
            try:
                record = self.event_queue.get(timeout=1)
            except queue.Empty:
                continue

            try:
                self.database.save_event(record)
            except Exception as exc:
                self.logger.exception(f"Failed to save event locally: {exc}")

            try:
                ok = self.mqtt_client.publish_event(record)
                if ok:
                    self.events_forwarded += 1
                    self.logger.info(
                        f"Forwarded event {record.get('event_id')} to MQTT."
                    )
                else:
                    self.events_failed += 1
                    self.logger.warning(
                        f"MQTT queue rejected event {record.get('event_id')}."
                    )
            except Exception as exc:
                self.events_failed += 1
                self.logger.exception(f"Failed to publish event: {exc}")

        self.logger.info("Event forwarder stopped.")

    def statistics(self) -> Dict[str, Any]:
        return {
            "events_forwarded": self.events_forwarded,
            "events_failed": self.events_failed,
            "queue_depth": self.event_queue.qsize(),
        }


class RuntimeHealthMonitor(threading.Thread):
    """
    Cross-platform health reporter for the demo/laptop setup.
    Saves health snapshots to SQLite and publishes them to MQTT.
    """

    def __init__(
        self,
        station_id: str,
        mqtt_client: MQTTClient,
        gps_reader: Any,
        sensor_reader: Any,
        database: LocalDatabase,
        report_interval_seconds: int,
    ) -> None:
        super().__init__(name="HEALTH_THREAD", daemon=True)
        self.station_id = station_id
        self.mqtt_client = mqtt_client
        self.gps_reader = gps_reader
        self.sensor_reader = sensor_reader
        self.database = database
        self.report_interval_seconds = report_interval_seconds
        self.stop_event = threading.Event()
        self.logger = get_logger("RuntimeHealthMonitor")
        self.start_time = time.time()
        self.reports_sent = 0
        self._psutil = None
        try:
            import psutil  # type: ignore
            self._psutil = psutil
        except Exception:
            self._psutil = None

    def stop(self) -> None:
        self.stop_event.set()

    def _cpu_usage(self) -> float:
        if self._psutil is None:
            return 0.0
        try:
            return float(self._psutil.cpu_percent(interval=None))
        except Exception:
            return 0.0

    def _ram_usage(self) -> float:
        if self._psutil is None:
            return 0.0
        try:
            return float(self._psutil.virtual_memory().percent)
        except Exception:
            return 0.0

    def _disk_usage(self) -> float:
        if self._psutil is None:
            return 0.0
        try:
            root = os.environ.get("SystemDrive", "C:")
            return float(self._psutil.disk_usage(root + "\\").percent)
        except Exception:
            try:
                return float(self._psutil.disk_usage(str(Path.home().anchor or "/")).percent)
            except Exception:
                return 0.0

    def _temperature(self) -> float:
        return 0.0

    def _gps_status(self) -> str:
        try:
            if self.gps_reader is None:
                return "UNAVAILABLE"
            return "LOCKED" if self.gps_reader.is_locked() else "SEARCHING"
        except Exception:
            return "ERROR"

    def _network_status(self) -> str:
        return "CONNECTED" if self.mqtt_client.is_connected() else "DISCONNECTED"

    def _sensor_status(self) -> str:
        try:
            return "HEALTHY" if self.sensor_reader.is_healthy() else "FAULT"
        except Exception:
            return "ERROR"

    def _build_report(self) -> Dict[str, Any]:
        return {
            "station_id": self.station_id,
            "cpu_usage": self._cpu_usage(),
            "ram_usage": self._ram_usage(),
            "disk_usage": self._disk_usage(),
            "temperature": self._temperature(),
            "gps_status": self._gps_status(),
            "network_status": self._network_status(),
            "sensor_status": self._sensor_status(),
            "uptime_seconds": int(time.time() - self.start_time),
            "thread_count": threading.active_count(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def run(self) -> None:
        self.logger.info("Runtime health monitor started.")
        while not self.stop_event.is_set():
            try:
                report = self._build_report()
                self.database.save_health_report(report)
                packet = PacketBuilder.build_health_packet(
                    station_id=self.station_id,
                    cpu_usage=report["cpu_usage"],
                    ram_usage=report["ram_usage"],
                    disk_usage=report["disk_usage"],
                    temperature=report["temperature"],
                    gps_status=report["gps_status"],
                    network_status=report["network_status"],
                    uptime_seconds=report["uptime_seconds"],
                )
                self.mqtt_client.publish_health(packet)
                self.reports_sent += 1
                self.logger.info(
                    "HEALTH_REPORT | "
                    f"cpu={report['cpu_usage']:.1f} | "
                    f"ram={report['ram_usage']:.1f} | "
                    f"disk={report['disk_usage']:.1f} | "
                    f"gps={report['gps_status']} | "
                    f"mqtt={report['network_status']} | "
                    f"sensor={report['sensor_status']}"
                )
            except Exception as exc:
                self.logger.exception(f"Health monitor failed: {exc}")

            self.stop_event.wait(self.report_interval_seconds)

        self.logger.info("Runtime health monitor stopped.")

    def statistics(self) -> Dict[str, Any]:
        return {
            "reports_sent": self.reports_sent,
            "uptime_seconds": int(time.time() - self.start_time),
            "report_interval": self.report_interval_seconds,
        }


# ---------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------

def build_gps_reader(config, logger):
    if os.getenv("SSN_FORCE_SIMULATION", "0") == "1":
        logger.warning("Simulation mode forced by SSN_FORCE_SIMULATION=1.")
        return NullGPSReader()

    if GPSReader is None:
        logger.warning("GPSReader import unavailable; using NullGPSReader.")
        return NullGPSReader()

    try:
        gps = GPSReader(
            serial_port=config.gps.serial_port,
            baud_rate=config.gps.baud_rate,
        )
        logger.info(
            f"Real GPS reader initialized on {config.gps.serial_port}."
        )
        return gps
    except Exception as exc:
        logger.warning(f"GPS hardware unavailable; using NullGPSReader ({exc}).")
        return NullGPSReader()


def build_sensor_reader(sample_queue, sampling_rate: int, logger):
    if os.getenv("SSN_FORCE_SIMULATION", "0") == "1":
        logger.warning("Simulation mode forced by SSN_FORCE_SIMULATION=1.")
        return SimulatedSensorReader(
            sample_queue=sample_queue,
            sampling_rate=sampling_rate,
        )

    if ADXL355Reader is None:
        logger.warning("ADXL355Reader import unavailable; using simulator.")
        return SimulatedSensorReader(
            sample_queue=sample_queue,
            sampling_rate=sampling_rate,
        )

    try:
        reader = ADXL355Reader(
            sample_queue=sample_queue,
            sampling_rate=sampling_rate,
            spi_bus=int(os.getenv("SSN_SPI_BUS", "0")),
            spi_device=int(os.getenv("SSN_SPI_DEVICE", "0")),
        )
        logger.info("Real ADXL355 sensor reader initialized.")
        return reader
    except Exception as exc:
        logger.warning(f"Sensor hardware unavailable; using simulator ({exc}).")
        return SimulatedSensorReader(
            sample_queue=sample_queue,
            sampling_rate=sampling_rate,
        )


def resolve_mqtt_broker(config) -> str:
    env_broker = os.getenv("MQTT_BROKER_IP")
    if env_broker:
        return env_broker

    # The checked-in config points to a LAN address; for local development
    # default to localhost unless the user explicitly overrides it.
    return "localhost"


def stop_component(component: Any) -> None:
    if component is None:
        return
    try:
        if hasattr(component, "stop"):
            component.stop()
    except Exception:
        pass


# ---------------------------------------------------------------------
# Main boot sequence
# ---------------------------------------------------------------------

def main() -> int:
    config_path = PROJECT_ROOT / "config" / "config.yaml"

    try:
        initialize_config(str(config_path))
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}")
        return 1

    initialize_logging()
    logger = get_logger("SSN_MAIN")

    config = get_config()

    logger.info("=" * 60)
    logger.info("SSN STARTING...")
    logger.info("=" * 60)
    logger.info(f"Station ID: {config.station.station_id}")
    logger.info(
        "Configured MQTT broker in YAML: "
        f"{config.mqtt.broker_ip}:{config.mqtt.broker_port}"
    )

    broker_ip = resolve_mqtt_broker(config)
    if broker_ip != config.mqtt.broker_ip:
        logger.warning(
            f"Using MQTT broker override: {broker_ip}:{config.mqtt.broker_port}"
        )

    database = LocalDatabase(config.storage.database_path)
    waveform_storage = WaveformStorage(config.storage.waveform_directory)

    sample_queue: queue.Queue = queue.Queue(maxsize=max(1000, config.sensor.sampling_rate * 10))
    event_queue: queue.Queue = queue.Queue(maxsize=100)

    circular_buffer = CircularBuffer(
        max_samples=int(config.sensor.sampling_rate * max(5, config.buffer.pre_event_seconds))
    )

    event_buffer = EventBuffer(
        pre_event_seconds=config.buffer.pre_event_seconds,
        event_seconds=config.buffer.event_seconds,
        post_event_seconds=config.buffer.post_event_seconds,
        sampling_rate=config.sensor.sampling_rate,
    )

    event_detector = EventDetector(
        sampling_rate=config.sensor.sampling_rate,
        stalta_threshold=config.sensor.stalta_threshold,
        pga_threshold=config.sensor.threshold_pga,
        low_frequency=config.sensor.frequency_low,
        high_frequency=config.sensor.frequency_high,
    )

    gps_reader = build_gps_reader(config, logger)
    sensor_reader = build_sensor_reader(sample_queue, config.sensor.sampling_rate, logger)

    mqtt_client = MQTTClient(
        broker_ip=broker_ip,
        broker_port=config.mqtt.broker_port,
        keepalive=config.mqtt.keepalive,
        qos=config.mqtt.qos,
        event_topic=config.mqtt.event_topic,
        health_topic=config.mqtt.health_topic,
        station_id=config.station.station_id,
        local_database=database,
    )

    sensor_manager = SensorManager(
        station_id=config.station.station_id,
        sample_queue=sample_queue,
        event_queue=event_queue,
        gps_reader=gps_reader,
        circular_buffer=circular_buffer,
        event_buffer=event_buffer,
        waveform_storage=waveform_storage,
        event_detector=event_detector,
        sampling_rate=config.sensor.sampling_rate,
    )

    event_forwarder = EventForwarder(
        event_queue=event_queue,
        mqtt_client=mqtt_client,
        database=database,
    )


# SIMULATION TRIGGER
    simulation_trigger = SimulationTrigger(
    station_id=config.station.station_id,
    event_queue=event_queue,
)

    health_monitor = RuntimeHealthMonitor(
        station_id=config.station.station_id,
        mqtt_client=mqtt_client,
        gps_reader=gps_reader,
        sensor_reader=sensor_reader,
        database=database,
        report_interval_seconds=config.health.report_interval_seconds,
    )

    threads = [
        mqtt_client,
        sensor_manager,
        event_forwarder,
        health_monitor,
        # COMMENT BELOW BEFORE RUNNING ACTUAL
        simulation_trigger,
    ]

    # Start connection / producers first.
    try:
        if hasattr(gps_reader, "start"):
            gps_reader.start()
    except Exception as exc:
        logger.warning(f"GPS thread could not be started: {exc}")

    try:
        if hasattr(sensor_reader, "start"):
            sensor_reader.start()
    except Exception as exc:
        logger.warning(f"Sensor reader could not be started: {exc}")

    for thread in threads:
        thread.start()

    logger.info("SSN is running.")
    logger.info(f"MQTT topic (events): {config.mqtt.event_topic}")
    logger.info(f"MQTT topic (health): {config.mqtt.health_topic}")
    logger.info("Press Ctrl+C to stop.")

    stop_requested = threading.Event()

    def _handle_signal(signum, frame):
        stop_requested.set()

    try:
        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)
    except Exception:
        pass

    try:
        while not stop_requested.is_set():
            time.sleep(1)

    except KeyboardInterrupt:
        stop_requested.set()

    logger.info("Shutdown requested, stopping threads...")

    stop_component(health_monitor)
    stop_component(event_forwarder)
    stop_component(sensor_manager)
    stop_component(mqtt_client)

    # COMMENT BELOW LINE
    stop_component(simulation_trigger)
    stop_component(sensor_reader)
    stop_component(gps_reader)

    for thread in threads:
        try:
            thread.join(timeout=5)
        except Exception:
            pass

    # Some readers may be plain objects, not threads.
    try:
        if hasattr(sensor_reader, "join"):
            sensor_reader.join(timeout=5)
    except Exception:
        pass

    try:
        if hasattr(gps_reader, "join"):
            gps_reader.join(timeout=5)
    except Exception:
        pass

    logger.info("SSN stopped cleanly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
