import os
import yaml
from dataclasses import dataclass
from typing import Any


class ConfigurationError(Exception):
    pass


@dataclass(frozen=True)
class StationConfig:
    station_id: str
    station_name: str
    latitude: float
    longitude: float
    elevation: float


@dataclass(frozen=True)
class SensorConfig:
    sampling_rate: int
    adc_gain: int
    adc_channel: int
    threshold_pga: float
    stalta_threshold: float
    frequency_low: float
    frequency_high: float


@dataclass(frozen=True)
class BufferConfig:
    pre_event_seconds: int
    event_seconds: int
    post_event_seconds: int


@dataclass(frozen=True)
class GPSConfig:
    enabled: bool
    serial_port: str
    baud_rate: int


@dataclass(frozen=True)
class MQTTConfig:
    broker_ip: str
    broker_port: int
    keepalive: int
    qos: int
    event_topic: str
    health_topic: str


@dataclass(frozen=True)
class HealthConfig:
    report_interval_seconds: int


@dataclass(frozen=True)
class StorageConfig:
    database_path: str
    waveform_directory: str


@dataclass(frozen=True)
class LoggingConfig:
    log_level: str
    log_file: str


@dataclass(frozen=True)
class SystemConfig:
    max_retry_count: int
    retry_delay_seconds: int
    watchdog_timeout_seconds: int


class ConfigManager:

    def __init__(self, config_path: str):
        self.config_path = config_path

        self.station: StationConfig
        self.sensor: SensorConfig
        self.buffer: BufferConfig
        self.gps: GPSConfig
        self.mqtt: MQTTConfig
        self.health: HealthConfig
        self.storage: StorageConfig
        self.logging: LoggingConfig
        self.system: SystemConfig

        self._load()

    def _load(self) -> None:

        if not os.path.exists(self.config_path):
            raise ConfigurationError(
                f"Configuration file not found: {self.config_path}"
            )

        try:
            with open(self.config_path, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file)
        except yaml.YAMLError as error:
            raise ConfigurationError(
                f"Invalid YAML configuration: {error}"
            ) from error
        except Exception as error:
            raise ConfigurationError(
                f"Failed to load configuration: {error}"
            ) from error

        if not isinstance(config, dict):
            raise ConfigurationError(
                "Configuration root must be a dictionary"
            )

        self.station = self._load_station(config)
        self.sensor = self._load_sensor(config)
        self.buffer = self._load_buffer(config)
        self.gps = self._load_gps(config)
        self.mqtt = self._load_mqtt(config)
        self.health = self._load_health(config)
        self.storage = self._load_storage(config)
        self.logging = self._load_logging(config)
        self.system = self._load_system(config)

    @staticmethod
    def _require(section: dict, key: str) -> Any:

        if key not in section:
            raise ConfigurationError(
                f"Missing configuration key: {key}"
            )

        return section[key]

    def _load_station(self, config: dict) -> StationConfig:

        station = self._require(config, "station")

        return StationConfig(
            station_id=str(self._require(station, "station_id")),
            station_name=str(self._require(station, "station_name")),
            latitude=float(self._require(station, "latitude")),
            longitude=float(self._require(station, "longitude")),
            elevation=float(self._require(station, "elevation"))
        )

    def _load_sensor(self, config: dict) -> SensorConfig:

        sensor = self._require(config, "sensor")

        sampling_rate = int(self._require(sensor, "sampling_rate"))

        if sampling_rate <= 0:
            raise ConfigurationError(
                "sampling_rate must be greater than zero"
            )

        return SensorConfig(
            sampling_rate=sampling_rate,
            adc_gain=int(self._require(sensor, "adc_gain")),
            adc_channel=int(self._require(sensor, "adc_channel")),
            threshold_pga=float(
                self._require(sensor, "threshold_pga")
            ),
            stalta_threshold=float(
                self._require(sensor, "stalta_threshold")
            ),
            frequency_low=float(
                self._require(sensor, "frequency_low")
            ),
            frequency_high=float(
                self._require(sensor, "frequency_high")
            )
        )

    def _load_buffer(self, config: dict) -> BufferConfig:

        buffer_cfg = self._require(config, "buffer")

        return BufferConfig(
            pre_event_seconds=int(
                self._require(buffer_cfg, "pre_event_seconds")
            ),
            event_seconds=int(
                self._require(buffer_cfg, "event_seconds")
            ),
            post_event_seconds=int(
                self._require(buffer_cfg, "post_event_seconds")
            )
        )

    def _load_gps(self, config: dict) -> GPSConfig:

        gps = self._require(config, "gps")

        return GPSConfig(
            enabled=bool(self._require(gps, "enabled")),
            serial_port=str(self._require(gps, "serial_port")),
            baud_rate=int(self._require(gps, "baud_rate"))
        )

    def _load_mqtt(self, config: dict) -> MQTTConfig:

        mqtt = self._require(config, "mqtt")

        broker_port = int(self._require(mqtt, "broker_port"))

        if broker_port < 1 or broker_port > 65535:
            raise ConfigurationError(
                "Invalid MQTT port"
            )

        qos = int(self._require(mqtt, "qos"))

        if qos not in [0, 1, 2]:
            raise ConfigurationError(
                "MQTT QoS must be 0, 1 or 2"
            )

        return MQTTConfig(
            broker_ip=str(self._require(mqtt, "broker_ip")),
            broker_port=broker_port,
            keepalive=int(self._require(mqtt, "keepalive")),
            qos=qos,
            event_topic=str(self._require(mqtt, "event_topic")),
            health_topic=str(self._require(mqtt, "health_topic"))
        )

    def _load_health(self, config: dict) -> HealthConfig:

        health = self._require(config, "health")

        return HealthConfig(
            report_interval_seconds=int(
                self._require(
                    health,
                    "report_interval_seconds"
                )
            )
        )

    def _load_storage(self, config: dict) -> StorageConfig:

        storage = self._require(config, "storage")

        waveform_directory = str(
            self._require(storage, "waveform_directory")
        )

        os.makedirs(waveform_directory, exist_ok=True)

        database_path = str(
            self._require(storage, "database_path")
        )

        return StorageConfig(
            database_path=database_path,
            waveform_directory=waveform_directory
        )

    def _load_logging(self, config: dict) -> LoggingConfig:

        logging_cfg = self._require(config, "logging")

        log_file = str(
            self._require(logging_cfg, "log_file")
        )

        log_directory = os.path.dirname(log_file)

        if log_directory:
            os.makedirs(log_directory, exist_ok=True)

        return LoggingConfig(
            log_level=str(
                self._require(logging_cfg, "log_level")
            ),
            log_file=log_file
        )

    def _load_system(self, config: dict) -> SystemConfig:

        system = self._require(config, "system")

        return SystemConfig(
            max_retry_count=int(
                self._require(system, "max_retry_count")
            ),
            retry_delay_seconds=int(
                self._require(system, "retry_delay_seconds")
            ),
            watchdog_timeout_seconds=int(
                self._require(
                    system,
                    "watchdog_timeout_seconds"
                )
            )
        )


_config_instance = None


def initialize_config(config_path: str) -> ConfigManager:

    global _config_instance

    _config_instance = ConfigManager(config_path)

    return _config_instance


def get_config() -> ConfigManager:

    if _config_instance is None:
        raise ConfigurationError(
            "Configuration not initialized"
        )

    return _config_instance