import math
import queue
import threading
import time
from typing import Any, Dict

from smbus2 import SMBus

from logging_system.logger import SensorLogger
from utils.constants import THREAD_ADC_READER


class ADXL345Reader(threading.Thread):
    """
    ADXL345 I2C Reader

    Responsibilities
    ----------------
    1. Initialize and verify ADXL345 hardware
    2. Read X, Y and Z acceleration
    3. Convert raw acceleration to m/s^2
    4. Compute vector magnitude
    5. Push samples into the processing queue

    Notes
    -----
    GPS timestamps are NOT generated here.

    SensorManager is responsible for attaching
    synchronized GPS timestamps and removing gravity.
    """

    REG_DEVID = 0x00
    REG_BW_RATE = 0x2C
    REG_POWER_CTL = 0x2D
    REG_DATA_FORMAT = 0x31
    REG_DATAX0 = 0x32

    EXPECTED_DEVICE_ID = 0xE5

    MEASUREMENT_MODE = 0x08
    FULL_RESOLUTION = 0x08
    OUTPUT_DATA_RATE_200HZ = 0x0B

    GRAVITY = 9.80665
    SCALE_FACTOR_G = 0.0039

    def __init__(
        self,
        sample_queue: queue.Queue,
        sampling_rate: int,
        i2c_bus: int = 1,
        i2c_address: int = 0x53,
    ):
        super().__init__(
            name=THREAD_ADC_READER,
            daemon=True,
        )

        if sampling_rate <= 0:
            raise ValueError(
                "sampling_rate must be > 0"
            )

        self.sample_queue = sample_queue
        self.sampling_rate = sampling_rate
        self.sample_interval = 1.0 / sampling_rate

        self.i2c_bus = i2c_bus
        self.i2c_address = i2c_address

        self.logger = SensorLogger()

        self.stop_event = threading.Event()

        self.bus = None

        self.samples_read = 0
        self.read_errors = 0

        self.last_sample_monotonic = time.monotonic()

        self._initialize_sensor()

    def _initialize_sensor(self) -> None:
        self.bus = SMBus(
            self.i2c_bus
        )

        device_id = self.bus.read_byte_data(
            self.i2c_address,
            self.REG_DEVID,
        )

        if device_id != self.EXPECTED_DEVICE_ID:
            raise RuntimeError(
                (
                    "ADXL345 Device ID mismatch. "
                    f"Expected={hex(self.EXPECTED_DEVICE_ID)} "
                    f"Received={hex(device_id)}"
                )
            )

        self.bus.write_byte_data(
            self.i2c_address,
            self.REG_DATA_FORMAT,
            self.FULL_RESOLUTION,
        )
        self.bus.write_byte_data(
            self.i2c_address,
            self.REG_BW_RATE,
            self.OUTPUT_DATA_RATE_200HZ,
        )

        self.bus.write_byte_data(
            self.i2c_address,
            self.REG_POWER_CTL,
            self.MEASUREMENT_MODE,
        )

        self.logger.acquisition_started()

    def _convert_signed_16bit(
        self,
        low_byte: int,
        high_byte: int,
    ) -> int:
        value = (
            low_byte |
            (high_byte << 8)
        )

        if value & 0x8000:
            value -= 1 << 16

        return value

    def _raw_to_ms2(
        self,
        raw_value: int,
    ) -> float:
        acceleration_g = (
            raw_value *
            self.SCALE_FACTOR_G
        )

        return (
            acceleration_g *
            self.GRAVITY
        )

    def _calculate_magnitude(
        self,
        ax: float,
        ay: float,
        az: float,
    ) -> float:
        return math.sqrt(
            ax * ax +
            ay * ay +
            az * az
        )

    def read_sample(
        self,
    ) -> Dict[str, Any]:
        data = self.bus.read_i2c_block_data(
            self.i2c_address,
            self.REG_DATAX0,
            6,
        )

        x_raw = self._convert_signed_16bit(
            data[0],
            data[1],
        )

        y_raw = self._convert_signed_16bit(
            data[2],
            data[3],
        )

        z_raw = self._convert_signed_16bit(
            data[4],
            data[5],
        )

        ax = self._raw_to_ms2(x_raw)
        ay = self._raw_to_ms2(y_raw)
        az = self._raw_to_ms2(z_raw)

        magnitude = self._calculate_magnitude(
            ax,
            ay,
            az,
        )

        self.samples_read += 1

        self.last_sample_monotonic = (
            time.monotonic()
        )

        return {
            "ax": ax,
            "ay": ay,
            "az": az,
            "magnitude": magnitude,
        }

    def run(self) -> None:
        next_sample_time = time.perf_counter()

        while not self.stop_event.is_set():
            try:
                sample = self.read_sample()

                self.sample_queue.put(
                    sample,
                    timeout=1,
                )

            except queue.Full:
                if self.stop_event.is_set():
                    break

                self.read_errors += 1

                self.logger.sensor_error(
                    "Sample queue full"
                )

            except Exception as error:
                self.read_errors += 1

                self.logger.sensor_error(
                    f"Sensor read error: {error}"
                )

                time.sleep(1)

            next_sample_time += self.sample_interval

            sleep_time = (
                next_sample_time -
                time.perf_counter()
            )

            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                next_sample_time = (
                    time.perf_counter()
                )

        self._cleanup()

        self.logger.acquisition_stopped()

    def stop(self) -> None:
        self.stop_event.set()

    def _cleanup(self) -> None:
        try:
            if self.bus is not None:
                self.bus.close()
        except Exception:
            pass

    def reconnect(self) -> bool:
        try:
            self._cleanup()

            self._initialize_sensor()

            return True

        except Exception as error:
            self.logger.sensor_error(
                f"Reconnect failed: {error}"
            )

            return False

    def is_healthy(self) -> bool:
        if self.read_errors > 100:
            return False

        age = (
            time.monotonic() -
            self.last_sample_monotonic
        )

        if age > 5:
            return False

        return True

    def statistics(
        self,
    ) -> Dict[str, Any]:
        return {
            "samples_read": self.samples_read,
            "read_errors": self.read_errors,
            "sampling_rate": self.sampling_rate,
            "i2c_bus": self.i2c_bus,
            "i2c_address": hex(self.i2c_address),
            "last_sample_age_seconds": (
                time.monotonic() -
                self.last_sample_monotonic
            ),
        }