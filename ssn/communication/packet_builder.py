import json
import uuid
from datetime import datetime
from typing import Dict
from typing import Any


class PacketBuilder:
    """
    Builds standardized packets for:

    1. Event Transmission
    2. Health Reports
    3. Heartbeats
    4. Error Reports

    All packets follow a common structure:

    {
        packet_id,
        packet_type,
        station_id,
        timestamp,
        payload
    }
    """

    EVENT_PACKET = "EVENT"

    HEALTH_PACKET = "HEALTH"

    HEARTBEAT_PACKET = "HEARTBEAT"

    ERROR_PACKET = "ERROR"

    SYSTEM_PACKET = "SYSTEM"

    @staticmethod
    def _generate_packet_id() -> str:

        return str(
            uuid.uuid4()
        )

    @staticmethod
    def _utc_timestamp() -> str:

        return (
            datetime.utcnow()
            .isoformat()
        )

    @classmethod
    def _base_packet(
        cls,
        packet_type: str,
        station_id: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:

        return {
            "packet_id":
                cls._generate_packet_id(),

            "packet_type":
                packet_type,

            "station_id":
                station_id,

            "timestamp":
                cls._utc_timestamp(),

            "payload":
                payload
        }

    @classmethod
    def build_event_packet(
        cls,
        station_id: str,
        event_record: Dict[str, Any]
    ) -> Dict[str, Any]:

        return cls._base_packet(
            packet_type=cls.EVENT_PACKET,
            station_id=station_id,
            payload=event_record
        )

    @classmethod
    def build_health_packet(
        cls,
        station_id: str,
        cpu_usage: float,
        ram_usage: float,
        disk_usage: float,
        temperature: float,
        gps_status: str,
        network_status: str,
        uptime_seconds: int
    ) -> Dict[str, Any]:

        payload = {
            "cpu_usage":
                cpu_usage,

            "ram_usage":
                ram_usage,

            "disk_usage":
                disk_usage,

            "temperature":
                temperature,

            "gps_status":
                gps_status,

            "network_status":
                network_status,

            "uptime_seconds":
                uptime_seconds
        }

        return cls._base_packet(
            packet_type=cls.HEALTH_PACKET,
            station_id=station_id,
            payload=payload
        )

    @classmethod
    def build_heartbeat_packet(
        cls,
        station_id: str
    ) -> Dict[str, Any]:

        payload = {
            "alive": True
        }

        return cls._base_packet(
            packet_type=cls.HEARTBEAT_PACKET,
            station_id=station_id,
            payload=payload
        )

    @classmethod
    def build_error_packet(
        cls,
        station_id: str,
        error_type: str,
        error_message: str
    ) -> Dict[str, Any]:

        payload = {
            "error_type":
                error_type,

            "error_message":
                error_message
        }

        return cls._base_packet(
            packet_type=cls.ERROR_PACKET,
            station_id=station_id,
            payload=payload
        )

    @classmethod
    def build_system_packet(
        cls,
        station_id: str,
        message: str,
        severity: str
    ) -> Dict[str, Any]:

        payload = {
            "message":
                message,

            "severity":
                severity
        }

        return cls._base_packet(
            packet_type=cls.SYSTEM_PACKET,
            station_id=station_id,
            payload=payload
        )

    @staticmethod
    def serialize(
        packet: Dict[str, Any]
    ) -> str:

        return json.dumps(
            packet,
            ensure_ascii=False,
            separators=(",", ":")
        )

    @staticmethod
    def deserialize(
        packet_string: str
    ) -> Dict[str, Any]:

        return json.loads(
            packet_string
        )

    @staticmethod
    def packet_size_bytes(
        packet: Dict[str, Any]
    ) -> int:

        serialized = json.dumps(
            packet
        )

        return len(
            serialized.encode("utf-8")
        )

    @staticmethod
    def validate_packet(
        packet: Dict[str, Any]
    ) -> bool:

        required_fields = [
            "packet_id",
            "packet_type",
            "station_id",
            "timestamp",
            "payload"
        ]

        for field in required_fields:

            if field not in packet:

                return False

        return True