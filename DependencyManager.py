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

# Create .pylama directory if it doesn't exist
PACKAGE_DIR = os.path.join(os.path.expanduser('~'), '.pylama')
os.makedirs(PACKAGE_DIR, exist_ok=True)

# Configure logger for DependencyManager
logger = logging.getLogger('pylama.dependency')
logger.setLevel(logging.INFO)

# Create file handler for DependencyManager logs
dep_log_file = os.path.join(PACKAGE_DIR, 'pylama_dependency.log')
file_handler = logging.FileHandler(dep_log_file)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

logger.debug('DependencyManager initialized')

class DependencyManager:
    """Klasa do zarządzania zależnościami projektu."""

    # Mapowanie specjalnych przypadków, gdzie nazwa modułu różni się od nazwy pakietu
    PACKAGE_MAPPING = {
        'PIL': 'pillow',
        'cv2': 'opencv-python',
        'sklearn': 'scikit-learn',
        'bs4': 'beautifulsoup4',
        'webdriver': 'selenium',  # webdriver jest częścią selenium
        'Image': 'Pillow',  # Image z PIL
    }

    @staticmethod
    def extract_imports(code: str) -> List[str]:
        """Wyodrębnij importowane moduły z kodu."""
        # Usuń komentarze, aby uniknąć fałszywych trafień
        code = re.sub(r'#.*?$', '', code, flags=re.MULTILINE)

        # Regex do znalezienia importowanych modułów
        import_patterns = [
            r'^\s*import\s+([a-zA-Z0-9_]+(?:\s*,\s*[a-zA-Z0-9_]+)*)',  # import numpy, os, sys
            r'^\s*from\s+([a-zA-Z0-9_.]+)\s+import',  # from numpy import array
            r'^\s*import\s+([a-zA-Z0-9_]+(?:\s*,\s*[a-zA-Z0-9_]+)*)\s+as',  # import numpy as np
        ]

        modules = set()

        for pattern in import_patterns:
            matches = re.finditer(pattern, code, re.MULTILINE)
            for match in matches:
                # Dla każdego dopasowania, rozdziel po przecinkach i usuń białe znaki
                imported_modules = [m.strip() for m in match.group(1).split(',')]
                for module_name in imported_modules:
                    # Pobierz tylko główny moduł (np. dla 'selenium.webdriver' weź tylko 'selenium')
                    base_module = module_name.split('.')[0]
                    if base_module and base_module not in modules:
                        modules.add(base_module)

        return list(modules)

    @staticmethod
    def get_installed_packages() -> Dict[str, str]:
        """Pobierz listę zainstalowanych pakietów przy użyciu importlib.metadata."""
        try:
            # Pobierz wszystkie dystrybucje
            distributions = metadata.distributions()

            # Utwórz słownik {nazwa: wersja}
            installed_packages = {}
            for dist in distributions:
                try:
                    # W nowszych wersjach:
                    name = dist.metadata['Name'].lower()
                    version = dist.version
                except (AttributeError, KeyError):
                    try:
                        # Alternatywne podejście:
                        name = dist.name.lower()
                        version = dist.version
                    except AttributeError:
                        # Jeśli nic nie działa, spróbuj po prostu pobrać nazwę
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
        """Sprawdź, które zależności są już zainstalowane, a których brakuje."""
        installed_packages = DependencyManager.get_installed_packages()
        installed = []
        missing = []

        for module in modules:
            try:
                # Najpierw spróbuj zaimportować moduł
                importlib.import_module(module)
                installed.append(module)
                continue
            except ImportError:
                pass

            # Sprawdź mapowanie specjalnych przypadków
            package_name = DependencyManager.PACKAGE_MAPPING.get(module, module)

            # Sprawdź, czy pakiet jest zainstalowany (nawet jeśli nie można go zaimportować)
            if package_name.lower() in installed_packages:
                installed.append(module)
            else:
                missing.append(package_name)

        return installed, missing

    @staticmethod
    def install_dependencies(packages: List[str]) -> bool:
        """Zainstaluj brakujące zależności."""
        if not packages:
            return True

        # Usuń duplikaty i zmapuj nazwy modułów na nazwy pakietów
        unique_packages = []
        seen = set()

        for pkg in packages:
            # Użyj zmapowanej nazwy pakietu jeśli istnieje, w przeciwnym razie użyj oryginalnej
            mapped_pkg = DependencyManager.PACKAGE_MAPPING.get(pkg, pkg)
            if mapped_pkg.lower() not in seen:
                seen.add(mapped_pkg.lower())
                unique_packages.append(mapped_pkg)

        logger.info(f"Instalowanie zależności: {', '.join(unique_packages)}...")

        # Podziel instalację na pojedyncze pakiety, aby lepiej śledzić błędy
        success = True
        for pkg in unique_packages:
            try:
                logger.info(f"Instalowanie {pkg}...")
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pkg],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                logger.info(f"Zainstalowano {pkg} pomyślnie")
            except subprocess.CalledProcessError as e:
                logger.error(f"Nie udało się zainstalować {pkg}: {str(e)}")
                success = False
                # Kontynuuj instalację pozostałych pakietów mimo błędu
                continue

        if success:
            logger.info("Wszystkie zależności zostały pomyślnie zainstalowane")
        else:
            logger.warning("Wystąpiły błędy podczas instalacji niektórych zależności")

        return success