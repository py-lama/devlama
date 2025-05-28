import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import os
import json
import time
import subprocess
import sys
import re
import importlib
from importlib import metadata

# Create .devlama directory if it doesn't exist
PACKAGE_DIR = os.path.join(os.path.expanduser('~'), '.devlama')
os.makedirs(PACKAGE_DIR, exist_ok=True)

# Configure logger for DependencyManager
logger = logging.getLogger('devlama.dependency')
logger.setLevel(logging.INFO)

# Create file handler for DependencyManager logs
dep_log_file = os.path.join(PACKAGE_DIR, 'devlama_dependency.log')
file_handler = logging.FileHandler(dep_log_file)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

logger.debug('DependencyManager initialized')

class DependencyManager:
    """Class for managing project dependencies."""

    # Mapping of special cases where the module name differs from the package name
    PACKAGE_MAPPING = {
        'PIL': 'pillow',
        'cv2': 'opencv-python',
        'sklearn': 'scikit-learn',
        'bs4': 'beautifulsoup4',
        'webdriver': 'selenium',  # webdriver is part of selenium
        'Image': 'Pillow',  # Image from PIL
    }

    @staticmethod
    def extract_imports(code: str) -> List[str]:
        """Extract imported modules from code."""
        # Remove comments to avoid false positives
        code = re.sub(r'#.*?$', '', code, flags=re.MULTILINE)

        # Regex to find imported modules
        import_patterns = [
            r'^\s*import\s+([a-zA-Z0-9_]+(?:\s*,\s*[a-zA-Z0-9_]+)*)',  # import numpy, os, sys
            r'^\s*from\s+([a-zA-Z0-9_.]+)\s+import',  # from numpy import array
            r'^\s*import\s+([a-zA-Z0-9_]+(?:\s*,\s*[a-zA-Z0-9_]+)*)\s+as',  # import numpy as np
        ]

        modules = set()

        for pattern in import_patterns:
            matches = re.finditer(pattern, code, re.MULTILINE)
            for match in matches:
                # For each match, split by commas and remove whitespace
                imported_modules = [m.strip() for m in match.group(1).split(',')]
                for module_name in imported_modules:
                    # Get only the main module (e.g., for 'selenium.webdriver' take only 'selenium')
                    base_module = module_name.split('.')[0]
                    if base_module and base_module not in modules:
                        modules.add(base_module)

        return list(modules)

    @staticmethod
    def get_installed_packages() -> Dict[str, str]:
        """Get a list of installed packages using importlib.metadata."""
        try:
            # Get all distributions
            distributions = metadata.distributions()

            # Create dictionary {name: version}
            installed_packages = {}
            for dist in distributions:
                try:
                    # In newer versions:
                    name = dist.metadata['Name'].lower()
                    version = dist.version
                except (AttributeError, KeyError):
                    try:
                        # Alternative approach:
                        name = dist.name.lower()
                        version = dist.version
                    except AttributeError:
                        # If nothing works, just try to get the name
                        name = str(dist).lower()
                        version = "unknown"

                installed_packages[name] = version

            return installed_packages
        except Exception as e:
            logger.error(f"Error while fetching packages: {e}")
            # Save error details to error log file
            error_log = os.path.join(PACKAGE_DIR, 'dependency_errors.log')
            with open(error_log, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().isoformat()}] Error fetching packages: {e}\n")
            return {}

    @staticmethod
    def check_dependencies(modules: List[str]) -> Tuple[List[str], List[str]]:
        """Check which dependencies are already installed and which are missing."""
        installed_packages = DependencyManager.get_installed_packages()
        installed = []
        missing = []

        for module in modules:
            try:
                # First try to import the module
                importlib.import_module(module)
                installed.append(module)
                continue
            except ImportError:
                pass

            # Check the mapping of special cases
            package_name = DependencyManager.PACKAGE_MAPPING.get(module, module)

            # Check if the package is installed (even if it cannot be imported)
            if package_name.lower() in installed_packages:
                installed.append(module)
            else:
                missing.append(package_name)

        return installed, missing

    @staticmethod
    def install_dependencies(packages: List[str]) -> bool:
        """Install missing dependencies."""
        if not packages:
            return True

        # Remove duplicates and map module names to package names
        unique_packages = []
        seen = set()

        for pkg in packages:
            # Use the mapped package name if it exists, otherwise use the original
            mapped_pkg = DependencyManager.PACKAGE_MAPPING.get(pkg, pkg)
            if mapped_pkg.lower() not in seen:
                seen.add(mapped_pkg.lower())
                unique_packages.append(mapped_pkg)

        logger.info(f"Installing dependencies: {', '.join(unique_packages)}...")

        # Split installation into individual packages to better track errors
        success = True
        for pkg in unique_packages:
            try:
                logger.info(f"Installing {pkg}...")
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pkg],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                logger.info(f"Installed {pkg} successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install {pkg}: {str(e)}")
                success = False
                # Continue installing remaining packages despite the error
                continue

        if success:
            logger.info("All dependencies were successfully installed")
        else:
            logger.warning("Errors occurred while installing some dependencies")

        return success