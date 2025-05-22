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
# Try multiple possible locations for the .env file
env_paths = [
    ROOT_DIR / '.env',                 # Project root .env
    ROOT_DIR / 'pylama' / '.env',      # pylama subdirectory .env
    Path(os.path.expanduser('~/.pylama/.env'))  # User home config
]

# Try to load from any available .env file
env_loaded = False
for env_path in env_paths:
    if env_path.exists():
        logger.info(f"Loading environment variables from {env_path}")
        load_dotenv(env_path)
        env_loaded = True
        break

if not env_loaded:
    logger.warning(f"No .env file found in any of these locations: {[str(p) for p in env_paths]}")
    logger.info(f"Using default configuration values")

# Directory for logs
LOGS_DIR = Path(os.environ.get('LOG_DIR', ROOT_DIR / "logs")).expanduser().resolve()

# Environment variable configuration with fallbacks
# Network configuration
DEFAULT_HOST = os.environ.get('HOST', "127.0.0.1")
DEBUG_MODE = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't', 'yes')

# Service ports - load from environment variables with fallbacks
DEFAULT_PORTS = {
    "pybox": int(os.environ.get('PYBOX_PORT', 9000)),
    "pyllm": int(os.environ.get('PYLLM_PORT', 9001)),
    "shellama": int(os.environ.get('SHELLAMA_PORT', 9002)),
    "pylama": int(os.environ.get('PYLAMA_PORT', 9003)),
    "apilama": int(os.environ.get('APILAMA_PORT', 9080)),
    "weblama": int(os.environ.get('WEBLAMA_PORT', 9081)),
}

# Path configurations
MARKDOWN_DIR = Path(os.environ.get('MARKDOWN_DIR', ROOT_DIR / "markdown")).expanduser().resolve()
API_URL = os.environ.get('API_URL', f"http://{DEFAULT_HOST}:{DEFAULT_PORTS['apilama']}")

# Auto-adjustment configuration
AUTO_ADJUST_PORTS = os.environ.get('AUTO_ADJUST_PORTS', 'True').lower() in ('true', '1', 't', 'yes')
PORT_INCREMENT = int(os.environ.get('PORT_INCREMENT', 10))

# Docker configuration
DOCKER_NETWORK = os.environ.get('DOCKER_NETWORK', 'pylama-network')
DOCKER_IMAGE_PREFIX = os.environ.get('DOCKER_IMAGE_PREFIX', 'pylama')

# Log the configuration
logger.info(f"Configuration loaded successfully")
logger.info(f"Host: {DEFAULT_HOST}")
logger.info(f"Debug mode: {DEBUG_MODE}")
logger.info(f"Ports: {DEFAULT_PORTS}")
logger.info(f"Logs directory: {LOGS_DIR}")
logger.info(f"Markdown directory: {MARKDOWN_DIR}")
logger.info(f"API URL: {API_URL}")
logger.info(f"Auto-adjust ports: {AUTO_ADJUST_PORTS}")
logger.info(f"Port increment: {PORT_INCREMENT}")
logger.info(f"Docker network: {DOCKER_NETWORK}")
logger.info(f"Docker image prefix: {DOCKER_IMAGE_PREFIX}")


def ensure_logs_dir():
    """
Ensure that the logs directory exists.
    """
    if not LOGS_DIR.exists():
        LOGS_DIR.mkdir(parents=True)
        logger.info(f"Created logs directory at {LOGS_DIR}")


def create_example_env_file(path=None):
    """
Create an example .env file with default configuration values.

Args:
    path: Path to create the example .env file. If None, creates it in the project root.
    """
    if path is None:
        path = ROOT_DIR / 'env.example'
    
    example_content = """# PyLama Ecosystem Configuration
# Copy this file to .env and modify as needed

# Network Configuration
HOST=127.0.0.1
DEBUG=False

# Service Ports
PYBOX_PORT=9000
PYLLM_PORT=9001
SHELLAMA_PORT=9002
PYLAMA_PORT=9003
APILAMA_PORT=9080
WEBLAMA_PORT=9081

# Path Configuration
LOG_DIR=./logs
MARKDOWN_DIR=./markdown
API_URL=http://127.0.0.1:9080

# Auto-adjustment Configuration
AUTO_ADJUST_PORTS=True
PORT_INCREMENT=10

# Docker Configuration
DOCKER_NETWORK=pylama-network
DOCKER_IMAGE_PREFIX=pylama
"""
    
    # Write the example .env file
    with open(path, 'w') as f:
        f.write(example_content)
    
    logger.info(f"Created example .env file at {path}")
    return path
