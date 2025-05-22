#!/usr/bin/env python3

"""
Ecosystem manager for the PyLama ecosystem.

This module contains functions for starting and stopping the entire PyLama ecosystem.
"""

import time
import subprocess
import logging
import webbrowser

from .config import (ROOT_DIR, DEFAULT_HOST, DEFAULT_PORTS, ensure_logs_dir,
                 DEBUG_MODE, AUTO_ADJUST_PORTS, PORT_INCREMENT, API_URL,
                 DOCKER_NETWORK, DOCKER_IMAGE_PREFIX, create_example_env_file)
from .port_utils import is_port_in_use, find_available_ports_for_all_services, check_service_availability
from .service_utils import start_service, stop_service, get_ecosystem_status

logger = logging.getLogger(__name__)


def open_weblama_in_browser(host=None, port=None):
    """
Open WebLama in the default web browser.
    """
    host = host or DEFAULT_HOST
    port = port or DEFAULT_PORTS['weblama']
    
    url = f"http://{host}:{port}"
    logger.info(f"Opening WebLama in browser at {url}")
    try:
        webbrowser.open(url)
        return True
    except Exception as e:
        logger.error(f"Error opening WebLama in browser: {e}")
        return False


def initialize_configuration():
    """
Initialize the PyLama ecosystem configuration.

This function ensures that all necessary directories exist and configuration files are available.
    """
    # Ensure logs directory exists
    ensure_logs_dir()
    
    # Create example .env file if it doesn't exist
    env_example_path = ROOT_DIR / 'env.example'
    if not env_example_path.exists():
        create_example_env_file(env_example_path)
        logger.info(f"Created example configuration file at {env_example_path}")
        logger.info(f"Copy this file to .env and modify as needed")
    
    # Log debug information if in debug mode
    if DEBUG_MODE:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")


def start_ecosystem(components=None, use_docker=False, open_browser=False, auto_adjust_ports=None):
    """
Start the PyLama ecosystem.

Args:
    components: List of components to start. If None, starts all components.
    use_docker: Whether to use Docker to start the ecosystem.
    open_browser: Whether to open WebLama in the browser after starting.
    auto_adjust_ports: Whether to automatically adjust ports if they are in use.
                       If None, uses the value from the environment configuration.
    """
    # Initialize configuration
    initialize_configuration()
    
    # Use environment configuration if auto_adjust_ports is not specified
    if auto_adjust_ports is None:
        auto_adjust_ports = AUTO_ADJUST_PORTS
        logger.info(f"Using auto_adjust_ports={auto_adjust_ports} from environment configuration")
    
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
                
                # Find available ports for all services using the configured PORT_INCREMENT
                logger.info(f"Using port increment of {PORT_INCREMENT} from configuration")
                new_ports = find_available_ports_for_all_services(DEFAULT_PORTS, DEFAULT_HOST, port_increment=PORT_INCREMENT)
                if new_ports:
                    logger.info(f"Using new ports: {new_ports}")
                    # Update ports dictionary with new values
                    for service, port in new_ports.items():
                        DEFAULT_PORTS[service] = port
                    logger.info(f"Updated ports configuration: {DEFAULT_PORTS}")
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
    if components is None:
        components = DEFAULT_PORTS.keys()
    
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
    """
Stop the PyLama ecosystem.
    """
    if use_docker:
        logger.info("Stopping PyLama ecosystem using Docker...")
        subprocess.run(["docker-compose", "down"], cwd=ROOT_DIR)
        logger.info("Docker containers stopped")
        return
    
    # Default to all components if none specified
    if components is None:
        components = DEFAULT_PORTS.keys()
    
    # Stop services in reverse order
    service_order = ["weblama", "pylama", "apilama", "shellama", "pyllm", "pybox"]
    for service in service_order:
        if service not in components:
            continue
        
        stop_service(service)
