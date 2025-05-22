#!/usr/bin/env python3

import os
import sys
import subprocess
import signal
import time
import logging
import psutil
from pathlib import Path
import socket

def is_port_in_use(host, port):
    """Check if a port is in use."""
    try:
        # Check if port is in use using socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result == 0  # If result is 0, connection succeeded, port is in use
    except Exception as e:
        logger.error(f"Error checking if port {port} is in use: {e}")
        return False  # Assume port is not in use if check fails

def check_port_available(host, port):
    """Check if a port is available."""
    return not is_port_in_use(host, port)

def check_service_availability(service, host, port):
    """Check if a service is available via HTTP."""
    import requests
    url = f"http://{host}:{port}"
    try:
        response = requests.get(url, timeout=2)
        logger.info(f"Service {service} is available at {url} with status code {response.status_code}")
        return True
    except requests.RequestException as e:
        logger.warning(f"Service {service} is not available at {url}: {e}")
        return False

def find_available_port(base_port, host='127.0.0.1', increment=10):
    """Find an available port by incrementing the base port by the specified increment until an available port is found."""
    port = base_port
    
    # Try up to 10 increments (e.g., 9080, 9090, 9100, ...)
    for _ in range(10):
        if check_port_available(host, port):
            return port
        port += increment
    
    # If we couldn't find an available port, return None
    logger.error(f"Could not find an available port starting from {base_port}")
    return None

def find_available_ports_for_all_services(ports_dict=None, host='127.0.0.1', increment=10):
    """Find available ports for all services by incrementing all ports by the same amount."""
    # Use provided ports_dict or get it from the global DEFAULT_PORTS later in the code
    if ports_dict is None:
        # This will be set to DEFAULT_PORTS when the function is called
        ports_dict = {}
    
    # Check if any ports are in use
    busy_ports = []
    for service, port in ports_dict.items():
        if is_port_in_use(host, port):
            busy_ports.append((service, port))
    
    if not busy_ports:
        # All ports are available, no need to change
        return ports_dict.copy()
    
    # Some ports are busy, try incrementing all ports by the same amount
    for i in range(1, 10):  # Try up to 9 increments
        new_ports = {}
        increment_amount = i * increment
        all_available = True
        
        for service, port in ports_dict.items():
            new_port = port + increment_amount
            if not check_port_available(host, new_port):
                all_available = False
                break
            new_ports[service] = new_port
        
        if all_available:
            logger.info(f"Found available ports for all services by incrementing by {increment_amount}")
            return new_ports
    
    # If we couldn't find available ports for all services, return None
    logger.error("Could not find available ports for all services")
    return None

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
    if is_port_in_use(host, port):
        logger.warning(f"Port {port} is already in use. {service} may not start correctly.")
    
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


def start_ecosystem(components=None, use_docker=False, open_browser=False, auto_adjust_ports=True):
    """Start the PyLama ecosystem."""
    ensure_logs_dir()
    
    # Check if any ports are in use and stop Docker containers if needed
    if auto_adjust_ports:
        busy_ports = []
        for service, port in DEFAULT_PORTS.items():
            if is_port_in_use(DEFAULT_HOST, port):
                busy_ports.append((service, port))
        
        if busy_ports:
            logger.warning(f"The following ports are already in use: {busy_ports}")
            
            # Try to stop Docker containers if they might be using the ports
            try:
                logger.info("Stopping Docker containers that might be using the ports...")
                subprocess.run(["docker-compose", "down"], cwd=ROOT_DIR, check=False)
                time.sleep(2)  # Wait for containers to stop
            except Exception as e:
                logger.error(f"Error stopping Docker containers: {e}")
            
            # Check again after stopping Docker
            still_busy = []
            for service, port in busy_ports:
                if is_port_in_use(DEFAULT_HOST, port):
                    still_busy.append((service, port))
            
            if still_busy:
                logger.warning(f"The following ports are still in use after stopping Docker: {still_busy}")
                
                # Find available ports for all services
                new_ports = find_available_ports_for_all_services(DEFAULT_PORTS, DEFAULT_HOST)
                if new_ports:
                    logger.info(f"Using new ports: {new_ports}")
                    # Update ports dictionary with new values
                    for service, port in new_ports.items():
                        DEFAULT_PORTS[service] = port
                else:
                    logger.error("Could not find available ports. Some services may fail to start.")
    
    if use_docker:
        logger.info("Starting PyLama ecosystem using Docker...")
        # Update docker-compose.yml with new ports if needed
        if auto_adjust_ports and 'new_ports' in locals() and new_ports:
            # TODO: Update docker-compose.yml with new ports
            pass
        
        subprocess.run(["docker-compose", "up", "-d"], cwd=ROOT_DIR)
        logger.info(f"Docker containers started. Access WebLama at http://{DEFAULT_HOST}:{DEFAULT_PORTS['weblama']}")
        
        # Open browser if requested
        if open_browser:
            # Wait a moment for services to start
            time.sleep(3)
            open_weblama_in_browser()
        
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
    started_services = []
    
    for service in service_order:
        if service not in components:
            continue
        
        service_dir = ROOT_DIR / service
        if not service_dir.exists():
            logger.error(f"Directory for {service} not found at {service_dir}")
            continue
        
        port = DEFAULT_PORTS[service]
        start_service(service, service_dir, port, DEFAULT_HOST)
        started_services.append(service)
        time.sleep(2)  # Wait for the service to start
    
    # Check if services are actually available via HTTP for web services
    web_services = ["apilama", "weblama"]
    available_services = []
    
    # Wait a bit longer for services to fully initialize
    time.sleep(3)
    
    for service in started_services:
        if service in web_services:
            port = DEFAULT_PORTS[service]
            if check_service_availability(service, DEFAULT_HOST, port):
                available_services.append(service)
            else:
                logger.warning(f"{service} was started but is not responding on port {port}")
        else:
            # For non-web services, just check if the process is running
            status = get_ecosystem_status()
            if service in status and status[service]["status"] == "running":
                available_services.append(service)
            else:
                logger.warning(f"{service} was started but is not running")
    
    # Print summary
    if available_services:
        logger.info(f"Services available: {', '.join(available_services)}")
    else:
        logger.warning("No services are available")
    
    logger.info(f"Selected services started. Access WebLama at http://{DEFAULT_HOST}:{DEFAULT_PORTS['weblama']}")
    
    # Open browser if requested and WebLama is among the started components
    if open_browser and "weblama" in components and "weblama" in available_services:
        # WebLama is available, open it in browser
        open_weblama_in_browser()
    elif open_browser and "weblama" in components:
        logger.warning("WebLama is not available, cannot open in browser")


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
    """Print the status of all services in the PyLama ecosystem."""
    logger.info("PyLama Ecosystem Status:")
    
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
                compose_result = subprocess.run(["docker-compose", "ps"], cwd=ROOT_DIR, capture_output=True, text=True, check=False)
                print(compose_result.stdout)
            except Exception as compose_error:
                logger.error(f"Error getting docker-compose status: {compose_error}")
    except Exception as e:
        logger.error(f"Error getting Docker container status: {e}")


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


def open_weblama_in_browser():
    """Open WebLama in the default web browser."""
    import webbrowser
    url = f"http://{DEFAULT_HOST}:{DEFAULT_PORTS['weblama']}"
    logger.info(f"Opening WebLama in browser at {url}")
    try:
        webbrowser.open(url)
        return True
    except Exception as e:
        logger.error(f"Error opening WebLama in browser: {e}")
        return False


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
    start_parser.add_argument("--open", action="store_true", help="Open WebLama in browser after starting")
    start_parser.add_argument("--browser", action="store_true", help="Alias for --open, opens WebLama in browser")
    
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
    
    # Open command
    open_parser = subparsers.add_parser("open", help="Open WebLama in a web browser")
    open_parser.add_argument("--port", type=int, help="Custom port to use (default: 9081)")
    open_parser.add_argument("--host", type=str, help="Custom host to use (default: 127.0.0.1)")
    
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
        
        # Check if browser should be opened
        open_browser = args.open or args.browser
        
        # Start the ecosystem with port auto-adjustment if enabled
        start_ecosystem(components, args.docker, open_browser, args.auto_adjust_ports)
    
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
    
    elif args.command == "open":
        # Use custom host/port if provided, otherwise use defaults
        host = args.host if args.host is not None else DEFAULT_HOST
        port = args.port if args.port is not None else DEFAULT_PORTS['weblama']
        
        # Open WebLama in browser with custom host/port if provided
        url = f"http://{host}:{port}"
        logger.info(f"Opening WebLama in browser at {url}")
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            logger.error(f"Error opening WebLama in browser: {e}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
