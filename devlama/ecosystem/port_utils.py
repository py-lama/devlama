#!/usr/bin/env python3

"""
Port utilities for the PyLama ecosystem.

This module contains functions for checking port availability and finding available ports.
"""

import socket
import logging

logger = logging.getLogger(__name__)


def is_port_in_use(host, port):
    """
Check if a port is in use.
    """
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
    """
Check if a port is available.
    """
    return not is_port_in_use(host, port)


def check_service_availability(service, host, port):
    """
Check if a service is available via HTTP.
    """
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
    """
Find an available port by incrementing the base port by the specified increment until an available port is found.
    """
    port = base_port
    
    # Try up to 10 increments (e.g., 9080, 9090, 9100, ...)
    for _ in range(10):
        if check_port_available(host, port):
            return port
        port += increment
    
    # If we couldn't find an available port, return None
    logger.error(f"Could not find an available port starting from {base_port}")
    return None


def find_available_ports_for_all_services(ports_dict, host='127.0.0.1', port_increment=10):
    """
Find available ports for all services by incrementing all ports by the same amount.
    """
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
        increment_amount = i * port_increment
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
