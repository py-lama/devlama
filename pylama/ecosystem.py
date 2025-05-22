#!/usr/bin/env python3

import os
import sys
import subprocess
import signal
import time
import logging
import psutil
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)7s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Default ports
DEFAULT_PORTS = {
    "pybox": 9000,
    "pyllm": 9001,
    "shellama": 9002,
    "pylama": 9003,
    "apilama": 9080,
    "weblama": 9081,
}

# Default host
DEFAULT_HOST = "127.0.0.1"

# Path to the root directory of the PyLama ecosystem
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Dictionary to store process information
processes = {}

# Logs directory
LOGS_DIR = ROOT_DIR / "logs"


def ensure_logs_dir():
    """Ensure the logs directory exists."""
    os.makedirs(LOGS_DIR, exist_ok=True)


def check_venv(service_dir):
    """Check if a virtual environment exists for the service."""
    venv_path = service_dir / "venv"
    dot_venv_path = service_dir / ".venv"
    
    if venv_path.exists() and (venv_path / "bin" / "activate").exists():
        return venv_path
    elif dot_venv_path.exists() and (dot_venv_path / "bin" / "activate").exists():
        return dot_venv_path
    return None


def install_dependencies(service, service_dir):
    """Install dependencies for a service."""
    logger.info(f"Installing dependencies for {service}...")
    
    os.chdir(service_dir)
    
    # Check if requirements.txt exists
    if (service_dir / "requirements.txt").exists():
        venv_path = check_venv(service_dir)
        if venv_path:
            logger.info(f"Installing dependencies from requirements.txt for {service}...")
            subprocess.run(f"source {venv_path}/bin/activate && pip install -r requirements.txt && pip install -e . && deactivate", 
                          shell=True, executable="/bin/bash")
        else:
            logger.warning(f"No virtual environment found for {service}. Skipping dependency installation.")
    else:
        logger.warning(f"No requirements.txt found for {service}. Skipping dependency installation.")
    
    # Return to the original directory
    os.chdir(ROOT_DIR)


def start_service(service, service_dir, port, host):
    """Start a service."""
    logger.info(f"Starting {service} on port {port}...")
    
    # Check if port is in use
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    logger.warning(f"Port {port} is already in use by PID {proc.pid}. {service} may not start correctly.")
                    break
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
    
    os.chdir(service_dir)
    
    # Install dependencies if needed
    if service != "weblama":  # Skip for weblama as it's Node.js
        venv_path = check_venv(service_dir)
        if venv_path:
            subprocess.run(f"source {venv_path}/bin/activate && pip install -e . && deactivate", 
                          shell=True, executable="/bin/bash", stderr=subprocess.DEVNULL)
    
    # Prepare the command to start the service
    if service == "weblama":
        cmd = f"node ./bin/weblama-cli.js start --port {port} --api-url http://{host}:{DEFAULT_PORTS['apilama']}"
    else:
        venv_path = check_venv(service_dir)
        if venv_path:
            cmd = f"source {venv_path}/bin/activate && python -m {service}.app --port {port} --host {host}"
        else:
            logger.warning(f"No virtual environment found for {service}. Using system Python.")
            cmd = f"python -m {service}.app --port {port} --host {host}"
    
    # Start the service in the background
    log_file = LOGS_DIR / f"{service}.log"
    process = subprocess.Popen(
        cmd,
        shell=True,
        executable="/bin/bash",
        stdout=open(log_file, "w"),
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid,
    )
    
    # Store the process information
    processes[service] = {
        "pid": process.pid,
        "process": process,
        "log_file": log_file,
    }
    
    # Write PID to file
    with open(LOGS_DIR / f"{service}.pid", "w") as f:
        f.write(str(process.pid))
    
    # Return to the original directory
    os.chdir(ROOT_DIR)
    
    logger.info(f"{service} started with PID {process.pid}")
    logger.info(f"Logs available at {log_file}")
    return process.pid


def stop_service(service):
    """Stop a service."""
    pid_file = LOGS_DIR / f"{service}.pid"
    if pid_file.exists():
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        
        logger.info(f"Stopping {service} (PID: {pid})...")
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except ProcessLookupError:
            logger.warning(f"Process {pid} not found. It may have already terminated.")
        except Exception as e:
            logger.error(f"Error stopping {service}: {e}")
        
        # Remove PID file
        pid_file.unlink(missing_ok=True)
        
        # Remove from processes dictionary
        if service in processes:
            del processes[service]
        
        logger.info(f"{service} stopped")
    else:
        logger.warning(f"{service} is not running")


def start_ecosystem(components=None, use_docker=False):
    """Start the PyLama ecosystem."""
    ensure_logs_dir()
    
    if use_docker:
        logger.info("Starting PyLama ecosystem using Docker...")
        subprocess.run(["docker-compose", "up", "-d"], cwd=ROOT_DIR)
        logger.info("Docker containers started. Access WebLama at http://localhost:9081")
        return
    
    # Default to all components if none specified
    if not components:
        components = ["pybox", "pyllm", "shellama", "apilama", "pylama", "weblama"]
    
    # Install dependencies for all services first
    logger.info("Installing dependencies for selected services...")
    for service in components:
        if service not in DEFAULT_PORTS:
            logger.warning(f"Unknown service: {service}. Skipping.")
            continue
        
        service_dir = ROOT_DIR / service
        if not service_dir.exists():
            logger.error(f"Directory for {service} not found at {service_dir}")
            continue
        
        install_dependencies(service, service_dir)
    
    # Install Node.js dependencies for WebLama if needed
    if "weblama" in components:
        weblama_dir = ROOT_DIR / "weblama"
        if weblama_dir.exists():
            logger.info("Installing dependencies for WebLama...")
            os.chdir(weblama_dir)
            subprocess.run(["npm", "install", "--silent"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.chdir(ROOT_DIR)
    
    # Start services in the correct order
    service_order = ["pybox", "pyllm", "shellama", "apilama", "pylama", "weblama"]
    for service in service_order:
        if service not in components:
            continue
        
        service_dir = ROOT_DIR / service
        if not service_dir.exists():
            logger.error(f"Directory for {service} not found at {service_dir}")
            continue
        
        start_service(service, service_dir, DEFAULT_PORTS[service], DEFAULT_HOST)
        time.sleep(2)  # Wait for the service to start
    
    logger.info(f"Selected services started. Access WebLama at http://{DEFAULT_HOST}:{DEFAULT_PORTS['weblama']}")


def stop_ecosystem(components=None, use_docker=False):
    """Stop the PyLama ecosystem."""
    if use_docker:
        logger.info("Stopping PyLama ecosystem Docker containers...")
        subprocess.run(["docker-compose", "down"], cwd=ROOT_DIR)
        logger.info("Docker containers stopped")
        return
    
    # Default to all components if none specified
    if not components:
        components = ["weblama", "pylama", "apilama", "shellama", "pyllm", "pybox"]
    
    # Stop services in reverse order
    for service in components:
        if service not in DEFAULT_PORTS:
            logger.warning(f"Unknown service: {service}. Skipping.")
            continue
        
        stop_service(service)
    
    logger.info("Selected services stopped")


def get_ecosystem_status():
    """Get the status of all services in the PyLama ecosystem."""
    ensure_logs_dir()
    
    status = {}
    for service in DEFAULT_PORTS.keys():
        pid_file = LOGS_DIR / f"{service}.pid"
        if pid_file.exists():
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())
            
            # Check if the process is running
            try:
                process = psutil.Process(pid)
                if process.is_running():
                    status[service] = {"status": "running", "pid": pid}
                else:
                    status[service] = {"status": "not running", "pid": pid, "note": "stale PID file"}
            except psutil.NoSuchProcess:
                status[service] = {"status": "not running", "pid": pid, "note": "stale PID file"}
        else:
            status[service] = {"status": "not running"}
    
    return status


def print_ecosystem_status():
    """Print the status of all services in the PyLama ecosystem."""
    status = get_ecosystem_status()
    
    logger.info("PyLama Ecosystem Status:")
    for service, info in status.items():
        status_str = info["status"]
        if status_str == "running":
            logger.info(f"{service}: Running (PID: {info['pid']})")
        else:
            note = info.get("note", "")
            if note:
                logger.warning(f"{service}: Not running ({note})")
            else:
                logger.warning(f"{service}: Not running")
    
    # Check Docker status
    try:
        subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        logger.info("\nDocker Container Status:")
        subprocess.run(["docker-compose", "ps"], cwd=ROOT_DIR)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass


def view_service_logs(service):
    """View logs for a specific service."""
    ensure_logs_dir()
    
    if service not in DEFAULT_PORTS:
        logger.error(f"Unknown service: {service}")
        return
    
    log_file = LOGS_DIR / f"{service}.log"
    if not log_file.exists():
        logger.warning(f"No log file found for {service}")
        # Create an empty log file
        with open(log_file, "w") as f:
            pass
    
    logger.info(f"=== Showing logs for {service} ===")
    logger.info("Press Ctrl+C to exit")
    
    try:
        subprocess.run(["tail", "-f", str(log_file)])
    except KeyboardInterrupt:
        logger.info("Stopped viewing logs")


def main():
    """Main function for the ecosystem management CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="PyLama Ecosystem Management")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start the PyLama ecosystem")
    start_parser.add_argument("--docker", action="store_true", help="Use Docker to start the ecosystem")
    start_parser.add_argument("--pybox", action="store_true", help="Start PyBox")
    start_parser.add_argument("--pyllm", action="store_true", help="Start PyLLM")
    start_parser.add_argument("--shellama", action="store_true", help="Start SheLLama")
    start_parser.add_argument("--apilama", action="store_true", help="Start APILama")
    start_parser.add_argument("--pylama", action="store_true", help="Start PyLama")
    start_parser.add_argument("--weblama", action="store_true", help="Start WebLama")
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop the PyLama ecosystem")
    stop_parser.add_argument("--docker", action="store_true", help="Use Docker to stop the ecosystem")
    stop_parser.add_argument("--pybox", action="store_true", help="Stop PyBox")
    stop_parser.add_argument("--pyllm", action="store_true", help="Stop PyLLM")
    stop_parser.add_argument("--shellama", action="store_true", help="Stop SheLLama")
    stop_parser.add_argument("--apilama", action="store_true", help="Stop APILama")
    stop_parser.add_argument("--pylama", action="store_true", help="Stop PyLama")
    stop_parser.add_argument("--weblama", action="store_true", help="Stop WebLama")
    
    # Restart command
    restart_parser = subparsers.add_parser("restart", help="Restart the PyLama ecosystem")
    restart_parser.add_argument("--docker", action="store_true", help="Use Docker to restart the ecosystem")
    restart_parser.add_argument("--pybox", action="store_true", help="Restart PyBox")
    restart_parser.add_argument("--pyllm", action="store_true", help="Restart PyLLM")
    restart_parser.add_argument("--shellama", action="store_true", help="Restart SheLLama")
    restart_parser.add_argument("--apilama", action="store_true", help="Restart APILama")
    restart_parser.add_argument("--pylama", action="store_true", help="Restart PyLama")
    restart_parser.add_argument("--weblama", action="store_true", help="Restart WebLama")
    
    # Status command
    subparsers.add_parser("status", help="Show the status of the PyLama ecosystem")
    
    # Logs command
    logs_parser = subparsers.add_parser("logs", help="View logs for a service")
    logs_parser.add_argument("service", choices=["pybox", "pyllm", "shellama", "apilama", "pylama", "weblama"],
                           help="Service to view logs for")
    
    args = parser.parse_args()
    
    if args.command == "start":
        # Check if specific components are specified
        components = []
        if args.pybox:
            components.append("pybox")
        if args.pyllm:
            components.append("pyllm")
        if args.shellama:
            components.append("shellama")
        if args.apilama:
            components.append("apilama")
        if args.pylama:
            components.append("pylama")
        if args.weblama:
            components.append("weblama")
        
        # If no specific components are specified, start all
        if not components:
            components = None
        
        start_ecosystem(components, args.docker)
    
    elif args.command == "stop":
        # Check if specific components are specified
        components = []
        if args.pybox:
            components.append("pybox")
        if args.pyllm:
            components.append("pyllm")
        if args.shellama:
            components.append("shellama")
        if args.apilama:
            components.append("apilama")
        if args.pylama:
            components.append("pylama")
        if args.weblama:
            components.append("weblama")
        
        # If no specific components are specified, stop all
        if not components:
            components = None
        
        stop_ecosystem(components, args.docker)
    
    elif args.command == "restart":
        # Check if specific components are specified
        components = []
        if args.pybox:
            components.append("pybox")
        if args.pyllm:
            components.append("pyllm")
        if args.shellama:
            components.append("shellama")
        if args.apilama:
            components.append("apilama")
        if args.pylama:
            components.append("pylama")
        if args.weblama:
            components.append("weblama")
        
        # If no specific components are specified, restart all
        if not components:
            components = None
        
        stop_ecosystem(components, args.docker)
        time.sleep(2)
        start_ecosystem(components, args.docker)
    
    elif args.command == "status":
        print_ecosystem_status()
    
    elif args.command == "logs":
        view_service_logs(args.service)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
