#!/usr/bin/env python3

"""
Log management for the PyLama ecosystem.

This module contains functions for collecting and viewing logs from all PyLama components.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Optional, Union, Any

# Initialize logging with PyLogs
from devlama.ecosystem.logging_config import init_logging, get_logger

# Initialize logging first, before any other imports
init_logging()

# Get a logger for this module
logger = get_logger('log_manager')

from .config import ROOT_DIR, ensure_logs_dir


def find_loglama():
    """
    Find the LogLama package and add it to the Python path if necessary.
    
    Returns:
        bool: True if LogLama was found, False otherwise.
    """
    # Check if loglama is already in the path
    try:
        import loglama
        return True
    except ImportError:
        pass
    
    # Try to find loglama in the standard location
    loglama_path = Path(ROOT_DIR) / 'loglama'
    
    if loglama_path.exists() and str(loglama_path) not in sys.path:
        sys.path.insert(0, str(loglama_path))
        try:
            import loglama
            return True
        except ImportError:
            pass
    
    return False


def collect_logs(components: Optional[List[str]] = None, verbose: bool = False) -> Dict[str, int]:
    """
    Collect logs from PyLama components and import them into LogLama.
    
    Args:
        components: List of components to collect logs from. If None, collects from all components.
        verbose: Whether to show verbose output.
        
    Returns:
        Dict mapping component names to the number of log records imported.
    """
    # Check if LogLama is available
    if not find_loglama():
        logger.error("LogLama not found. Cannot collect logs.")
        return {}
    
    try:
        # Import LogLama modules
        from loglama.collectors.log_collector import collect_logs_from_component, collect_all_logs
        
        # Collect logs
        if components:
            # Collect logs from specified components
            results = {}
            for component in components:
                count = collect_logs_from_component(component)
                results[component] = count
                if verbose:
                    logger.info(f"Collected {count} logs from {component}")
        else:
            # Collect logs from all components
            results = collect_all_logs()
            
            if verbose:
                for component, count in results.items():
                    logger.info(f"Collected {count} logs from {component}")
        
        # Log summary
        total_count = sum(results.values())
        logger.info(f"Collected {total_count} logs from {len(results)} components")
        
        return results
    
    except Exception as e:
        logger.exception(f"Error collecting logs: {e}")
        return {}


def start_log_collector(components: Optional[List[str]] = None, interval: int = 300, 
                       verbose: bool = False, background: bool = True) -> bool:
    """
    Start the LogLama log collector for PyLama components.
    
    Args:
        components: List of components to collect logs from. If None, collects from all components.
        interval: Collection interval in seconds.
        verbose: Whether to show verbose output.
        background: Whether to run in the background.
        
    Returns:
        bool: True if the collector was started successfully, False otherwise.
    """
    # Check if LogLama is available
    if not find_loglama():
        logger.error("LogLama not found. Cannot start log collector.")
        return False
    
    try:
        # Import LogLama modules
        from loglama.collectors.scheduled_collector import run_collector
        from loglama.config.env_loader import get_env
        
        if background:
            # Run in the background using subprocess
            cmd = [sys.executable, '-m', 'loglama.collectors.scheduled_collector']
            
            # Add components if specified
            if components:
                cmd.extend(['--components'] + components)
            
            # Add other arguments
            cmd.extend(['--interval', str(interval)])
            if verbose:
                cmd.append('--verbose')
            
            # Create log directory if it doesn't exist
            ensure_logs_dir()
            log_dir = Path(get_env('LOGLAMA_LOG_DIR', os.path.join(ROOT_DIR, 'logs')))
            log_dir.mkdir(exist_ok=True)
            
            # Open log file
            log_file = open(log_dir / 'collector.log', 'a')
            
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=log_file,
                close_fds=True,
                start_new_session=True
            )
            
            # Log success message
            logger.info(f"Started log collector with PID {process.pid}")
            logger.info(f"Logs are being written to {log_dir / 'collector.log'}")
            
            # Write PID to file for later management
            with open(log_dir / 'collector.pid', 'w') as f:
                f.write(str(process.pid))
            
            return True
        else:
            # Run in the foreground
            logger.info(f"Starting log collector for {', '.join(components) if components else 'all components'}")
            logger.info(f"Collection interval: {interval} seconds")
            
            # Run the collector
            run_collector(components=components, interval=interval, verbose=verbose)
            return True
    
    except Exception as e:
        logger.exception(f"Error starting log collector: {e}")
        return False


def stop_log_collector() -> bool:
    """
    Stop the LogLama log collector if it's running.
    
    Returns:
        bool: True if the collector was stopped successfully, False otherwise.
    """
    # Check if LogLama is available
    if not find_loglama():
        logger.error("LogLama not found. Cannot stop log collector.")
        return False
    
    try:
        # Import LogLama modules
        from loglama.config.env_loader import get_env
        
        # Check if the collector is running
        log_dir = Path(get_env('LOGLAMA_LOG_DIR', os.path.join(ROOT_DIR, 'logs')))
        pid_file = log_dir / 'collector.pid'
        
        if not pid_file.exists():
            logger.info("Log collector is not running.")
            return True
        
        # Read the PID from the file
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Try to kill the process
        try:
            import signal
            os.kill(pid, signal.SIGTERM)
            logger.info(f"Stopped log collector with PID {pid}")
            
            # Remove the PID file
            pid_file.unlink()
            
            return True
        except ProcessLookupError:
            logger.warning(f"Log collector process with PID {pid} not found. It may have already stopped.")
            
            # Remove the PID file
            pid_file.unlink()
            
            return True
        except Exception as e:
            logger.error(f"Error stopping log collector: {e}")
            return False
    
    except Exception as e:
        logger.exception(f"Error stopping log collector: {e}")
        return False


def view_logs(component: Optional[str] = None, level: Optional[str] = None, 
              limit: int = 50, json_output: bool = False) -> bool:
    """
    View logs from LogLama.
    
    Args:
        component: Component to filter logs by. If None, shows logs from all components.
        level: Log level to filter by. If None, shows logs of all levels.
        limit: Maximum number of logs to display.
        json_output: Whether to output in JSON format.
        
    Returns:
        bool: True if logs were displayed successfully, False otherwise.
    """
    # Check if LogLama is available
    if not find_loglama():
        logger.error("LogLama not found. Cannot view logs.")
        return False
    
    try:
        # Build the command to run the LogLama CLI
        cmd = [sys.executable, '-m', 'loglama.cli.main', 'logs']
        
        # Add filters
        if component:
            cmd.extend(['--logger-name', component])
        if level:
            cmd.extend(['--level', level.upper()])
        
        # Add other options
        cmd.extend(['--limit', str(limit)])
        if json_output:
            cmd.append('--json-output')
        
        # Run the command
        subprocess.run(cmd)
        
        return True
    
    except Exception as e:
        logger.exception(f"Error viewing logs: {e}")
        return False
