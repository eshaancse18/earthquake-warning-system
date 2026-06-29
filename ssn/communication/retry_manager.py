import threading
import time
from typing import Dict
from typing import List

from logging_system.logger import CommunicationLogger


class RetryManager(threading.Thread):
    """
    MQTT Packet Replay Manager

    Responsibilities:
    -----------------
    1. Detect pending packets
    2. Replay unsent packets
    3. Handle MQTT outages
    4. Ensure zero packet loss
    5. Track replay statistics

    Workflow:
    ---------

    Packet Created
            ↓
    Save SQLite
            ↓
    MQTT Send
            ↓

    Success?
       |
    YES ----> Mark Transmitted

    NO
       ↓
    Pending Queue

       ↓

    Retry Manager

       ↓

    MQTT Available?

       |
    YES

       ↓

    Replay Packet

       ↓

    Mark Transmitted
    """

    def __init__(
        self,
        station_id: str,
        mqtt_client,
        local_database,
        retry_interval_seconds: int = 10,
        batch_size: int = 100
    ):

        super().__init__(
            name="RETRY_MANAGER_THREAD",
            daemon=True
        )

        self.station_id = station_id

        self.mqtt_client = mqtt_client

        self.local_database = local_database

        self.retry_interval_seconds = (
            retry_interval_seconds
        )

        self.batch_size = batch_size

        self.stop_event = threading.Event()

        self.logger = (
            CommunicationLogger()
        )

        self.total_replayed = 0

        self.total_failed = 0

        self.last_replay_time = None

    def stop(self) -> None:

        self.stop_event.set()

    def _mqtt_available(
        self
    ) -> bool:

        try:

            return bool(
                self.mqtt_client.connected
            )

        except Exception:

            return False

    def _load_pending_packets(
        self
    ) -> List[Dict]:

        return (
            self.local_database
            .get_pending_packets(
                limit=self.batch_size
            )
        )

    def _replay_packet(
        self,
        packet: Dict
    ) -> bool:

        try:

            topic = packet["topic"]

            payload = packet["payload"]

            packet_id = (
                packet["packet_id"]
            )

            success = (
                self.mqtt_client
                ._send_packet(
                    topic=topic,
                    packet=payload
                )
            )

            if success:

                self.local_database.mark_packet_transmitted(
                    packet_id
                )

                self.total_replayed += 1

                return True

            self.total_failed += 1

            return False

        except Exception as error:

            self.total_failed += 1

            self.logger.packet_failed(
                topic="REPLAY",
                error=str(error)
            )

            return False

    def _replay_batch(
        self
    ) -> None:

        packets = (
            self._load_pending_packets()
        )

        if not packets:

            return

        self.logger.logger.info(
            (
                f"Replaying "
                f"{len(packets)} "
                f"pending packets"
            )
        )

        for packet in packets:

            if (
                self.stop_event.is_set()
            ):

                return

            if (
                not self._mqtt_available()
            ):

                return

            self._replay_packet(
                packet
            )

    def run(
        self
    ) -> None:

        self.logger.logger.info(
            "Retry Manager Started"
        )

        while not self.stop_event.is_set():

            try:

                if (
                    self._mqtt_available()
                ):

                    self._replay_batch()

                    self.last_replay_time = (
                        time.time()
                    )

            except Exception as error:

                self.logger.packet_failed(
                    topic="RETRY_MANAGER",
                    error=str(error)
                )

            self.stop_event.wait(
                self.retry_interval_seconds
            )

        self.logger.logger.info(
            "Retry Manager Stopped"
        )

    def statistics(
        self
    ) -> Dict:

        return {
            "station_id":
                self.station_id,

            "total_replayed":
                self.total_replayed,

            "total_failed":
                self.total_failed,

            "last_replay_time":
                self.last_replay_time,

            "pending_packets":
                self.local_database
                .pending_packet_count()
        }

    def is_healthy(
        self
    ) -> bool:

        if self.total_failed > 1000:

            return False

        return True