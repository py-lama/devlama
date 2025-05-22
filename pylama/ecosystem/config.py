#!/usr/bin/env python3

"""
Configuration for the PyLama ecosystem.

This module contains constants and configuration-related functions for the PyLama ecosystem.
"""

import os
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)7s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Root directory of the PyLama project
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))).resolve()

# Directory for logs
LOGS_DIR = ROOT_DIR / "logs"

# Default host and ports for services
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORTS = {
    "pybox": 9000,
    "pyllm": 9001,
    "shellama": 9002,
    "pylama": 9003,
    "apilama": 9080,
    "weblama": 9081,
}


def ensure_logs_dir():
    """
Ensure that the logs directory exists.
    """
    if not LOGS_DIR.exists():
        LOGS_DIR.mkdir(parents=True)
        logger.info(f"Created logs directory at {LOGS_DIR}")
