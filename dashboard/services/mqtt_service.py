import json
import threading
from collections import deque

import paho.mqtt.client as mqtt


class MQTTService:
    def __init__(
        self,
        broker="localhost",
        port=1883,
        topics=None,
        max_messages=500,
    ):
        self.broker = broker
        self.port = port

        self.topics = topics or [
            ("ssn/+/heartbeat", 0),
            ("ssn/+/health", 0),
            ("ssn/+/event", 0),
            ("crs/alert", 0),
            ("crs/voting", 0),
        ]

        self.messages = deque(maxlen=max_messages)
        self.connected = False

        self.client = mqtt.Client()

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

    # --------------------------------------------------
    # MQTT Callbacks
    # --------------------------------------------------

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True

            for topic, qos in self.topics:
                client.subscribe(topic, qos)

            print("Connected to MQTT Broker")

        else:
            print(f"Connection failed. Code = {rc}")

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        print("Disconnected from MQTT Broker")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except Exception:
            payload = msg.payload.decode()

        self.messages.appendleft(
            {
                "topic": msg.topic,
                "payload": payload,
            }
        )

    # --------------------------------------------------
    # Public Methods
    # --------------------------------------------------

    def start(self):
        self.client.connect(self.broker, self.port)

        thread = threading.Thread(
            target=self.client.loop_forever,
            daemon=True,
        )

        thread.start()

    def stop(self):
        self.client.disconnect()

    def publish(self, topic, payload):
        if isinstance(payload, dict):
            payload = json.dumps(payload)

        self.client.publish(topic, payload)

    def get_messages(self):
        return list(self.messages)

    def clear_messages(self):
        self.messages.clear()

    def is_connected(self):
        return self.connected


mqtt_service = MQTTService()