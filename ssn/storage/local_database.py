
import json
import sqlite3
import threading

from datetime import datetime
from datetime import timezone

from typing import Dict
from typing import Any
from typing import List
from typing import Optional


class LocalDatabase:
    """
    Local SQLite Storage Engine

    Responsibilities
    ----------------
    1. Store confirmed earthquake events
    2. Store health reports
    3. Store unsent MQTT packets
    4. Replay packets after reconnect
    5. Prevent data loss
    6. Provide local persistence

    Tables
    ------
    events
    health_reports
    outgoing_packets
    system_logs
    """

    def __init__(
        self,
        database_path: str
    ):

        self.database_path = (
            database_path
        )

        self.lock = (
            threading.Lock()
        )

        self._initialize_database()

    def _get_connection(
        self
    ) -> sqlite3.Connection:

        connection = sqlite3.connect(
            self.database_path,
            check_same_thread=False
        )

        connection.row_factory = (
            sqlite3.Row
        )

        return connection

    def _initialize_database(
        self
    ) -> None:

        with self.lock:

            connection = (
                self._get_connection()
            )

            cursor = (
                connection.cursor()
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS events
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    event_id TEXT UNIQUE NOT NULL,

                    station_id TEXT NOT NULL,

                    event_time TEXT NOT NULL,

                    confidence REAL,

                    pga REAL,

                    stalta REAL,

                    waveform_json TEXT,

                    created_at TEXT NOT NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS health_reports
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    station_id TEXT NOT NULL,

                    cpu_usage REAL,

                    ram_usage REAL,

                    disk_usage REAL,

                    temperature REAL,

                    gps_status TEXT,

                    network_status TEXT,

                    report_time TEXT NOT NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS outgoing_packets
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    packet_id TEXT UNIQUE,

                    packet_type TEXT,

                    topic TEXT,

                    payload TEXT,

                    transmitted INTEGER DEFAULT 0,

                    created_at TEXT NOT NULL,

                    transmitted_at TEXT
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS system_logs
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    level TEXT,

                    message TEXT,

                    created_at TEXT NOT NULL
                )
                """
            )

            connection.commit()

            connection.close()

    def save_event(
        self,
        event_record: Dict[str, Any]
    ) -> None:

        metadata = event_record.get(
            "metadata",
            {}
        )

        station_id = metadata.get(
            "station_id"
        )

        if not station_id:

            raise ValueError(
                "station_id missing "
                "in event metadata"
            )

        waveform = event_record.get(
            "waveform",
            []
        )

        with self.lock:

            connection = (
                self._get_connection()
            )

            cursor = (
                connection.cursor()
            )

            cursor.execute(
                """
                INSERT OR REPLACE INTO events
                (
                    event_id,
                    station_id,
                    event_time,
                    confidence,
                    pga,
                    stalta,
                    waveform_json,
                    created_at
                )
                VALUES
                (
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    event_record.get(
                        "event_id"
                    ),

                    station_id,

                    event_record.get(
                        "event_start_time"
                    ),

                    metadata.get(
                        "confidence"
                    ),

                    metadata.get(
                        "pga"
                    ),

                    metadata.get(
                        "stalta_ratio"
                    ),

                    json.dumps(
                        waveform,
                        default=str
                    ),

                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )
            )

            connection.commit()

            connection.close()

#part 2
    def save_health_report(
        self,
        report: Dict[str, Any]
    ) -> None:

        with self.lock:

            connection = (
                self._get_connection()
            )

            cursor = (
                connection.cursor()
            )

            cursor.execute(
                """
                INSERT INTO health_reports
                (
                    station_id,
                    cpu_usage,
                    ram_usage,
                    disk_usage,
                    temperature,
                    gps_status,
                    network_status,
                    report_time
                )
                VALUES
                (
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    report.get(
                        "station_id"
                    ),

                    report.get(
                        "cpu_usage"
                    ),

                    report.get(
                        "ram_usage"
                    ),

                    report.get(
                        "disk_usage"
                    ),

                    report.get(
                        "temperature"
                    ),

                    report.get(
                        "gps_status"
                    ),

                    report.get(
                        "network_status"
                    ),

                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )
            )

            connection.commit()

            connection.close()

    def save_outgoing_packet(
        self,
        packet_id: str,
        packet_type: str,
        topic: str,
        payload: Dict[str, Any]
    ) -> None:

        with self.lock:

            connection = (
                self._get_connection()
            )

            cursor = (
                connection.cursor()
            )

            cursor.execute(
                """
                INSERT OR REPLACE INTO outgoing_packets
                (
                    packet_id,
                    packet_type,
                    topic,
                    payload,
                    transmitted,
                    created_at
                )
                VALUES
                (
                    ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    packet_id,

                    packet_type,

                    topic,

                    json.dumps(
                        payload,
                        default=str
                    ),

                    0,

                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )
            )

            connection.commit()

            connection.close()

    def mark_packet_transmitted(
        self,
        packet_id: str
    ) -> None:

        with self.lock:

            connection = (
                self._get_connection()
            )

            cursor = (
                connection.cursor()
            )

            cursor.execute(
                """
                UPDATE outgoing_packets
                SET
                    transmitted = 1,
                    transmitted_at = ?
                WHERE packet_id = ?
                """,
                (
                    datetime.now(
                        timezone.utc
                    ).isoformat(),

                    packet_id
                )
            )

            connection.commit()

            connection.close()

    def get_pending_packets(
        self,
        limit: int = 100
    ) -> List[Dict]:

        with self.lock:

            connection = (
                self._get_connection()
            )

            cursor = (
                connection.cursor()
            )

            cursor.execute(
                """
                SELECT *
                FROM outgoing_packets
                WHERE transmitted = 0
                ORDER BY id ASC
                LIMIT ?
                """,
                (
                    limit,
                )
            )

            rows = (
                cursor.fetchall()
            )

            connection.close()

        result = []

        for row in rows:

            result.append(
                {
                    "packet_id":
                        row["packet_id"],

                    "packet_type":
                        row["packet_type"],

                    "topic":
                        row["topic"],

                    "payload":
                        json.loads(
                            row["payload"]
                        )
                }
            )

        return result

#part 3
    def write_system_log(
        self,
        level: str,
        message: str
    ) -> None:

        with self.lock:

            connection = (
                self._get_connection()
            )

            cursor = (
                connection.cursor()
            )

            cursor.execute(
                """
                INSERT INTO system_logs
                (
                    level,
                    message,
                    created_at
                )
                VALUES
                (
                    ?, ?, ?
                )
                """,
                (
                    level,

                    message,

                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )
            )

            connection.commit()

            connection.close()

    def event_count(
        self
    ) -> int:

        with self.lock:

            connection = (
                self._get_connection()
            )

            cursor = (
                connection.cursor()
            )

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM events
                """
            )

            count = (
                cursor.fetchone()[0]
            )

            connection.close()

            return count

    def pending_packet_count(
        self
    ) -> int:

        with self.lock:

            connection = (
                self._get_connection()
            )

            cursor = (
                connection.cursor()
            )

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM outgoing_packets
                WHERE transmitted = 0
                """
            )

            count = (
                cursor.fetchone()[0]
            )

            connection.close()

            return count

    def latest_event(
        self
    ) -> Optional[Dict]:

        with self.lock:

            connection = (
                self._get_connection()
            )

            cursor = (
                connection.cursor()
            )

            cursor.execute(
                """
                SELECT *
                FROM events
                ORDER BY id DESC
                LIMIT 1
                """
            )

            row = (
                cursor.fetchone()
            )

            connection.close()

        if row is None:

            return None

        event = dict(row)

        if event.get(
            "waveform_json"
        ):

            try:

                event[
                    "waveform"
                ] = json.loads(
                    event[
                        "waveform_json"
                    ]
                )

            except Exception:

                event[
                    "waveform"
                ] = []

        return event

    def database_statistics(
        self
    ) -> Dict:

        return {

            "event_count":
                self.event_count(),

            "pending_packets":
                self.pending_packet_count(),

            "database_path":
                self.database_path
        }
