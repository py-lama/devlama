#!/usr/bin/env python3

"""
Service utilities for the DevLama ecosystem.

This module contains functions for starting, stopping, and monitoring services.
"""

import os
import signal
import time
import subprocess
import logging
import psutil

from .config import LOGS_DIR, DEFAULT_PORTS, DEFAULT_HOST, ensure_logs_dir
from .port_utils import is_port_in_use

logger = logging.getLogger(__name__)

# Dictionary to keep track of running processes
processes = {}


def start_service(service, service_dir, port, host):
    """
Start a service.
    """
    logger.info(f"Starting {service} on port {port}...")
    
    # Check if port is in use
    if is_port_in_use(host, port):
        logger.warning(f"Port {port} is already in use. {service} may not start correctly.")
    
    os.chdir(service_dir)
    
    # Install dependencies if needed
    subprocess.run(["pip", "install", "-e", "."], check=False)
    
    # Start the service
    if service == "bexy":
        cmd = ["python", "-m", "bexy", "serve", "--port", str(port)]
    elif service == "getllm":
        cmd = ["python", "-m", "getllm", "serve", "--port", str(port)]
    elif service == "shellama":
        cmd = ["python", "-m", "shellama", "serve", "--port", str(port)]
    elif service == "apilama":
        cmd = ["python", "-m", "apilama.app", "--port", str(port), "--host", host]
    elif service == "devlama":
        cmd = ["python", "-m", "devlama", "serve", "--port", str(port)]
    elif service == "weblama":
        # For WebLama, we need to set the API_URL environment variable
        # to point to the APILama service
        api_port = DEFAULT_PORTS['apilama']
        env = os.environ.copy()
        env['API_URL'] = f"http://{host}:{api_port}"
        env['PORT'] = str(port)
        env['HOST'] = host
        logger.info(f"Setting WebLama API_URL to {env['API_URL']}")
        cmd = ["npm", "start"]
    else:
        logger.error(f"Unknown service: {service}")
        return
    
    # Create log file
    log_file = LOGS_DIR / f"{service}.log"
    with open(log_file, "a") as f:
        # Start the process
        if service == "weblama":
            # Use the environment variables we set for WebLama
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid,  # Create a new process group
                env=env,  # Use the environment with API_URL set
                cwd=service_dir  # Ensure we're in the right directory
            )
        else:
            # For other services, use the standard approach
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid,  # Create a new process group
            )
    
    # Save the PID
    pid_file = LOGS_DIR / f"{service}.pid"
    with open(pid_file, "w") as f:
        f.write(str(process.pid))
    
    # Save the process in the dictionary
    processes[service] = process
    
    logger.info(f"{service} started with PID {process.pid}")
    logger.info(f"Logs available at {log_file}")


def stop_service(service):
    """
Stop a service.
    """
    pid_file = LOGS_DIR / f"{service}.pid"
    if pid_file.exists():
        try:
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())
            
            logger.info(f"Stopping {service} (PID: {pid})...")
            try:
                # First try to terminate the process group
                try:
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                except (ProcessLookupError, OSError):
                    logger.warning(f"Process group for {pid} not found. Trying direct process termination.")
                    # Fallback to terminating just the process
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except (ProcessLookupError, OSError):
                        logger.warning(f"Process {pid} not found. It may have already terminated.")
            except Exception as e:
                logger.error(f"Error stopping {service}: {e}")
        except Exception as e:
            logger.error(f"Error reading PID file for {service}: {e}")
        
        # Remove PID file regardless of whether termination was successful
        try:
            pid_file.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Error removing PID file for {service}: {e}")
        
        # Remove from processes dictionary
        if service in processes:
            try:
                del processes[service]
            except Exception as e:
                logger.error(f"Error removing {service} from processes dictionary: {e}")
        
        logger.info(f"{service} stopped")
    else:
        logger.warning(f"{service} is not running")


def get_ecosystem_status():
    """
Get the status of all services in the DevLama ecosystem.
    """
    ensure_logs_dir()
    
    status = {}
    for service in DEFAULT_PORTS.keys():
        port = DEFAULT_PORTS[service]
        host = DEFAULT_HOST
        pid_file = LOGS_DIR / f"{service}.pid"
        
        # First check if the port is in use (service might be running even if PID file is stale)
        port_in_use = is_port_in_use(host, port)
        
        if port_in_use:
            # Port is in use, service is likely running
            pid = None
            if pid_file.exists():
                try:
                    with open(pid_file, "r") as f:
                        pid = int(f.read().strip())
                except Exception as e:
                    logger.warning(f"Error reading PID file for {service}: {e}")
            
            if pid:
                status[service] = {"status": "running", "pid": pid, "port": port}
            else:
                # Port is in use but we don't know the PID
                status[service] = {"status": "running", "note": f"Port {port} is in use, but PID is unknown", "port": port}
        else:
            # Port is not in use, check if there's a PID file
            if pid_file.exists():
                try:
                    with open(pid_file, "r") as f:
                        pid = int(f.read().strip())
                    
                    # Check if the process with this PID exists
                    try:
                        # First try using psutil
                        try:
                            process = psutil.Process(pid)
                            if process.is_running():
                                # Process exists but port is not in use - might be starting up or wrong port
                                status[service] = {"status": "starting", "pid": pid, "note": f"Process exists but port {port} is not in use"}
                            else:
                                status[service] = {"status": "not running", "pid": pid, "note": "stale PID file"}
                        except (psutil.NoSuchProcess, AttributeError):
                            # Fallback to checking process existence using os.kill with signal 0
                            try:
                                os.kill(pid, 0)
                                # Process exists but port is not in use
                                status[service] = {"status": "starting", "pid": pid, "note": f"Process exists but port {port} is not in use"}
                            except OSError:
                                status[service] = {"status": "not running", "pid": pid, "note": "stale PID file"}
                    except Exception as e:
                        logger.warning(f"Error checking process status for {service}: {e}")
                        status[service] = {"status": "unknown", "pid": pid, "note": str(e)}
                except Exception as e:
                    logger.warning(f"Error reading PID file for {service}: {e}")
                    status[service] = {"status": "unknown", "note": "invalid PID file"}
            else:
                status[service] = {"status": "not running"}
    
    return status


def print_ecosystem_status():
    """
Print the status of all services in the DevLama ecosystem.
    """
    logger.info("DevLama Ecosystem Status:")
    
    status = get_ecosystem_status()
    for service, info in status.items():
        if info["status"] == "running":
            if "pid" in info:
                logger.info(f"{service}: Running (PID: {info['pid']})")
            else:
                logger.info(f"{service}: Running ({info.get('note', 'Port in use')})")
        elif info["status"] == "starting":
            logger.info(f"{service}: Starting (PID: {info['pid']}, {info.get('note', '')})")
        elif info["status"] == "not running" and "note" in info:
            logger.warning(f"{service}: Not running ({info['note']})")
        elif info["status"] == "not running":
            logger.info(f"{service}: Not running")
        elif info["status"] == "unknown":
            logger.warning(f"{service}: Status unknown ({info['note']})")
        else:
            logger.info(f"{service}: {info['status']} {info.get('note', '')}")
    
    # Print Docker container status
    logger.info("\nDocker Container Status:")
    try:
        # Try to get Docker container status
        result = subprocess.run(["docker", "ps", "--format", "table {{.Names}}\t{{.Image}}\t{{.Command}}\t{{.Service}}\t{{.CreatedAt}}\t{{.Status}}\t{{.Ports}}"], 
                              capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(result.stdout)
        else:
            # Fallback to docker-compose ps
            try:
                from .config import ROOT_DIR
                compose_result = subprocess.run(["docker-compose", "ps"], cwd=ROOT_DIR, capture_output=True, text=True, check=False)
                print(compose_result.stdout)
            except Exception as compose_error:
                logger.error(f"Error getting docker-compose status: {compose_error}")
    except Exception as e:
        logger.error(f"Error getting Docker container status: {e}")


def view_service_logs(service):
    """
View logs for a specific service.
    """
    ensure_logs_dir()
    
    log_file = LOGS_DIR / f"{service}.log"
    if not log_file.exists():
        logger.error(f"No logs found for {service}")
        return
    
    logger.info(f"=== Showing logs for {service} ===")
    logger.info("Press Ctrl+C to exit")
    
    try:
        # Use tail to follow the log file
        subprocess.run(["tail", "-f", str(log_file)])
    except KeyboardInterrupt:
        logger.info("Stopped viewing logs")
