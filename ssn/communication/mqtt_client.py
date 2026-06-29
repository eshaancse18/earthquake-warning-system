import json
import queue
import threading
import time

from datetime import datetime
from datetime import timezone

from typing import Dict
from typing import Any
from typing import Optional

import paho.mqtt.client as mqtt

from communication.packet_builder import PacketBuilder

from logging_system.logger import (
    CommunicationLogger
)


class MQTTClient(threading.Thread):

    """
    Production MQTT Client

    Features
    --------
    1. Automatic Reconnect
    2. Local SQLite Persistence
    3. QoS Delivery
    4. ACK Tracking
    5. Offline Queueing
    6. Packet Replay Support
    7. Thread-Safe Operations
    8. Delivery Statistics

    Workflow
    --------

    publish()
        ↓

    SQLite Save
        ↓

    Local Queue
        ↓

    MQTT Publish
        ↓

    ACK Received
        ↓

    Mark SQLite Transmitted
    """

    def __init__(
        self,
        broker_ip: str,
        broker_port: int,
        keepalive: int,
        qos: int,
        event_topic: str,
        health_topic: str,
        station_id: str,
        local_database
    ):

        super().__init__(
            name="MQTT_THREAD",
            daemon=True
        )

        # =====================================================
        # CONFIGURATION
        # =====================================================

        self.station_id = (
            station_id
        )

        self.broker_ip = (
            broker_ip
        )

        self.broker_port = (
            broker_port
        )

        self.keepalive = (
            keepalive
        )

        self.qos = (
            qos
        )

        self.event_topic = (
            event_topic
        )

        self.health_topic = (
            health_topic
        )

        self.local_database = (
            local_database
        )

        # =====================================================
        # LOGGING
        # =====================================================

        self.logger = (
            CommunicationLogger()
        )

        # =====================================================
        # THREAD CONTROL
        # =====================================================

        self.stop_event = (
            threading.Event()
        )

        self.connection_lock = (
            threading.RLock()
        )

        self.ack_lock = (
            threading.Lock()
        )

        # =====================================================
        # CONNECTION STATE
        # =====================================================

        self.connected = False

        self.loop_running = False

        self.connection_attempts = 0

        self.last_connection_time = None

        self.last_disconnect_time = None

        # =====================================================
        # MESSAGE STATISTICS
        # =====================================================

        self.messages_sent = 0

        self.messages_failed = 0

        self.messages_queued = 0

        self.messages_acknowledged = 0

        self.consecutive_failures = 0

        self.last_publish_time = None

        # =====================================================
        # ACK TRACKING
        # =====================================================

        self.pending_ack = {}

        # Structure:
        #
        # {
        #     mqtt_mid:
        #         packet_id
        # }

        # =====================================================
        # PUBLISH QUEUE
        # =====================================================

        self.publish_queue = (
            queue.Queue(
                maxsize=10000
            )
        )

        # =====================================================
        # MQTT CLIENT
        # =====================================================

        self.client = mqtt.Client(
            client_id=(
                f"SSN_{station_id}"
            ),
            clean_session=False
        )

        self.client.on_connect = (
            self._on_connect
        )

        self.client.on_disconnect = (
            self._on_disconnect
        )

        self.client.on_publish = (
            self._on_publish
        )

        self.client.reconnect_delay_set(
            min_delay=1,
            max_delay=60
        )

        self.logger.logger.info(
            (
                "MQTT_CLIENT_INITIALIZED | "
                f"station_id={station_id} | "
                f"broker={broker_ip}:{broker_port}"
            )
        )







            # =====================================================
    # MQTT CALLBACKS
    # =====================================================

    def _on_connect(
        self,
        client,
        userdata,
        flags,
        rc
    ) -> None:

        with self.connection_lock:

            if rc == 0:

                self.connected = True

                self.connection_attempts = 0

                self.last_connection_time = (
                    datetime.now(
                        timezone.utc
                    )
                )

                self.logger.mqtt_connected()

                self.logger.logger.info(
                    (
                        "MQTT_CONNECTED | "
                        f"broker={self.broker_ip}:"
                        f"{self.broker_port}"
                    )
                )

            else:

                self.connected = False

                self.logger.logger.error(
                    (
                        "MQTT_CONNECTION_FAILED | "
                        f"return_code={rc}"
                    )
                )

    def _on_disconnect(
        self,
        client,
        userdata,
        rc
    ) -> None:

        with self.connection_lock:

            self.connected = False

            self.last_disconnect_time = (
                datetime.now(
                    timezone.utc
                )
            )

            self.logger.mqtt_disconnected()

            self.logger.logger.warning(
                (
                    "MQTT_DISCONNECTED | "
                    f"return_code={rc}"
                )
            )

    def _on_publish(
        self,
        client,
        userdata,
        mid
    ) -> None:

        try:

            with self.ack_lock:

                packet_id = (
                    self.pending_ack.get(
                        mid
                    )
                )

                if packet_id is not None:

                    self.local_database.mark_packet_transmitted(
                        packet_id
                    )

                    del self.pending_ack[mid]

            self.messages_sent += 1

            self.messages_acknowledged += 1

            self.consecutive_failures = 0

            self.last_publish_time = (
                datetime.now(
                    timezone.utc
                )
            )

        except Exception as error:

            self.logger.packet_failed(
                topic="ACK_HANDLER",
                error=str(error)
            )

    # =====================================================
    # CONNECTION MANAGEMENT
    # =====================================================

    def connect(
        self
    ) -> bool:

        with self.connection_lock:

            try:

                self.connection_attempts += 1

                self.client.connect(
                    host=self.broker_ip,
                    port=self.broker_port,
                    keepalive=self.keepalive
                )

                if not self.loop_running:

                    self.client.loop_start()

                    self.loop_running = True

                self.logger.logger.info(
                    (
                        "MQTT_CONNECT_ATTEMPT | "
                        f"attempt="
                        f"{self.connection_attempts}"
                    )
                )

                return True

            except Exception as error:

                self.connected = False

                self.logger.packet_failed(
                    topic="CONNECT",
                    error=str(error)
                )

                return False

    def disconnect(
        self
    ) -> None:

        with self.connection_lock:

            try:

                if self.loop_running:

                    self.client.loop_stop()

                    self.loop_running = False

                self.client.disconnect()

            except Exception as error:

                self.logger.packet_failed(
                    topic="DISCONNECT",
                    error=str(error)
                )

            finally:

                self.connected = False

                self.logger.logger.info(
                    "MQTT_CLIENT_STOPPED"
                )


        # =====================================================
    # PUBLISH API
    # =====================================================

    def publish(
        self,
        topic: str,
        packet: Dict[str, Any]
    ) -> bool:

        try:

            if not PacketBuilder.validate_packet(
                packet
            ):

                self.logger.packet_failed(
                    topic=topic,
                    error="Invalid packet"
                )

                return False

            packet_id = packet.get(
                "packet_id"
            )

            packet_type = packet.get(
                "packet_type"
            )

            # =========================================
            # STORE BEFORE TRANSMISSION
            # =========================================

            self.local_database.save_outgoing_packet(
                packet_id=packet_id,
                packet_type=packet_type,
                topic=topic,
                payload=packet
            )

            # =========================================
            # ADD TO TRANSMISSION QUEUE
            # =========================================

            try:

                self.publish_queue.put(
                    (
                        topic,
                        packet
                    ),
                    block=True,
                    timeout=2
                )

                self.messages_queued += 1

                return True

            except queue.Full:

                self.messages_failed += 1

                self.logger.packet_failed(
                    topic=topic,
                    error="Publish queue full"
                )

                return False

        except Exception as error:

            self.messages_failed += 1

            self.logger.packet_failed(
                topic=topic,
                error=str(error)
            )

            return False

    # =====================================================
    # EVENT PACKETS
    # =====================================================

    def publish_event(
        self,
        event_record: Dict[str, Any]
    ) -> bool:

        packet = (
            PacketBuilder
            .build_event_packet(
                station_id=self.station_id,
                event_record=event_record
            )
        )

        return self.publish(
            self.event_topic,
            packet
        )

    # =====================================================
    # HEALTH PACKETS
    # =====================================================

    def publish_health(
        self,
        packet: Dict[str, Any]
    ) -> bool:

        return self.publish(
            self.health_topic,
            packet
        )

    # =====================================================
    # HEARTBEAT PACKETS
    # =====================================================

    def publish_heartbeat(
        self
    ) -> bool:

        packet = (
            PacketBuilder
            .build_heartbeat_packet(
                station_id=self.station_id
            )
        )

        return self.publish(
            "earthquake/heartbeat",
            packet
        )

    # =====================================================
    # ERROR PACKETS
    # =====================================================

    def publish_error(
        self,
        error_type: str,
        error_message: str
    ) -> bool:

        packet = (
            PacketBuilder
            .build_error_packet(
                station_id=self.station_id,
                error_type=error_type,
                error_message=error_message
            )
        )

        return self.publish(
            "earthquake/errors",
            packet
        )

    # =====================================================
    # SYSTEM PACKETS
    # =====================================================

    def publish_system_message(
        self,
        message: str,
        severity: str = "INFO"
    ) -> bool:

        packet = (
            PacketBuilder
            .build_system_packet(
                station_id=self.station_id,
                message=message,
                severity=severity
            )
        )

        return self.publish(
            "earthquake/system",
            packet
        )
    
        # =====================================================
    # LOW LEVEL TRANSMISSION
    # =====================================================

    def _send_packet(
        self,
        topic: str,
        packet: Dict[str, Any]
    ) -> bool:

        try:

            payload = (
                PacketBuilder.serialize(
                    packet
                )
            )

            result = (
                self.client.publish(
                    topic=topic,
                    payload=payload,
                    qos=self.qos
                )
            )

            if (
                result.rc
                !=
                mqtt.MQTT_ERR_SUCCESS
            ):

                self.logger.packet_failed(
                    topic=topic,
                    error=(
                        f"MQTT Error "
                        f"{result.rc}"
                    )
                )

                return False

            with self.ack_lock:

                self.pending_ack[
                    result.mid
                ] = (
                    packet[
                        "packet_id"
                    ]
                )

            return True

        except Exception as error:

            self.logger.packet_failed(
                topic=topic,
                error=str(error)
            )

            return False

    # =====================================================
    # QUEUE PROCESSOR
    # =====================================================

    def _process_publish_queue(
        self
    ) -> None:

        try:

            topic, packet = (
                self.publish_queue.get(
                    timeout=1
                )
            )

        except queue.Empty:

            return

        success = (
            self._send_packet(
                topic=topic,
                packet=packet
            )
        )

        if success:

            return

        self.messages_failed += 1

        self.consecutive_failures += 1

        try:

            self.publish_queue.put(
                (
                    topic,
                    packet
                ),
                block=False
            )

        except queue.Full:

            self.logger.packet_failed(
                topic=topic,
                error=(
                    "Queue full during "
                    "requeue"
                )
            )

    # =====================================================
    # MAIN THREAD LOOP
    # =====================================================

    def run(
        self
    ) -> None:

        self.logger.logger.info(
            (
                "MQTT_THREAD_STARTED | "
                f"station_id="
                f"{self.station_id}"
            )
        )

        self.connect()

        while (
            not self.stop_event.is_set()
        ):

            try:

                # ==========================
                # CONNECTION MANAGEMENT
                # ==========================

                if not self.connected:

                    self.logger.logger.warning(
                        (
                            "MQTT_RECONNECTING"
                        )
                    )

                    time.sleep(5)

                    self.connect()

                    continue

                # ==========================
                # SEND QUEUED PACKETS
                # ==========================

                self._process_publish_queue()

            except Exception as error:

                self.messages_failed += 1

                self.consecutive_failures += 1

                self.logger.packet_failed(
                    topic="MQTT_THREAD",
                    error=str(error)
                )

                time.sleep(1)

        self.logger.logger.info(
            (
                "MQTT_THREAD_STOPPED | "
                f"station_id="
                f"{self.station_id}"
            )
        )



        # =====================================================
    # SHUTDOWN
    # =====================================================

    def stop(
        self
    ) -> None:

        self.logger.logger.info(
            (
                "MQTT_STOP_REQUESTED | "
                f"station_id="
                f"{self.station_id}"
            )
        )

        self.stop_event.set()

        self.disconnect()

    # =====================================================
    # STATISTICS
    # =====================================================

    def statistics(
        self
    ) -> Dict[str, Any]:

        with self.ack_lock:

            pending_ack_count = (
                len(
                    self.pending_ack
                )
            )

        return {

            "station_id":
                self.station_id,

            "connected":
                self.connected,

            "broker":
                (
                    f"{self.broker_ip}:"
                    f"{self.broker_port}"
                ),

            "messages_sent":
                self.messages_sent,

            "messages_failed":
                self.messages_failed,

            "messages_queued":
                self.messages_queued,

            "messages_acknowledged":
                self.messages_acknowledged,

            "consecutive_failures":
                self.consecutive_failures,

            "pending_ack":
                pending_ack_count,

            "queue_size":
                self.publish_queue.qsize(),

            "connection_attempts":
                self.connection_attempts,

            "last_connection_time":
                (
                    self.last_connection_time
                    .isoformat()
                    if self.last_connection_time
                    else None
                ),

            "last_disconnect_time":
                (
                    self.last_disconnect_time
                    .isoformat()
                    if self.last_disconnect_time
                    else None
                ),

            "last_publish_time":
                (
                    self.last_publish_time
                    .isoformat()
                    if self.last_publish_time
                    else None
                )
        }

    # =====================================================
    # HEALTH CHECK
    # =====================================================

    def is_healthy(
        self
    ) -> bool:

        if not self.connected:

            return False

        if (
            self.consecutive_failures
            > 20
        ):

            return False

        if (
            self.publish_queue.qsize()
            > 9000
        ):

            return False

        return True

    # =====================================================
    # CONNECTION STATUS
    # =====================================================

    def is_connected(
        self
    ) -> bool:

        return self.connected

    # =====================================================
    # ACK STATUS
    # =====================================================

    def pending_ack_count(
        self
    ) -> int:

        with self.ack_lock:

            return len(
                self.pending_ack
            )

    # =====================================================
    # QUEUE STATUS
    # =====================================================

    def queue_size(
        self
    ) -> int:

        return (
            self.publish_queue
            .qsize()
        )

    # =====================================================
    # DATABASE BACKLOG
    # =====================================================

    def pending_packet_count(
        self
    ) -> int:

        try:

            return (
                self.local_database
                .pending_packet_count()
            )

        except Exception:

            return -1

    # =====================================================
    # MQTT CLIENT INFO
    # =====================================================

    def connection_info(
        self
    ) -> Dict[str, Any]:

        return {

            "broker_ip":
                self.broker_ip,

            "broker_port":
                self.broker_port,

            "keepalive":
                self.keepalive,

            "qos":
                self.qos,

            "connected":
                self.connected
        }
