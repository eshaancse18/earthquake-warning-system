"""
Configuration Loader

Loads CRS configuration from YAML and provides a singleton
configuration object for the entire application.
"""

from pathlib import Path
from typing import Any, Dict

import yaml


class Config:
    """
    Loads configuration from config.yaml.
    """

    def __init__(self, path: str | Path):

        self.path = Path(path)

        if not self.path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.path}"
            )

        with open(self.path, "r", encoding="utf-8") as file:
            self._config: Dict[str, Any] = yaml.safe_load(file)

    def get(self, *keys, default=None):
        """
        Retrieve nested configuration values.

        Example:
            config.get("mqtt", "broker")
        """

        data = self._config

        for key in keys:

            if not isinstance(data, dict):
                return default

            data = data.get(key)

            if data is None:
                return default

        return data

    @property
    def data(self):
        return self._config


# ----------------------------------------------------------
# Singleton
# ----------------------------------------------------------

CONFIG_PATH = Path(__file__).parent / "config.yaml"

config = Config(CONFIG_PATH)