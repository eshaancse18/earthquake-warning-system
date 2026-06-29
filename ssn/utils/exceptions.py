class EarthquakeSystemException(Exception):
    """
    Base exception for the entire
    Earthquake Warning System.
    """

    pass


class ConfigurationError(
    EarthquakeSystemException
):
    """
    Configuration file errors.
    """

    pass


class InvalidConfigurationError(
    ConfigurationError
):
    """
    Invalid configuration values.
    """

    pass


class MissingConfigurationError(
    ConfigurationError
):
    """
    Missing configuration parameters.
    """

    pass


class SensorException(
    EarthquakeSystemException
):
    """
    Base sensor exception.
    """

    pass


class SensorInitializationError(
    SensorException
):
    """
    Sensor startup failure.
    """

    pass


class SensorReadError(
    SensorException
):
    """
    Sensor sample acquisition failure.
    """

    pass


class SensorCalibrationError(
    SensorException
):
    """
    Sensor calibration failure.
    """

    pass


class SensorTimeoutError(
    SensorException
):
    """
    Sensor timeout.
    """

    pass


class GPSError(
    EarthquakeSystemException
):
    """
    GPS base exception.
    """

    pass


class GPSConnectionError(
    GPSError
):
    """
    GPS serial connection failure.
    """

    pass


class GPSLockError(
    GPSError
):
    """
    GPS lock unavailable.
    """

    pass


class GPSParseError(
    GPSError
):
    """
    NMEA parsing failure.
    """

    pass


class BufferException(
    EarthquakeSystemException
):
    """
    Buffer subsystem exception.
    """

    pass


class BufferOverflowError(
    BufferException
):
    """
    Buffer overflow.
    """

    pass


class BufferUnderflowError(
    BufferException
):
    """
    Buffer underflow.
    """

    pass


class EventException(
    EarthquakeSystemException
):
    """
    Event processing exception.
    """

    pass


class EventDetectionError(
    EventException
):
    """
    Event detection failure.
    """

    pass


class EventStorageError(
    EventException
):
    """
    Event storage failure.
    """

    pass


class EventTransmissionError(
    EventException
):
    """
    Event transmission failure.
    """

    pass


class CommunicationException(
    EarthquakeSystemException
):
    """
    Communication subsystem exception.
    """

    pass


class MQTTConnectionError(
    CommunicationException
):
    """
    MQTT connection failure.
    """

    pass


class MQTTPublishError(
    CommunicationException
):
    """
    MQTT publish failure.
    """

    pass


class PacketValidationError(
    CommunicationException
):
    """
    Invalid packet structure.
    """

    pass


class DatabaseException(
    EarthquakeSystemException
):
    """
    Database base exception.
    """

    pass


class DatabaseConnectionError(
    DatabaseException
):
    """
    Database connection failure.
    """

    pass


class DatabaseWriteError(
    DatabaseException
):
    """
    Database write failure.
    """

    pass


class DatabaseReadError(
    DatabaseException
):
    """
    Database read failure.
    """

    pass


class HealthMonitorException(
    EarthquakeSystemException
):
    """
    Health monitoring exception.
    """

    pass


class DiagnosticsException(
    HealthMonitorException
):
    """
    Diagnostics failure.
    """

    pass


class WatchdogException(
    HealthMonitorException
):
    """
    Watchdog failure.
    """

    pass


class ProcessingException(
    EarthquakeSystemException
):
    """
    Signal processing exception.
    """

    pass


class FilterException(
    ProcessingException
):
    """
    Filtering failure.
    """

    pass


class STALTAException(
    ProcessingException
):
    """
    STA/LTA calculation failure.
    """

    pass


class PGAException(
    ProcessingException
):
    """
    PGA calculation failure.
    """

    pass


class FrequencyAnalysisException(
    ProcessingException
):
    """
    FFT analysis failure.
    """

    pass


class PWaveDetectionException(
    ProcessingException
):
    """
    P-wave detection failure.
    """

    pass


class ThreadException(
    EarthquakeSystemException
):
    """
    Thread management exception.
    """

    pass


class ThreadStartupError(
    ThreadException
):
    """
    Thread startup failure.
    """

    pass


class ThreadTerminationError(
    ThreadException
):
    """
    Thread termination failure.
    """

    pass


class StorageException(
    EarthquakeSystemException
):
    """
    Waveform storage exception.
    """

    pass


class FileWriteError(
    StorageException
):
    """
    File write failure.
    """

    pass


class FileReadError(
    StorageException
):
    """
    File read failure.
    """

    pass


class CRSException(
    EarthquakeSystemException
):
    """
    CRS communication exception.
    """

    pass


class VotingException(
    CRSException
):
    """
    Voting engine failure.
    """

    pass


class AlertGenerationException(
    CRSException
):
    """
    Alert generation failure.
    """

    pass

class RetryException(
    CommunicationException
):
    """
    Retry manager failure.
    """
    pass


class FFTException(
    FrequencyAnalysisException
):
    """
    FFT computation failure.
    """
    pass


class WaveformStorageError(
    StorageException
):
    """
    Waveform storage failure.
    """
    pass

class QueueFullException(
    CommunicationException
):
    """
    Internal queue full.
    """
    pass


class QueueEmptyException(
    CommunicationException
):
    """
    Internal queue empty.
    """
    pass


class HealthThresholdException(
    HealthMonitorException
):
    """
    Critical health threshold exceeded.
    """
    pass




__all__ = [

    "EarthquakeSystemException",

    "ConfigurationError",
    "InvalidConfigurationError",
    "MissingConfigurationError",

    "SensorException",
    "SensorInitializationError",
    "SensorReadError",
    "SensorCalibrationError",
    "SensorTimeoutError",

    "GPSError",
    "GPSConnectionError",
    "GPSLockError",
    "GPSParseError",

    "BufferException",
    "BufferOverflowError",
    "BufferUnderflowError",

    "EventException",
    "EventDetectionError",
    "EventStorageError",
    "EventTransmissionError",

    "CommunicationException",
    "MQTTConnectionError",
    "MQTTPublishError",
    "PacketValidationError",
    "RetryException",

    "DatabaseException",
    "DatabaseConnectionError",
    "DatabaseWriteError",
    "DatabaseReadError",

    "HealthMonitorException",
    "DiagnosticsException",
    "WatchdogException",
    "HealthThresholdException",

    "ProcessingException",
    "FilterException",
    "STALTAException",
    "PGAException",
    "FrequencyAnalysisException",
    "FFTException",
    "PWaveDetectionException",

    "ThreadException",
    "ThreadStartupError",
    "ThreadTerminationError",

    "StorageException",
    "FileWriteError",
    "FileReadError",
    "WaveformStorageError",

    "CRSException",
    "VotingException",
    "AlertGenerationException",

    "QueueFullException",
    "QueueEmptyException"
]