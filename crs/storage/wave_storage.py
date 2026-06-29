"""
Waveform Storage

Stores waveform recordings associated with
earthquake events.

Waveforms are stored on disk as compressed
NumPy archives (.npz), while only the file
path is kept in the database.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict

import numpy as np

from config.config import config
from logging_system.logger import logger


class WaveformStorage:
    """
    Handles storage of waveform data.
    """

    def __init__(self) -> None:

        self.storage_directory = Path(
            config.get(
                "storage",
                "waveform_directory"
            )
        )

        self.storage_directory.mkdir(
            parents=True,
            exist_ok=True
        )

    # --------------------------------------------------

    def save_waveform(
        self,
        station_id: str,
        waveform: Dict[str, np.ndarray]
    ) -> str:
        """
        Save waveform to disk.

        Parameters
        ----------
        station_id
            SSN identifier.

        waveform
            Dictionary containing waveform arrays.

            Example:
            {
                "x": np.array(...),
                "y": np.array(...),
                "z": np.array(...),
                "magnitude": np.array(...)
            }

        Returns
        -------
        str
            Absolute path of saved waveform.
        """

        timestamp = datetime.utcnow().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        filename = (
            f"{station_id}_{timestamp}.npz"
        )

        filepath = (
            self.storage_directory /
            filename
        )

        np.savez_compressed(

            filepath,

            **waveform

        )

        logger.info(
            f"Waveform stored: {filepath}"
        )

        return str(filepath)

    # --------------------------------------------------

    def load_waveform(
        self,
        filepath: str
    ) -> Dict[str, np.ndarray]:
        """
        Load waveform from disk.
        """

        archive = np.load(filepath)

        return {

            key: archive[key]

            for key in archive.files

        }

    # --------------------------------------------------

    def exists(
        self,
        filepath: str
    ) -> bool:

        return Path(filepath).exists()

    # --------------------------------------------------

    def delete(
        self,
        filepath: str
    ) -> None:

        path = Path(filepath)

        if path.exists():

            path.unlink()

            logger.info(
                f"Deleted waveform {filepath}"
            )


waveform_storage = WaveformStorage()