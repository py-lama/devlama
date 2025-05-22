#!/usr/bin/env python3

"""
Command-line interface for the PyLama ecosystem.

This module provides the command-line interface for managing the PyLama ecosystem.
"""

import argparse
import logging

from .ecosystem_manager import start_ecosystem, stop_ecosystem, open_weblama_in_browser
from .service_utils import print_ecosystem_status, view_service_logs

logger = logging.getLogger(__name__)


def main():
    """
Main function for the ecosystem management CLI.
    """
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
    start_parser.add_argument("--auto-adjust-ports", action="store_true", help="Automatically adjust ports if they are in use", default=True)
    start_parser.add_argument("--no-auto-adjust-ports", action="store_false", dest="auto_adjust_ports", help="Do not automatically adjust ports if they are in use")
    
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
    restart_parser.add_argument("--open", action="store_true", help="Open WebLama in browser after restarting")
    restart_parser.add_argument("--browser", action="store_true", help="Alias for --open, opens WebLama in browser")
    restart_parser.add_argument("--auto-adjust-ports", action="store_true", help="Automatically adjust ports if they are in use", default=True)
    restart_parser.add_argument("--no-auto-adjust-ports", action="store_false", dest="auto_adjust_ports", help="Do not automatically adjust ports if they are in use")
    
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
    
    logger.info("Application started")
    
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
        
        # Check if browser should be opened
        open_browser = args.open or args.browser
        
        # Stop and then start the ecosystem
        stop_ecosystem(components, args.docker)
        import time
        time.sleep(2)
        start_ecosystem(components, args.docker, open_browser, args.auto_adjust_ports)
    
    elif args.command == "status":
        print_ecosystem_status()
    
    elif args.command == "logs":
        view_service_logs(args.service)
    
    elif args.command == "open":
        # Use custom host/port if provided, otherwise use defaults
        host = args.host if args.host is not None else None  # Will use default in open_weblama_in_browser
        port = args.port if args.port is not None else None  # Will use default in open_weblama_in_browser
        
        # Open WebLama in browser
        open_weblama_in_browser(host, port)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
