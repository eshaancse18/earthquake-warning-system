from services.database_service import db
from services.mqtt_service import mqtt_service


class CRSService:

    def __init__(self):
        self.db = db
        self.mqtt = mqtt_service

    # ----------------------------------------------------
    # Stations
    # ----------------------------------------------------

    def get_stations(self):
        return self.db.get_stations()

    # ----------------------------------------------------
    # Health
    # ----------------------------------------------------

    def get_station_health(self):
        return self.db.get_station_health()

    # ----------------------------------------------------
    # Events
    # ----------------------------------------------------

    def get_events(self):
        return self.db.get_events()

    def get_latest_event(self):
        return self.db.get_latest_event()

    # ----------------------------------------------------
    # MQTT
    # ----------------------------------------------------

    def get_mqtt_logs(self):
        return self.mqtt.get_messages()

    # ----------------------------------------------------
    # Status
    # ----------------------------------------------------

    def mqtt_connected(self):
        return self.mqtt.is_connected()


crs_service = CRSService()