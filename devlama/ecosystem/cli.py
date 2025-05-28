#!/usr/bin/env python3

"""
Command-line interface for the DevLama ecosystem.

This module provides the command-line interface for managing the DevLama ecosystem.
"""

import argparse
import logging

from .ecosystem_manager import start_ecosystem, stop_ecosystem, open_weblama_in_browser
from .service_utils import print_ecosystem_status, view_service_logs
from .log_manager import collect_logs, start_log_collector, stop_log_collector, view_logs

logger = logging.getLogger(__name__)


def main():
    """
Main function for the ecosystem management CLI.
    """
    parser = argparse.ArgumentParser(description="DevLama Ecosystem Management")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start the DevLama ecosystem")
    start_parser.add_argument("--docker", action="store_true", help="Use Docker to start the ecosystem")
    start_parser.add_argument("--bexy", action="store_true", help="Start BEXY")
    start_parser.add_argument("--getllm", action="store_true", help="Start PyLLM")
    start_parser.add_argument("--shellama", action="store_true", help="Start SheLLama")
    start_parser.add_argument("--apilama", action="store_true", help="Start APILama")
    start_parser.add_argument("--devlama", action="store_true", help="Start DevLama")
    start_parser.add_argument("--weblama", action="store_true", help="Start WebLama")
    start_parser.add_argument("--open", action="store_true", help="Open WebLama in browser after starting")
    start_parser.add_argument("--browser", action="store_true", help="Alias for --open, opens WebLama in browser")
    start_parser.add_argument("--auto-adjust-ports", action="store_true", help="Automatically adjust ports if they are in use", default=True)
    start_parser.add_argument("--no-auto-adjust-ports", action="store_false", dest="auto_adjust_ports", help="Do not automatically adjust ports if they are in use")
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop the DevLama ecosystem")
    stop_parser.add_argument("--docker", action="store_true", help="Use Docker to stop the ecosystem")
    stop_parser.add_argument("--bexy", action="store_true", help="Stop BEXY")
    stop_parser.add_argument("--getllm", action="store_true", help="Stop PyLLM")
    stop_parser.add_argument("--shellama", action="store_true", help="Stop SheLLama")
    stop_parser.add_argument("--apilama", action="store_true", help="Stop APILama")
    stop_parser.add_argument("--devlama", action="store_true", help="Stop DevLama")
    stop_parser.add_argument("--weblama", action="store_true", help="Stop WebLama")
    
    # Restart command
    restart_parser = subparsers.add_parser("restart", help="Restart the DevLama ecosystem")
    restart_parser.add_argument("--docker", action="store_true", help="Use Docker to restart the ecosystem")
    restart_parser.add_argument("--bexy", action="store_true", help="Restart BEXY")
    restart_parser.add_argument("--getllm", action="store_true", help="Restart PyLLM")
    restart_parser.add_argument("--shellama", action="store_true", help="Restart SheLLama")
    restart_parser.add_argument("--apilama", action="store_true", help="Restart APILama")
    restart_parser.add_argument("--devlama", action="store_true", help="Restart DevLama")
    restart_parser.add_argument("--weblama", action="store_true", help="Restart WebLama")
    restart_parser.add_argument("--open", action="store_true", help="Open WebLama in browser after restarting")
    restart_parser.add_argument("--browser", action="store_true", help="Alias for --open, opens WebLama in browser")
    restart_parser.add_argument("--auto-adjust-ports", action="store_true", help="Automatically adjust ports if they are in use", default=True)
    restart_parser.add_argument("--no-auto-adjust-ports", action="store_false", dest="auto_adjust_ports", help="Do not automatically adjust ports if they are in use")
    
    # Status command
    subparsers.add_parser("status", help="Show the status of the DevLama ecosystem")
    
    # Logs command
    logs_parser = subparsers.add_parser("logs", help="View logs for a service")
    logs_parser.add_argument("service", choices=["bexy", "getllm", "shellama", "apilama", "devlama", "weblama", "all"],
                           help="Service to view logs for (use 'all' to view logs from all services)")
    logs_parser.add_argument("--level", choices=["debug", "info", "warning", "error", "critical"],
                           help="Filter logs by level")
    logs_parser.add_argument("--limit", type=int, default=50,
                           help="Maximum number of logs to display")
    logs_parser.add_argument("--json", action="store_true",
                           help="Output logs in JSON format")
    
    # Collect logs command
    collect_parser = subparsers.add_parser("collect-logs", help="Collect logs from services and import them into LogLama")
    collect_parser.add_argument("--services", nargs="+",
                              choices=["bexy", "getllm", "shellama", "apilama", "pylama", "weblama"],
                              help="Services to collect logs from (default: all)")
    collect_parser.add_argument("--verbose", "-v", action="store_true",
                              help="Show verbose output")
    
    # Log collector daemon commands
    collector_parser = subparsers.add_parser("log-collector", help="Manage the log collector daemon")
    collector_subparsers = collector_parser.add_subparsers(dest="collector_command", help="Log collector command")
    
    # Start log collector command
    start_collector_parser = collector_subparsers.add_parser("start", help="Start the log collector daemon")
    start_collector_parser.add_argument("--services", nargs="+",
                                      choices=["bexy", "getllm", "shellama", "apilama", "devlama", "weblama"],
                                      help="Services to collect logs from (default: all)")
    start_collector_parser.add_argument("--interval", "-i", type=int, default=300,
                                      help="Collection interval in seconds (default: 300)")
    start_collector_parser.add_argument("--verbose", "-v", action="store_true",
                                      help="Show verbose output")
    start_collector_parser.add_argument("--foreground", "-f", action="store_true",
                                      help="Run in the foreground instead of as a daemon")
    
    # Stop log collector command
    collector_subparsers.add_parser("stop", help="Stop the log collector daemon")
    
    # Status log collector command
    collector_subparsers.add_parser("status", help="Check the status of the log collector daemon")
    
    # Open command
    open_parser = subparsers.add_parser("open", help="Open WebLama in a web browser")
    open_parser.add_argument("--port", type=int, help="Custom port to use (default: 9081)")
    open_parser.add_argument("--host", type=str, help="Custom host to use (default: 127.0.0.1)")
    
    args = parser.parse_args()
    
    logger.info("Application started")
    
    if args.command == "start":
        # Check if specific components are specified
        components = []
        if args.bexy:
            components.append("bexy")
        if args.getllm:
            components.append("getllm")
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
        if args.bexy:
            components.append("bexy")
        if args.getllm:
            components.append("getllm")
        if args.shellama:
            components.append("shellama")
        if args.apilama:
            components.append("apilama")
        if args.devlama:
            components.append("devlama")
        if args.weblama:
            components.append("weblama")
        
        # If no specific components are specified, stop all
        if not components:
            components = None
        
        stop_ecosystem(components, args.docker)
    
    elif args.command == "restart":
        # Check if specific components are specified
        components = []
        if args.bexy:
            components.append("bexy")
        if args.getllm:
            components.append("getllm")
        if args.shellama:
            components.append("shellama")
        if args.apilama:
            components.append("apilama")
        if args.devlama:
            components.append("devlama")
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
        if args.service == "all":
            # Use LogLama to view logs from all services
            view_logs(component=None, level=args.level, limit=args.limit, json_output=args.json)
        else:
            # Use the traditional service log viewer for individual services
            view_service_logs(args.service)
    
    elif args.command == "collect-logs":
        # Collect logs from services and import them into LogLama
        services = args.services if args.services else None
        results = collect_logs(components=services, verbose=args.verbose)
        
        # Print results
        if results:
            total_count = sum(results.values())
            print(f"Collected {total_count} logs from {len(results)} services:")
            for service, count in results.items():
                print(f"  {service}: {count} records")
        else:
            print("No logs were collected. Make sure LogLama is installed and configured properly.")
    
    elif args.command == "log-collector":
        # Handle log collector commands
        if args.collector_command == "start":
            # Start the log collector
            services = args.services if args.services else None
            success = start_log_collector(
                components=services,
                interval=args.interval,
                verbose=args.verbose,
                background=not args.foreground
            )
            
            if success:
                if not args.foreground:
                    print("Log collector started successfully in the background.")
                    print("Logs are being collected from all DevLama components.")
            else:
                print("Failed to start log collector. Make sure LogLama is installed and configured properly.")
        
        elif args.collector_command == "stop":
            # Stop the log collector
            success = stop_log_collector()
            
            if success:
                print("Log collector stopped successfully.")
            else:
                print("Failed to stop log collector. It may not be running or there was an error.")
        
        elif args.collector_command == "status":
            # Check the status of the log collector
            import os
            from pathlib import Path
            from .config import ROOT_DIR
            
            # Try to find the PID file
            log_dir = Path(os.path.join(ROOT_DIR, 'logs'))
            pid_file = log_dir / 'collector.pid'
            
            if pid_file.exists():
                # Read the PID from the file
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Check if the process is running
                try:
                    os.kill(pid, 0)  # Signal 0 doesn't kill the process, just checks if it exists
                    print(f"Log collector is running with PID {pid}")
                except OSError:
                    print("Log collector is not running (stale PID file)")
            else:
                print("Log collector is not running")
        
        else:
            print("Please specify a log collector command: start, stop, or status")
    
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
