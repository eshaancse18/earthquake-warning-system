"""
Centralized Logging System for CRS.

This module provides a singleton logger that writes logs to both
the console and a rotating log file.
"""

from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

from config.config import config


class CRSLogger:
    """
    Creates and manages the CRS logger.
    """

    _logger = None

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """
        Returns the singleton logger instance.
        """

        if cls._logger is not None:
            return cls._logger

        logger = logging.getLogger("CRS")

        logger.setLevel(logging.INFO)

        logger.propagate = False

        # Prevent duplicate handlers
        if logger.handlers:
            return logger

        # --------------------------------------------------
        # Create log directory
        # --------------------------------------------------

        log_directory = Path(
            config.get(
                "storage",
                "log_directory"
            )
        )

        log_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        log_file = log_directory / "crs.log"

        # --------------------------------------------------
        # Formatter
        # --------------------------------------------------

        formatter = logging.Formatter(
            fmt=(
                "%(asctime)s | "
                "%(levelname)-8s | "
                "%(name)s | "
                "%(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # --------------------------------------------------
        # Console Handler
        # --------------------------------------------------

        console_handler = logging.StreamHandler()

        console_handler.setLevel(logging.INFO)

        console_handler.setFormatter(formatter)

        # --------------------------------------------------
        # Rotating File Handler
        # --------------------------------------------------

        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )

        file_handler.setLevel(logging.INFO)

        file_handler.setFormatter(formatter)

        # --------------------------------------------------
        # Add Handlers
        # --------------------------------------------------

        logger.addHandler(console_handler)

        logger.addHandler(file_handler)

        cls._logger = logger

        return logger


logger = CRSLogger.get_logger()