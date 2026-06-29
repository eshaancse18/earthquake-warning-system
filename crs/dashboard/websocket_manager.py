import json
import asyncio

from threading import RLock
from typing import Dict
from typing import Set


class WebSocketManager:
    """
    CRS Dashboard WebSocket Manager

    Responsibilities
    ----------------

    1. Manage dashboard clients
    2. Broadcast earthquake alerts
    3. Broadcast health reports
    4. Broadcast station status
    5. Maintain connection statistics
    """

    def __init__(self):

        self.lock = RLock()

        self.connections: Set = set()

        self.total_connections = 0

        self.messages_sent = 0

        self.last_message = None

    # ==========================================================
    # CONNECTIONS
    # ==========================================================

    async def connect(
        self,
        websocket
    ) -> None:

        await websocket.accept()

        with self.lock:

            self.connections.add(
                websocket
            )

            self.total_connections += 1

    async def disconnect(
        self,
        websocket
    ) -> None:

        with self.lock:

            if websocket in self.connections:

                self.connections.remove(
                    websocket
                )

    # ==========================================================
    # SEND
    # ==========================================================

    async def send(
        self,
        websocket,
        message: Dict
    ) -> None:

        try:

            await websocket.send_text(
                json.dumps(
                    message,
                    default=str
                )
            )

            self.messages_sent += 1

        except Exception:

            await self.disconnect(
                websocket
            )

    # ==========================================================
    # BROADCAST
    # ==========================================================

    async def broadcast(
        self,
        message: Dict
    ) -> None:

        with self.lock:

            clients = list(
                self.connections
            )

        if not clients:

            return

        payload = json.dumps(
            message,
            default=str
        )

        disconnected = []

        for websocket in clients:

            try:

                await websocket.send_text(
                    payload
                )

                self.messages_sent += 1

            except Exception:

                disconnected.append(
                    websocket
                )

        for websocket in disconnected:

            await self.disconnect(
                websocket
            )

        self.last_message = message

    # ==========================================================
    # EARTHQUAKE
    # ==========================================================

    async def broadcast_earthquake(
        self,
        earthquake: Dict
    ) -> None:

        await self.broadcast(

            {
                "type":
                    "EARTHQUAKE",

                "payload":
                    earthquake
            }
        )

    # ==========================================================
    # HEALTH
    # ==========================================================

    async def broadcast_health(
        self,
        report: Dict
    ) -> None:

        await self.broadcast(

            {
                "type":
                    "HEALTH",

                "payload":
                    report
            }
        )

    # ==========================================================
    # ALERT
    # ==========================================================

    async def broadcast_alert(
        self,
        alert: Dict
    ) -> None:

        await self.broadcast(

            {
                "type":
                    "ALERT",

                "payload":
                    alert
            }
        )

    # ==========================================================
    # STATION STATUS
    # ==========================================================

    async def broadcast_station_status(
        self,
        status: Dict
    ) -> None:

        await self.broadcast(

            {
                "type":
                    "STATION_STATUS",

                "payload":
                    status
            }
        )

    # ==========================================================
    # HEALTH
    # ==========================================================

    def is_healthy(
        self
    ) -> bool:

        return True

    # ==========================================================
    # STATS
    # ==========================================================

    def statistics(
        self
    ) -> Dict:

        with self.lock:

            return {

                "active_connections":
                    len(
                        self.connections
                    ),

                "total_connections":
                    self.total_connections,

                "messages_sent":
                    self.messages_sent,

                "last_message":
                    self.last_message
            }