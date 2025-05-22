#!/usr/bin/env python3

"""
Configuration for the PyLama ecosystem.

This module contains constants and configuration-related functions for the PyLama ecosystem.
"""

import os
import logging
from pathlib import Path

# Try to import dotenv for environment variable loading
try:
    from dotenv import load_dotenv
except ImportError:
    try:
        from python_dotenv import load_dotenv
    except ImportError:
        # If dotenv is not available, define a dummy function
        def load_dotenv(path=None):
            logging.warning("python-dotenv package not found, environment variables from .env will not be loaded")
            pass

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)7s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Root directory of the PyLama project
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))).resolve()

# Load environment variables from .env file
env_path = ROOT_DIR / 'pylama' / '.env'
if env_path.exists():
    logger.info(f"Loading environment variables from {env_path}")
    load_dotenv(env_path)
else:
    logger.warning(f"No .env file found at {env_path}")

# Directory for logs
LOGS_DIR = Path(os.environ.get('LOG_DIR', ROOT_DIR / "logs")).expanduser().resolve()

# Default host and ports for services - load from environment variables with fallbacks
DEFAULT_HOST = os.environ.get('HOST', "127.0.0.1")

# Load ports from environment variables with fallbacks
DEFAULT_PORTS = {
    "pybox": int(os.environ.get('PYBOX_PORT', 9000)),
    "pyllm": int(os.environ.get('PYLLM_PORT', 9001)),
    "shellama": int(os.environ.get('SHELLAMA_PORT', 9002)),
    "pylama": int(os.environ.get('PYLAMA_PORT', 9003)),
    "apilama": int(os.environ.get('APILAMA_PORT', 9080)),
    "weblama": int(os.environ.get('WEBLAMA_PORT', 9081)),
}

# Log the configuration
logger.info(f"Using host: {DEFAULT_HOST}")
logger.info(f"Using ports: {DEFAULT_PORTS}")


def ensure_logs_dir():
    """
Ensure that the logs directory exists.
    """
    if not LOGS_DIR.exists():
        LOGS_DIR.mkdir(parents=True)
        logger.info(f"Created logs directory at {LOGS_DIR}")
