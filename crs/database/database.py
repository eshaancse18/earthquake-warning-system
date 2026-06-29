"""
SQLite Database Manager
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from database.models import TABLES
from logging_system.logger import logger


class DatabaseManager:

    def __init__(self):

        db_path = Path("earthquake.db")

        self.connection = sqlite3.connect(
            db_path,
            check_same_thread=False
        )

        self.connection.row_factory = sqlite3.Row

        self.initialize_database()

    # --------------------------------------------------

    def initialize_database(self):

        cursor = self.connection.cursor()

        for table in TABLES:

            cursor.execute(table)

        self.connection.commit()

        logger.info("SQLite database initialized.")

    # --------------------------------------------------

    def execute(
        self,
        query,
        params=()
    ):

        cursor = self.connection.cursor()

        cursor.execute(query, params)

        self.connection.commit()

        return cursor

    # --------------------------------------------------

    def fetch_one(
        self,
        query,
        params=()
    ):

        cursor = self.connection.cursor()

        cursor.execute(query, params)

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    # --------------------------------------------------

    def fetch_all(
        self,
        query,
        params=()
    ):

        cursor = self.connection.cursor()

        cursor.execute(query, params)

        rows = cursor.fetchall()

        return [

            dict(row)

            for row in rows

        ]


database = DatabaseManager()