import csv
import json
import os
import threading
from datetime import datetime
from typing import Dict
from typing import List
from typing import Any


class WaveformStorage:
    """
    Waveform Storage Manager

    Responsibilities:
    ----------------
    1. Store complete waveform files
    2. Store event metadata
    3. Export CSV
    4. Export JSON
    5. Retrieve waveforms
    6. Manage storage directories

    Directory Layout:

    waveforms/

        YYYY/
            MM/
                DD/

                    event_id.csv
                    event_id.json
    """

    def __init__(
        self,
        base_directory: str
    ):

        self.base_directory = (
            os.path.abspath(
                base_directory
            )
        )

        self.lock = threading.Lock()

        os.makedirs(
            self.base_directory,
            exist_ok=True
        )

    def _event_directory(
        self,
        event_time: datetime
    ) -> str:

        year = (
            str(event_time.year)
        )

        month = (
            f"{event_time.month:02d}"
        )

        day = (
            f"{event_time.day:02d}"
        )

        directory = os.path.join(
            self.base_directory,
            year,
            month,
            day
        )

        os.makedirs(
            directory,
            exist_ok=True
        )

        return directory

    def save_json(
        self,
        event_id: str,
        event_time: datetime,
        event_record: Dict[str, Any]
    ) -> str:

        with self.lock:

            directory = (
                self._event_directory(
                    event_time
                )
            )

            filename = (
                f"{event_id}.json"
            )

            filepath = (
                os.path.join(
                    directory,
                    filename
                )
            )

            with open(
                filepath,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    event_record,
                    file,
                    indent=4,
                    default=str
                )

            return filepath

    def save_csv(
        self,
        event_id: str,
        event_time: datetime,
        waveform: List[Dict]
    ) -> str:

        with self.lock:

            directory = (
                self._event_directory(
                    event_time
                )
            )

            filename = (
                f"{event_id}.csv"
            )

            filepath = (
                os.path.join(
                    directory,
                    filename
                )
            )

            with open(
                filepath,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(
                    file
                )

                writer.writerow(
                    [
                        "timestamp",
                        "value"
                    ]
                )

                for sample in waveform:

                    writer.writerow(
                        [
                            sample.get(
                                "timestamp"
                            ),
                            sample.get(
                                "value"
                            )
                        ]
                    )

            return filepath

    def save_event(
        self,
        event_record: Dict[str, Any]
    ) -> Dict[str, str]:

        event_id = (
            event_record[
                "event_id"
            ]
        )

        start_time_string = (
            event_record[
                "event_start_time"
            ]
        )

        event_time = (
            datetime.fromisoformat(
                start_time_string
            )
        )

        waveform = (
            event_record[
                "waveform"
            ]
        )

        json_path = (
            self.save_json(
                event_id,
                event_time,
                event_record
            )
        )

        csv_path = (
            self.save_csv(
                event_id,
                event_time,
                waveform
            )
        )

        return {
            "json_path":
                json_path,

            "csv_path":
                csv_path
        }

    def load_event_json(
        self,
        filepath: str
    ) -> Dict:

        with open(
            filepath,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(
                file
            )

    def list_waveforms(
        self
    ) -> List[str]:

        files = []

        for root, _, filenames in os.walk(
            self.base_directory
        ):

            for filename in filenames:

                if (
                    filename.endswith(
                        ".json"
                    )
                ):

                    files.append(
                        os.path.join(
                            root,
                            filename
                        )
                    )

        files.sort()

        return files

    def storage_usage_bytes(
        self
    ) -> int:

        total = 0

        for root, _, files in os.walk(
            self.base_directory
        ):

            for file in files:

                filepath = (
                    os.path.join(
                        root,
                        file
                    )
                )

                if os.path.isfile(
                    filepath
                ):

                    total += (
                        os.path.getsize(
                            filepath
                        )
                    )

        return total

    def statistics(
        self
    ) -> Dict:

        waveform_count = len(
            self.list_waveforms()
        )

        storage_bytes = (
            self.storage_usage_bytes()
        )

        return {
            "waveform_count":
                waveform_count,

            "storage_bytes":
                storage_bytes
        }