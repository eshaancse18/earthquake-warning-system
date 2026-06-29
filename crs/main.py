"""
Central Receiving Server

Application entry point.
"""

from __future__ import annotations

import threading
import uvicorn

from api.main import app
from communication.mqtt_client import MQTTClient
from logging_system.logger import logger
from processing.event_manager import EventManager
from processing.event_receiver import EventReceiver
from processing.station_manager import station_manager


# --------------------------------------------------
# Create Components
# --------------------------------------------------

event_manager = EventManager()

event_receiver = EventReceiver(
    event_manager
)

mqtt_client = MQTTClient()


# --------------------------------------------------
# Register MQTT Callbacks
# --------------------------------------------------

mqtt_client.register_event_callback(
    event_receiver.handle_event
)

mqtt_client.register_health_callback(
    station_manager.handle_health_report
)


# --------------------------------------------------
# MQTT Thread
# --------------------------------------------------

def mqtt_thread():

    logger.info(
        "Starting MQTT Service..."
    )

    mqtt_client.connect()

    mqtt_client.start()


# --------------------------------------------------
# API Thread
# --------------------------------------------------

def api_thread():

    logger.info(
        "Starting FastAPI..."
    )

    uvicorn.run(

        app,

        host="0.0.0.0",

        port=8000

    )


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    logger.info(
        "=" * 50
    )

    logger.info(
        "CRS STARTING..."
    )

    logger.info(
        "=" * 50
    )

    mqtt = threading.Thread(

        target=mqtt_thread,

        daemon=True

    )

    api = threading.Thread(

        target=api_thread,

        daemon=True

    )

    mqtt.start()

    api.start()

    mqtt.join()

    api.join()


if __name__ == "__main__":

    main()