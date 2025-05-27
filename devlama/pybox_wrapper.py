#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wrapper for bexy functionality to handle import issues.

This module provides a clean interface to the bexy package classes
regardless of how the package is installed or structured.
"""

import os
import sys
import importlib.util
from typing import Dict, Any

# Add parent directory to sys.path to find bexy package
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Check if bexy/bexy/python_sandbox.py exists and import directly
python_sandbox_path = os.path.join(parent_dir, 'bexy', 'bexy', 'python_sandbox.py')
docker_sandbox_path = os.path.join(parent_dir, 'bexy', 'bexy', 'docker_sandbox.py')

# Import PythonSandbox
if os.path.exists(python_sandbox_path):
    # Import directly from the file
    spec = importlib.util.spec_from_file_location("bexy.python_sandbox", python_sandbox_path)
    python_sandbox_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(python_sandbox_module)
    
    # Get the class we need
    PythonSandbox = python_sandbox_module.PythonSandbox
else:
    # Fallback implementation if the module can't be found
    class PythonSandbox:
        """Fallback implementation of PythonSandbox."""
        def __init__(self):
            pass
        
        def run(self, code: str) -> Dict[str, Any]:
            """Run Python code in a sandbox."""
            return {
                "output": "Error: PythonSandbox module not found.",
                "error": "Module not found"
            }

# Import DockerSandbox
if os.path.exists(docker_sandbox_path):
    # Import directly from the file
    spec = importlib.util.spec_from_file_location("bexy.docker_sandbox", docker_sandbox_path)
    docker_sandbox_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(docker_sandbox_module)
    
    # Get the class we need
    DockerSandbox = docker_sandbox_module.DockerSandbox
else:
    # Fallback implementation if the module can't be found
    class DockerSandbox:
        """Fallback implementation of DockerSandbox."""
        def __init__(self):
            pass
        
        def run(self, code: str) -> Dict[str, Any]:
            """Run Python code in a Docker sandbox."""
            return {
                "output": "Error: DockerSandbox module not found.",
                "error": "Module not found"
            }
