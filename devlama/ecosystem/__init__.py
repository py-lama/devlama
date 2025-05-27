#!/usr/bin/env python3

"""
DevLama Ecosystem Management Module.

This package provides functionality for managing the DevLama ecosystem,
including starting, stopping, and monitoring services.
"""

from .config import (
    ROOT_DIR,
    LOGS_DIR,
    DEFAULT_HOST,
    DEFAULT_PORTS,
    ensure_logs_dir
)

from .port_utils import (
    is_port_in_use,
    check_port_available,
    check_service_availability,
    find_available_port,
    find_available_ports_for_all_services
)

from .service_utils import (
    start_service,
    stop_service,
    get_ecosystem_status,
    print_ecosystem_status,
    view_service_logs
)

from .ecosystem_manager import (
    start_ecosystem,
    stop_ecosystem,
    open_weblama_in_browser
)

from .cli import main

__all__ = [
    'ROOT_DIR',
    'LOGS_DIR',
    'DEFAULT_HOST',
    'DEFAULT_PORTS',
    'ensure_logs_dir',
    'is_port_in_use',
    'check_port_available',
    'check_service_availability',
    'find_available_port',
    'find_available_ports_for_all_services',
    'start_service',
    'stop_service',
    'get_ecosystem_status',
    'print_ecosystem_status',
    'view_service_logs',
    'start_ecosystem',
    'stop_ecosystem',
    'open_weblama_in_browser',
    'main'
]
