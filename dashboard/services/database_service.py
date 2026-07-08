import sqlite3
from pathlib import Path


class DatabaseService:
    def __init__(self):

        # db_path = Path("earthquake.db")
        db_path = Path(__file__).resolve().parents[2] / "earthquake.db"
        print(f"Dashboard is using database: {db_path}")


        self.connection = sqlite3.connect(
            db_path,
            check_same_thread=False
        )

        self.connection.row_factory = sqlite3.Row

    # def execute(self, query, params=None):
    #     with self.connection.cursor() as cursor:
    #         cursor.execute(query, params)

    #         if cursor.description:
    #             return cursor.fetchall()

    #         self.connection.commit()
    #         return []
    def execute(self, query, params=()):
        cursor = self.connection.cursor()

        cursor.execute(query, params)

        if cursor.description:
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        self.connection.commit()
        return []
    # ----------------------------------------------------
    # Earthquake Events
    # ----------------------------------------------------

    def get_events(self):
        query = """
        SELECT *
        FROM events
        ORDER BY event_time DESC;
        """
        return self.execute(query)
    

    def get_latest_event(self):
        query = """
        SELECT *
        FROM events
        ORDER BY event_time DESC
        LIMIT 1;
        """
        rows = self.execute(query)
        return rows[0] if rows else None
    # ----------------------------------------------------
    # Stations
    # ----------------------------------------------------

    def get_stations(self):
        query = """
        SELECT *
        FROM stations
        ORDER BY station_id;
        """
        return self.execute(query)

    # ----------------------------------------------------
    # Station Health
    # ----------------------------------------------------

    def get_station_health(self):
        query = """
        SELECT *
        FROM station_health
        ORDER BY timestamp DESC;
        """
        return self.execute(query)

    # ----------------------------------------------------
    # MQTT Logs
    # ----------------------------------------------------

    # def get_mqtt_logs(self, limit=100):
    #     query = """
    #     SELECT *
    #     FROM mqtt_logs
    #     ORDER BY timestamp DESC
    #     LIMIT %s;
    #     """
    #     return self.execute(query, (limit,))

    def get_mqtt_logs(self, limit=100):
        return []

    # ----------------------------------------------------
    # Close Connection
    # ----------------------------------------------------

    def close(self):
        self.connection.close()


db = DatabaseService()