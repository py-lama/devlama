#!/usr/bin/env python3

"""
Configuration for the DevLama ecosystem.

This module contains constants and configuration-related functions for the DevLama ecosystem.
"""

# Initialize logging first, before any other imports
# This ensures environment variables are loaded before other libraries
from devlama.ecosystem.logging_config import init_logging, get_logger

# Initialize logging with PyLogs
init_logging()

# Now import other standard libraries
import os
from pathlib import Path

# Get the logger
logger = get_logger('ecosystem.config')

# Root directory of the DevLama project
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))).resolve()

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
    "devlama": int(os.environ.get('DEVLAMA_PORT', 9003)),
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
DOCKER_NETWORK = os.environ.get('DOCKER_NETWORK', 'devlama-network')
DOCKER_IMAGE_PREFIX = os.environ.get('DOCKER_IMAGE_PREFIX', 'devlama')

# Log the configuration with structured context
logger.info("DevLama configuration loaded", extra={
    'context': {
        'host': DEFAULT_HOST,
        'debug_mode': DEBUG_MODE,
        'ports': DEFAULT_PORTS,
        'logs_dir': str(LOGS_DIR),
        'markdown_dir': str(MARKDOWN_DIR),
        'api_url': API_URL,
        'auto_adjust_ports': AUTO_ADJUST_PORTS,
        'port_increment': PORT_INCREMENT,
        'docker_network': DOCKER_NETWORK,
        'docker_image_prefix': DOCKER_IMAGE_PREFIX
    }
})


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
    
    example_content = """# DevLama Ecosystem Configuration
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
DOCKER_NETWORK=devlama-network
DOCKER_IMAGE_PREFIX=devlama
"""
    
    # Write the example .env file
    with open(path, 'w') as f:
        f.write(example_content)
    
    logger.info(f"Created example .env file at {path}")
    return path
