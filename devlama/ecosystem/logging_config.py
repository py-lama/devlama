#!/usr/bin/env python3

"""
DevLama Logging Configuration

This module configures logging for DevLama using the PyLogs package.
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
    from loglama.utils import configure_logging, LogContext, capture_context
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
    Initialize logging for DevLama using PyLogs.
    
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
    log_dir = get_env('PYLAMA_LOG_DIR', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs'))
    db_enabled = get_env('PYLAMA_DB_LOGGING', 'true').lower() in ('true', 'yes', '1')
    db_path = get_env('DEVLAMA_DB_PATH', os.path.join(log_dir, 'devlama.db'))
    json_format = get_env('PYLAMA_JSON_LOGS', 'false').lower() in ('true', 'yes', '1')
    
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Ensure database table exists before logging starts
    if db_enabled:
        try:
            from loglama.handlers.sqlite_handler import SQLiteHandler
            handler = SQLiteHandler(db_path)
            # The handler will create the table in its __init__ method
            # We don't need to keep this handler, as configure_logging will create its own
            del handler
        except Exception as e:
            print(f"Error initializing database for logging: {e}")
    
    # Configure logging
    logger = configure_logging(
        name='devlama',
        level=log_level,
        console=True,
        file=True,
        file_path=os.path.join(log_dir, 'devlama.log'),
        database=db_enabled,
        db_path=db_path,
        json=json_format,
        context_filter=True
    )
    
    # Log initialization
    logger.info('DevLama logging initialized with PyLogs')
    return True


def get_logger(name=None):
    """
    Get a logger instance.
    
    Args:
        name (str, optional): Name of the logger. Defaults to 'devlama'.
        
    Returns:
        Logger: A configured logger instance.
    """
    if not name:
        name = 'devlama'
    elif not name.startswith('devlama.'):
        name = f'devlama.{name}'
    
    if LOGLAMA_AVAILABLE:
        from loglama import get_logger as loglama_get_logger
        return loglama_get_logger(name)
    else:
        return logging.getLogger(name)


def log_service_context(service_name=None, port=None, host=None):
    """
    Context manager for adding service context to logs.
    
    Args:
        service_name (str, optional): Name of the service.
        port (int, optional): Port the service is running on.
        host (str, optional): Host the service is running on.
        
    Returns:
        Context manager that adds service context to logs.
    """
    if not LOGLAMA_AVAILABLE:
        # Return a dummy context manager if PyLogs is not available
        class DummyContext:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        return DummyContext()
    
    context = {}
    if service_name:
        context['service'] = service_name
    if port:
        context['port'] = port
    if host:
        context['host'] = host
    
    return LogContext(**context)


def log_service_operation(service, operation, success=True, error=None):
    """
    Log a service operation.
    
    Args:
        service (str): The service that performed the operation.
        operation (str): The operation that was performed.
        success (bool, optional): Whether the operation was successful. Defaults to True.
        error (str, optional): The error message if the operation failed. Defaults to None.
    """
    logger = get_logger(f'devlama.services.{service}')
    
    if success:
        logger.info(f'{service} {operation} successful')
    else:
        logger.error(f'{service} {operation} failed: {error}')
