import math
import queue
import threading
import time
from typing import Dict
from typing import Any

import spidev

from logging_system.logger import SensorLogger
from utils.constants import THREAD_ADC_READER


class ADXL355Reader(threading.Thread):

    """
    ADXL355 SPI Reader

    Responsibilities
    ----------------
    1. Read X-axis acceleration
    2. Read Y-axis acceleration
    3. Read Z-axis acceleration
    4. Compute vector magnitude
    5. Push samples into processing queue

    Notes
    -----
    GPS timestamps are NOT generated here.

    SensorManager is responsible for
    attaching synchronized GPS timestamps.
    """

    # ADXL355 Registers

    REG_DEVID_AD = 0x00

    REG_XDATA3 = 0x08
    REG_YDATA3 = 0x0B
    REG_ZDATA3 = 0x0E

    REG_RANGE = 0x2C
    REG_POWER_CTL = 0x2D

    EXPECTED_DEVICE_ID = 0xAD

    RANGE_2G = 0x01

    MEASUREMENT_MODE = 0x00

    SCALE_FACTOR_2G = 0.0000039 * 9.80665

    def __init__(
        self,
        sample_queue: queue.Queue,
        sampling_rate: int,
        spi_bus: int = 0,
        spi_device: int = 0
    ):

        super().__init__(
            name=THREAD_ADC_READER,
            daemon=True
        )

        if sampling_rate <= 0:

            raise ValueError(
                "sampling_rate must be > 0"
            )

        self.sample_queue = sample_queue

        self.sampling_rate = sampling_rate

        self.sample_interval = (
            1.0 / sampling_rate
        )

        self.spi_bus = spi_bus

        self.spi_device = spi_device

        self.logger = SensorLogger()

        self.stop_event = threading.Event()

        self.spi = None

        self.samples_read = 0

        self.read_errors = 0

        self.last_sample_monotonic = (
            time.monotonic()
        )

        self._initialize_sensor()

    def _initialize_sensor(self) -> None:

        self.spi = spidev.SpiDev()

        self.spi.open(
            self.spi_bus,
            self.spi_device
        )

        self.spi.max_speed_hz = 5000000

        self.spi.mode = 0

        device_id = self._read_register(
            self.REG_DEVID_AD
        )

        if device_id != self.EXPECTED_DEVICE_ID:

            raise RuntimeError(
                (
                    f"ADXL355 Device ID mismatch. "
                    f"Expected={hex(self.EXPECTED_DEVICE_ID)} "
                    f"Received={hex(device_id)}"
                )
            )

        self._write_register(
            self.REG_RANGE,
            self.RANGE_2G
        )

        self._write_register(
            self.REG_POWER_CTL,
            self.MEASUREMENT_MODE
        )

        self.logger.acquisition_started()

    def _read_register(
        self,
        register: int
    ) -> int:

        tx = [
            (register << 1) | 0x01,
            0x00
        ]

        rx = self.spi.xfer2(tx)

        return rx[1]

    def _write_register(
        self,
        register: int,
        value: int
    ) -> None:

        tx = [
            (register << 1),
            value
        ]

        self.spi.xfer2(tx)

    def _read_axis_raw(
        self,
        start_register: int
    ) -> int:

        tx = [
            (start_register << 1) | 0x01,
            0x00,
            0x00,
            0x00
        ]

        rx = self.spi.xfer2(tx)

        raw = (
            (rx[1] << 16)
            |
            (rx[2] << 8)
            |
            rx[3]
        )

        raw >>= 4

        if raw & (1 << 19):

            raw -= (1 << 20)

        return raw

    def _raw_to_ms2(
        self,
        raw_value: int
    ) -> float:

        return (
            raw_value
            *
            self.SCALE_FACTOR_2G
        )

    def _calculate_magnitude(
        self,
        ax: float,
        ay: float,
        az: float
    ) -> float:

        return math.sqrt(
            ax * ax
            +
            ay * ay
            +
            az * az
        )

    def read_sample(
        self
    ) -> Dict[str, Any]:

        x_raw = self._read_axis_raw(
            self.REG_XDATA3
        )

        y_raw = self._read_axis_raw(
            self.REG_YDATA3
        )

        z_raw = self._read_axis_raw(
            self.REG_ZDATA3
        )

        ax = self._raw_to_ms2(
            x_raw
        )

        ay = self._raw_to_ms2(
            y_raw
        )

        az = self._raw_to_ms2(
            z_raw
        )

        magnitude = (
            self._calculate_magnitude(
                ax,
                ay,
                az
            )
        )

        self.samples_read += 1

        self.last_sample_monotonic = (
            time.monotonic()
        )

        return {

            "ax": ax,

            "ay": ay,

            "az": az,

            "magnitude": magnitude
        }

    def run(self) -> None:

        next_sample_time = (
            time.perf_counter()
        )

        while not self.stop_event.is_set():

            try:

                sample = (
                    self.read_sample()
                )

                self.sample_queue.put(
                    sample,
                    timeout=1
                )

            except queue.Full:

                self.read_errors += 1

                self.logger.sensor_error(
                    "Sample queue full"
                )

            except Exception as error:

                self.read_errors += 1

                self.logger.sensor_error(
                    (
                        f"Sensor read error: "
                        f"{error}"
                    )
                )

                time.sleep(1)

            next_sample_time += (
                self.sample_interval
            )

            sleep_time = (
                next_sample_time
                -
                time.perf_counter()
            )

            if sleep_time > 0:

                time.sleep(
                    sleep_time
                )

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

            if self.spi is not None:

                self.spi.close()

        except Exception:

            pass

    def reconnect(
        self
    ) -> bool:

        try:

            self._cleanup()

            self._initialize_sensor()

            return True

        except Exception as error:

            self.logger.sensor_error(
                (
                    f"Reconnect failed: "
                    f"{error}"
                )
            )

            return False

    def is_healthy(
        self
    ) -> bool:

        if self.read_errors > 100:

            return False

        age = (
            time.monotonic()
            -
            self.last_sample_monotonic
        )

        if age > 5:

            return False

        return True

    def statistics(
        self
    ) -> Dict[str, Any]:

        return {

            "samples_read":
                self.samples_read,

            "read_errors":
                self.read_errors,

            "sampling_rate":
                self.sampling_rate,

            "last_sample_age_seconds":
                (
                    time.monotonic()
                    -
                    self.last_sample_monotonic
                )
        }