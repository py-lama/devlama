#!/usr/bin/env python3

"""
Pylama Logging Configuration

This module configures logging for Pylama using the PyLogs package.
It ensures that environment variables are loaded before any other libraries.
"""

import os
import sys
import logging
from pathlib import Path

# Add the loglama package to the path if it's not already installed
loglama_path = Path(__file__).parent.parent.parent.parent / 'loglama'
if loglama_path.exists() and str(loglama_path) not in sys.path:
    sys.path.insert(0, str(loglama_path))

# Import PyLogs components
try:
    from loglama.config.env_loader import load_env, get_env
    from loglama.utils import configure_logging
    from loglama.utils.context import LogContext, capture_context
    from loglama.formatters import ColoredFormatter, JSONFormatter
    from loglama.handlers import SQLiteHandler, EnhancedRotatingFileHandler
    LOGLAMA_AVAILABLE = True
except ImportError as e:
    print(f"PyLogs import error: {e}")
    LOGLAMA_AVAILABLE = False

# Set up basic logging as a fallback
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)7s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def init_logging():
    """
    Initialize logging for Pylama using PyLogs.
    
    This function should be called at the very beginning of the application
    before any other imports or configurations are done.
    """
    if not LOGLAMA_AVAILABLE:
        print("PyLogs package not available. Using default logging configuration.")
        return False
    
    # Load environment variables from .env files
    load_env(verbose=True)
    
    # Get logging configuration from environment variables
    log_level = get_env('PYLAMA_LOG_LEVEL', 'INFO')
    log_dir = get_env('PYLAMA_LOG_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs'))
    db_enabled = get_env('PYLAMA_DB_LOGGING', 'true').lower() in ('true', 'yes', '1')
    db_path = get_env('PYLAMA_DB_PATH', os.path.join(log_dir, 'pylama.db'))
    json_format = get_env('PYLAMA_JSON_LOGS', 'false').lower() in ('true', 'yes', '1')
    
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logger = configure_logging(
        name='pylama',
        level=log_level,
        console=True,
        file=True,
        file_path=os.path.join(log_dir, 'pylama.log'),
        database=db_enabled,
        db_path=db_path,
        json=json_format,
        context_filter=True
    )
    
    # Log initialization
    logger.info('Pylama logging initialized with PyLogs')
    return True


def get_logger(name=None):
    """
    Get a logger instance.
    
    Args:
        name (str, optional): Name of the logger. Defaults to 'pylama'.
        
    Returns:
        Logger: A configured logger instance.
    """
    if not name:
        name = 'pylama'
    elif not name.startswith('pylama.'):
        name = f'pylama.{name}'
    
    if LOGLAMA_AVAILABLE:
        from loglama import get_logger as loglama_get_logger
        return loglama_get_logger(name)
    else:
        return logging.getLogger(name)
