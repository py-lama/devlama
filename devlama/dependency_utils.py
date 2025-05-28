# -*- coding: utf-8 -*-

"""
Dependency utilities for PyLama.

This module provides functions for checking and installing dependencies.
"""

import importlib
import logging
import sys
from typing import List, Tuple

from .DependencyManager import DependencyManager

logger = logging.getLogger('devlama.dependency_utils')


def check_dependencies(modules: List[str]) -> Tuple[List[str], List[str]]:
    """
    Check which dependencies are already installed and which are missing.
    
    Args:
        modules: List of module names to check
        
    Returns:
        Tuple of (installed_modules, missing_modules)
    """
    return DependencyManager.check_dependencies(modules)


def install_dependencies(packages: List[str]) -> bool:
    """
    Install missing dependencies.
    
    Args:
        packages: List of package names to install
        
    Returns:
        True if all packages were installed successfully, False otherwise
    """
    return DependencyManager.install_dependencies(packages)


def extract_imports(code: str) -> List[str]:
    """
    Extract imported modules from code.
    
    Args:
        code: Python code to analyze
        
    Returns:
        List of module names imported in the code
    """
    return DependencyManager.extract_imports(code)
