#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyLama Sandbox - Automatyczne środowisko do uruchamiania dowolnego kodu Python

Ten moduł zapewnia automatyczne środowisko do uruchamiania kodu Python z zarządzaniem
zależnościami i integracją z Ollama Runner. Pozwala na szybkie tworzenie środowiska
do dowolnego kodu Python, automatycznie wykrywając i instalując wymagane zależności.

Główne funkcje:
1. Analiza kodu Python i wykrywanie importów za pomocą modułu ast
2. Automatyczna instalacja brakujących pakietów
3. Bezpieczne środowisko wykonawcze oparte na Docker
"""

import os
import sys
import subprocess
import tempfile
import shutil
import logging
import time
import traceback
import random
import json
import re
import importlib
import importlib.util
import inspect
import ast
import uuid
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Union, Set, Callable

# Konfiguracja loggera
logging_level = os.getenv('LOGGING_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, logging_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Próba importu pkg_resources, ale obsługa przypadku, gdy nie jest dostępny
try:
    import pkg_resources

    HAS_PKG_RESOURCES = True
except ImportError:
    HAS_PKG_RESOURCES = False
    logger.warning("Moduł pkg_resources nie jest dostępny. Niektóre funkcje mogą być ograniczone.")

# Próba importu dotenv, ale obsługa przypadku, gdy nie jest dostępny
try:
    from dotenv import load_dotenv

    HAS_DOTENV = True
    # Załaduj zmienne środowiskowe z pliku .env, jeśli istnieje
    load_dotenv()
except ImportError:
    HAS_DOTENV = False
    logger.warning("Moduł python-dotenv nie jest dostępny. Zmienne środowiskowe z pliku .env nie zostaną załadowane.")

# Mapowanie zależności - nazwa importu do nazwy pakietu PyPI
DEPENDENCY_MAP = {
    # Web and Browser Automation
    'selenium': 'selenium',
    'selenium.webdriver': 'selenium',
    'webdriver_manager': 'webdriver-manager',
    'pyautogui': 'pyautogui',
    'playwright': 'playwright',

    # Data Analysis
    'numpy': 'numpy',
    'pandas': 'pandas',
    'matplotlib': 'matplotlib',
    'seaborn': 'seaborn',
    'scipy': 'scipy',
    'sklearn': 'scikit-learn',
    'tensorflow': 'tensorflow',
    'torch': 'torch',
    'keras': 'keras',

    # Web Development
    'flask': 'flask',
    'django': 'django',
    'fastapi': 'fastapi',
    'requests': 'requests',
    'aiohttp': 'aiohttp',
    'bs4': 'beautifulsoup4',
    'lxml': 'lxml',

    # Utilities
    'dotenv': 'python-dotenv',
    'PIL': 'pillow',
    'yaml': 'pyyaml',
    'dateutil': 'python-dateutil',
    'pytz': 'pytz',
    'tqdm': 'tqdm',
}


class CodeAnalyzer:
    """Klasa do analizy kodu Python i wykrywania importowanych modułów."""

    def __init__(self):
        self.standard_libs = self._get_standard_libs()
        self.dependency_map = DEPENDENCY_MAP

    def _get_standard_libs(self) -> Set[str]:
        """Zwraca zbiór nazw modułów biblioteki standardowej Python."""
        # Lista popularnych modułów biblioteki standardowej
        return {
            'abc', 'argparse', 'array', 'ast', 'asyncio', 'base64', 'binascii', 'builtins',
            'calendar', 'collections', 'concurrent', 'configparser', 'contextlib', 'copy',
            'csv', 'ctypes', 'datetime', 'decimal', 'difflib', 'dis', 'email', 'enum',
            'errno', 'fcntl', 'filecmp', 'fnmatch', 'functools', 'gc', 'getopt', 'getpass',
            'gettext', 'glob', 'gzip', 'hashlib', 'heapq', 'hmac', 'html', 'http',
            'importlib', 'inspect', 'io', 'ipaddress', 'itertools', 'json', 'keyword',
            'linecache', 'locale', 'logging', 'lzma', 'math', 'mimetypes', 'mmap',
            'multiprocessing', 'netrc', 'numbers', 'operator', 'os', 'pathlib', 'pickle',
            'pkgutil', 'platform', 'pprint', 'pwd', 'pydoc', 'queue', 'random', 're',
            'reprlib', 'resource', 'select', 'shelve', 'shlex', 'shutil', 'signal',
            'site', 'smtplib', 'socket', 'socketserver', 'sqlite3', 'ssl', 'stat',
            'string', 'struct', 'subprocess', 'sys', 'sysconfig', 'tarfile', 'tempfile',
            'textwrap', 'threading', 'time', 'timeit', 'token', 'tokenize', 'traceback',
            'types', 'typing', 'unicodedata', 'unittest', 'urllib', 'uuid', 'warnings',
            'weakref', 'webbrowser', 'xml', 'xmlrpc', 'zipfile', 'zipimport', 'zlib',
            # Dodane moduły, które często są traktowane jako zewnętrzne, ale są standardowe
            'datetime', 'email', 'html', 'http', 'logging', 'math', 'multiprocessing',
            'unittest', 'urllib', 'xml'
        }

    def analyze_code(self, code: str) -> Dict[str, List[str]]:
        """
        Analizuje kod Python i wykrywa importowane moduły.

        Args:
            code: Kod Python do analizy.

        Returns:
            Słownik z listami modułów podzielonych na kategorie.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            logger.error(f"Błąd składni w kodzie: {e}")
            return {
                'standard_library': [],
                'third_party': [],
                'unknown': []
            }

        imports = set()

        # Wyszukaj wszystkie importy w kodzie
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name.split('.')[0])  # Pobierz główną nazwę modułu
            elif isinstance(node, ast.ImportFrom):
                if node.module:  # Ignoruj 'from . import x'
                    imports.add(node.module.split('.')[0])  # Pobierz główną nazwę modułu

        # Podziel importy na kategorie
        standard_library = []
        third_party = []
        unknown = []

        for module_name in imports:
            if module_name in self.standard_libs:
                standard_library.append(module_name)
            elif module_name in DEPENDENCY_MAP:
                third_party.append(module_name)
            else:
                # Jeśli nie jest to moduł standardowy ani znany zewnętrzny, zakładamy, że jest zewnętrzny
                third_party.append(module_name)

        return {
            'standard_library': standard_library,
            'third_party': third_party,
            'unknown': unknown
        }

    def _categorize_import(self, module_name: str, imports: Dict[str, List[str]]) -> None:
        """
        Kategoryzuje importowany moduł jako standardowy, zewnętrzny lub nieznany.

        Args:
            module_name: Nazwa importowanego modułu
            imports: Słownik do aktualizacji
        """
        # Wyodrębnij główny moduł (np. z "numpy.random" wyodrębnij "numpy")
        main_module = module_name.split('.')[0]

        # Sprawdź, czy moduł jest już w jednej z kategorii
        for category in imports.values():
            if main_module in category:
                return

        # Kategoryzuj moduł
        if main_module in self.standard_library:
            imports['standard_library'].append(main_module)
        elif main_module in self.dependency_map or any(
                module_name.startswith(dep + '.') for dep in self.dependency_map):
            imports['third_party'].append(main_module)
        else:
            # Sprawdź, czy moduł jest zainstalowany
            try:
                importlib.util.find_spec(main_module)
                imports['third_party'].append(main_module)
            except (ImportError, ModuleNotFoundError):
                imports['unknown'].append(main_module)

    def get_required_packages(self, imports: Dict[str, List[str]]) -> List[str]:
        """
        Zwraca listę pakietów PyPI wymaganych przez kod.

        Args:
            imports: Słownik z importami podzielonymi na kategorie.

        Returns:
            Lista nazw pakietów PyPI.
        """
        required_packages = []

        # Dodaj pakiety zewnętrzne
        for module in imports.get('third_party', []):
            if module in self.dependency_map:
                required_packages.append(self.dependency_map[module])
            else:
                # Jeśli nie ma mapowania, zakładamy, że nazwa pakietu jest taka sama jak nazwa modułu
                required_packages.append(module)

        # Dodaj pakiety z unknown (może być ryzykowne, ale spróbujemy)
        for module in imports.get('unknown', []):
            if module in self.dependency_map:
                required_packages.append(self.dependency_map[module])
            else:
                # Sprawdź, czy istnieje pakiet o takiej nazwie w PyPI
                required_packages.append(module)

        return list(set(required_packages))  # Usuń duplikaty


class DependencyManager:
    """Klasa do zarządzania zależnościami pakietów Python."""

    def __init__(self):
        """Inicjalizacja menedżera zależności."""
        self.code_analyzer = CodeAnalyzer()
        self.installed_packages = self._get_installed_packages()
        # Dodatkowe mapowanie dla popularnych pakietów, które mogą być trudne do wykrycia
        self.additional_mappings = {
            'np': 'numpy',
            'pd': 'pandas',
            'plt': 'matplotlib',
            'tf': 'tensorflow',
            'torch': 'torch',
            'cv2': 'opencv-python',
            'sk': 'scikit-learn',
            'sklearn': 'scikit-learn',
            'bs4': 'beautifulsoup4',
            'requests': 'requests',
            'django': 'django',
            'flask': 'flask',
            'sqlalchemy': 'sqlalchemy',
            'pytest': 'pytest',
            'unittest': None,  # Moduł standardowy
            'json': None,  # Moduł standardowy
            'os': None,  # Moduł standardowy
            'sys': None,  # Moduł standardowy
            'math': None  # Moduł standardowy
        }

    def _get_installed_packages(self) -> Dict[str, str]:
        """Zwraca słownik zainstalowanych pakietów z ich wersjami."""
        installed = {}

        if HAS_PKG_RESOURCES:
            # Użyj pkg_resources, jeśli jest dostępny
            try:
                for package in pkg_resources.working_set:
                    installed[package.key] = package.version
            except Exception as e:
                logger.warning(f"Nie udało się pobrać listy zainstalowanych pakietów: {e}")
        else:
            # Alternatywna metoda, jeśli pkg_resources nie jest dostępny
            try:
                # Użyj pip do pobrania listy zainstalowanych pakietów
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'list', '--format=json'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )

                if result.returncode == 0 and result.stdout.strip():
                    packages = json.loads(result.stdout)
                    for package in packages:
                        name = package.get('name', '').lower()
                        version = package.get('version', '')
                        if name and version:
                            installed[name] = version
            except Exception as e:
                logger.warning(f"Nie udało się pobrać listy zainstalowanych pakietów przez pip: {e}")

        return installed

    def analyze_dependencies(self, code: str) -> Dict[str, Any]:
        """
        Analizuje kod Python i wykrywa zależności.

        Args:
            code: Kod Python do analizy.

        Returns:
            Słownik z informacjami o zależnościach.
        """
        try:
            # Analizuj kod i wykryj importy
            imports = self.code_analyzer.analyze_code(code)

            # Pobierz wymagane pakiety na podstawie importów
            required_packages = self.code_analyzer.get_required_packages(imports)

            # Dodatkowa analiza kodu dla wykrycia aliasowanych importów
            for alias, package in self.additional_mappings.items():
                if package and f"{alias}." in code and package not in required_packages:
                    required_packages.append(package)

            # Sprawdź, które pakiety są już zainstalowane
            installed = []
            missing = []

            for package in required_packages:
                if package in self.installed_packages:
                    installed.append(package)
                else:
                    missing.append(package)

            return {
                'imports': imports,
                'required_packages': required_packages,
                'installed_packages': installed,
                'missing_packages': missing,
                'installed_packages_count': len(installed)
            }
        except Exception as e:
            logger.error(f"Błąd podczas analizy zależności: {e}")
            return {
                'imports': {},
                'required_packages': [],
                'installed_packages': [],
                'missing_packages': [],
                'installed_packages_count': 0,
                'error': str(e)
            }

    def install_package(self, package_name: str) -> bool:
        """
        Instaluje pakiet Python za pomocą pip.

        Args:
            package_name: Nazwa pakietu do zainstalowania

        Returns:
            True, jeśli instalacja się powiodła, False w przeciwnym razie
        """
        try:
            logger.info(f"Instalowanie pakietu: {package_name}")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # Aktualizuj słownik zainstalowanych pakietów
            self.installed_packages = self._get_installed_packages()
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Błąd podczas instalacji pakietu {package_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd podczas instalacji pakietu {package_name}: {e}")
            return False

    def ensure_dependencies(self, code: str) -> Dict[str, Any]:
        """
        Analizuje kod i instaluje brakujące zależności.

        Args:
            code: Kod Python do analizy

        Returns:
            Słownik z informacjami o zależnościach i wynikach instalacji
        """
        # Analizuj zależności
        dependencies = self.analyze_dependencies(code)

        # Instaluj brakujące pakiety
        installation_results = []
        for package in dependencies['missing_packages']:
            success = self.install_package(package)
            installation_results.append({
                'package': package,
                'success': success
            })

        # Aktualizuj słownik zainstalowanych pakietów
        dependencies['installed_packages'] = [
            {'name': package, 'version': self.installed_packages.get(package.lower(), 'unknown')}
            for package in dependencies['required_packages']
            if package.lower() in self.installed_packages
        ]
        dependencies['installation_results'] = installation_results

        return dependencies


class DockerEnvironment:
    """Zarządza środowiskiem Docker do uruchamiania kodu Python."""

    def __init__(self, image_name: str = None, container_name: str = None):
        """
        Inicjalizacja środowiska Docker.

        Args:
            image_name: Nazwa obrazu Docker (domyślnie: python:3.9-slim)
            container_name: Nazwa kontenera (domyślnie: pylama-sandbox-{uuid})
        """
        self.image_name = image_name or os.getenv('DOCKER_IMAGE', 'python:3.9-slim')
        self.container_name = container_name or os.getenv('DOCKER_CONTAINER_NAME',
                                                          f'pylama-sandbox-{uuid.uuid4().hex[:8]}')
        self.check_docker_installation()

    def check_docker_installation(self) -> bool:
        """
        Sprawdza, czy Docker jest zainstalowany i dostępny.

        Returns:
            True, jeśli Docker jest dostępny, False w przeciwnym razie
        """
        try:
            result = subprocess.run(
                ['docker', '--version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True
            )

            if result.returncode != 0:
                logger.error("Docker nie jest prawidłowo zainstalowany.")
                logger.error(f"Błąd: {result.stderr}")
                return False

            logger.info(f"Docker zainstalowany: {result.stdout.strip()}")
            return True
        except FileNotFoundError:
            logger.error("Docker nie jest zainstalowany lub nie jest dostępny w ścieżce systemowej.")
            return False

    def is_container_running(self) -> bool:
        """
        Sprawdza, czy kontener Docker jest już uruchomiony.

        Returns:
            True, jeśli kontener jest uruchomiony, False w przeciwnym razie
        """
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={self.container_name}', '--format', '{{.Names}}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True
            )

            return self.container_name in result.stdout
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania stanu kontenera: {e}")
            return False

    def start_container(self) -> bool:
        """
        Uruchamia kontener Docker, jeśli nie jest już uruchomiony.

        Returns:
            True, jeśli kontener został uruchomiony lub już działa, False w przypadku błędu
        """
        if self.is_container_running():
            logger.info(f"Kontener '{self.container_name}' już działa.")
            return True

        logger.info(f"Uruchamianie kontenera '{self.container_name}'...")

        try:
            # Najpierw sprawdź, czy obrazu nie trzeba pobrać
            result = subprocess.run(
                ['docker', 'image', 'inspect', self.image_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )

            if result.returncode != 0:
                logger.info(f"Pobieranie obrazu Docker '{self.image_name}'...")
                pull_result = subprocess.run(
                    ['docker', 'pull', self.image_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                    text=True
                )
                logger.info(f"Obraz Docker pobrany: {self.image_name}")

            # Utwórz i uruchom kontener
            run_result = subprocess.run(
                [
                    'docker', 'run',
                    '--name', self.container_name,
                    '-d',  # Uruchom w tle
                    '--rm',  # Usuń kontener po zatrzymaniu
                    '-v', f"{os.getcwd()}:/app",  # Zamontuj bieżący katalog jako /app
                    '-w', '/app',  # Ustaw katalog roboczy na /app
                    self.image_name,
                    'tail', '-f', '/dev/null'  # Utrzymuj kontener uruchomiony
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True
            )

            logger.info(f"Kontener '{self.container_name}' uruchomiony.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Błąd podczas uruchamiania kontenera: {e}")
            logger.error(f"STDERR: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd podczas uruchamiania kontenera: {e}")
            return False

    def stop_container(self) -> bool:
        """
        Zatrzymuje kontener Docker, jeśli jest uruchomiony.

        Returns:
            True, jeśli kontener został zatrzymany lub nie był uruchomiony, False w przypadku błędu
        """
        if not self.is_container_running():
            logger.info(f"Kontener '{self.container_name}' nie jest uruchomiony.")
            return True

        logger.info(f"Zatrzymywanie kontenera '{self.container_name}'...")

        try:
            subprocess.run(
                ['docker', 'stop', self.container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True
            )

            logger.info(f"Kontener '{self.container_name}' zatrzymany.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Błąd podczas zatrzymywania kontenera: {e}")
            return False
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd podczas zatrzymywania kontenera: {e}")
            return False

    def run_code(self, code: str, timeout: int = 60) -> Dict[str, Any]:
        """
        Uruchamia kod Python w kontenerze Docker.

        Args:
            code: Kod Python do uruchomienia
            timeout: Limit czasu wykonania w sekundach

        Returns:
            Słownik z wynikami wykonania kodu
        """
        # Upewnij się, że kontener jest uruchomiony
        if not self.is_container_running() and not self.start_container():
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Nie udało się uruchomić kontenera Docker',
                'error': 'ContainerStartError'
            }

        # Utwórz tymczasowy plik z kodem
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(code)

        try:
            # Kopiuj plik do kontenera
            copy_result = subprocess.run(
                ['docker', 'cp', temp_file_path, f"{self.container_name}:/app/temp_script.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True
            )

            # Uruchom kod w kontenerze
            run_result = subprocess.run(
                [
                    'docker', 'exec',
                    '-e', 'PYTHONUNBUFFERED=1',
                    self.container_name,
                    'python', '/app/temp_script.py'
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                text=True
            )

            return {
                'success': run_result.returncode == 0,
                'stdout': run_result.stdout,
                'stderr': run_result.stderr,
                'return_code': run_result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Przekroczono limit czasu wykonania ({timeout}s)',
                'error': 'TimeoutError'
            }
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'stdout': e.stdout if hasattr(e, 'stdout') else '',
                'stderr': e.stderr if hasattr(e, 'stderr') else str(e),
                'error': 'ExecutionError'
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'error': type(e).__name__
            }
        finally:
            # Usuń tymczasowy plik
            try:
                os.unlink(temp_file_path)
            except:
                pass

            # Usuń plik z kontenera
            try:
                subprocess.run(
                    ['docker', 'exec', self.container_name, 'rm', '-f', '/app/temp_script.py'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False
                )
            except:
                pass


class PythonSandbox:
    """Główna klasa do uruchamiania kodu Python w bezpiecznym środowisku."""

    def __init__(self, use_docker: bool = True):
        """
        Inicjalizacja środowiska sandbox.

        Args:
            use_docker: Czy używać Docker do uruchamiania kodu
        """
        self.use_docker = use_docker
        self.dependency_manager = DependencyManager()

        if use_docker:
            self.docker_env = DockerEnvironment()
        else:
            self.docker_env = None

    def run_code(self, code: str, install_dependencies: bool = True, timeout: int = 60) -> Dict[str, Any]:
        """
        Uruchamia kod Python w bezpiecznym środowisku.

        Args:
            code: Kod Python do uruchomienia
            install_dependencies: Czy automatycznie instalować zależności
            timeout: Limit czasu wykonania w sekundach

        Returns:
            Słownik z wynikami wykonania kodu i informacjami o zależnościach
        """
        result = {
            'code': code,
            'dependencies': None,
            'execution': None
        }

        # Analizuj i zainstaluj zależności, jeśli potrzeba
        if install_dependencies:
            dependencies = self.dependency_manager.ensure_dependencies(code)
            result['dependencies'] = dependencies

        # Uruchom kod
        if self.use_docker and self.docker_env:
            execution_result = self.docker_env.run_code(code, timeout)
        else:
            execution_result = self._run_code_locally(code, timeout)

        result['execution'] = execution_result
        return result

    def _run_code_locally(self, code: str, timeout: int = 60) -> Dict[str, Any]:
        """
        Uruchamia kod Python lokalnie (bez Docker).

        Args:
            code: Kod Python do uruchomienia
            timeout: Limit czasu wykonania w sekundach

        Returns:
            Słownik z wynikami wykonania kodu
        """
        # Utwórz tymczasowy plik z kodem
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(code)

        try:
            # Uruchom kod w nowym procesie
            process = subprocess.run(
                [sys.executable, temp_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                text=True
            )

            return {
                'success': process.returncode == 0,
                'stdout': process.stdout,
                'stderr': process.stderr,
                'return_code': process.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Przekroczono limit czasu wykonania ({timeout}s)',
                'error': 'TimeoutError'
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'error': type(e).__name__
            }
        finally:
            # Usuń tymczasowy plik
            try:
                os.unlink(temp_file_path)
            except:
                pass


# Przykład użycia
def main():
    # Definiowanie przykładowych kodów jako zmienne
    # Przykład 1: Kod z zewnętrznymi zależnościami (numpy, pandas)
    example_code = "print('Hello, world!')\n"
    example_code += "import numpy as np\n\n"
    example_code += "# Przykład użycia NumPy\n"
    example_code += "arr = np.array([1, 2, 3, 4, 5])\n"
    example_code += "print(f'Tablica NumPy: {arr}')\n"
    example_code += "print(f'Średnia: {np.mean(arr)}')\n\n"
    example_code += "# Przykład użycia pandas\n"
    example_code += "import pandas as pd\n"
    example_code += "df = pd.DataFrame({\n"
    example_code += "    'A': [1, 2, 3, 4, 5],\n"
    example_code += "    'B': [10, 20, 30, 40, 50]\n"
    example_code += "})\n"
    example_code += "print('\\nDataFrame pandas:')\n"
    example_code += "print(df)\n"
    example_code += "print(f'Średnia kolumny A: {df[\"A\"].mean()}')"

    # Przykład 2: Kod bez zewnętrznych zależności
    simple_code = "import os\n"
    simple_code += "import sys\n"
    simple_code += "import math\n\n"
    simple_code += "print('Informacje o systemie:')\n"
    simple_code += "print(f'System operacyjny: {os.name}')\n"
    simple_code += "print(f'Wersja Pythona: {sys.version}')\n"
    simple_code += "print(f'Katalog bieżący: {os.getcwd()}')\n\n"
    simple_code += "# Przykład obliczeń matematycznych\n"
    simple_code += "print('\\nObliczenia matematyczne:')\n"
    simple_code += "print(f'Pi: {math.pi}')\n"
    simple_code += "print(f'Pierwiastek z 16: {math.sqrt(16)}')\n"
    simple_code += "print(f'Silnia z 5: {math.factorial(5)}')"

    # Funkcja do wyświetlania wyników
    def display_results(result, title):
        print(f"\n=== {title} ===")
        print("Wyniki analizy zależności:")
        print(f"  Wymagane pakiety: {', '.join(result.get('required_packages', []))}" if result.get(
            'required_packages') else "  Wymagane pakiety: brak")
        print(f"  Zainstalowane pakiety: {result.get('installed_packages_count', 0)}")
        print(f"  Brakujące pakiety: {', '.join(result.get('missing_packages', []))}" if result.get(
            'missing_packages') else "  Brakujące pakiety: brak")

        print("\nWyniki wykonania kodu:")
        print(f"  Sukces: {result.get('success', False)}")
        print(f"  Standardowe wyjście:\n{result.get('stdout', '')}")
        if result.get('stderr'):
            print(f"  Standardowe wyjście błędów:\n{result.get('stderr', '')}")

    # Utwórz sandbox i uruchom kod z zewnętrznymi zależnościami
    print("\n=== Test 1: Uruchamianie kodu z zewnętrznymi zależnościami (numpy, pandas) ===")
    sandbox = PythonSandbox(use_docker=True)
    result = sandbox.run_code(example_code)
    display_results(result, "Wyniki dla kodu z zewnętrznymi zależnościami")

    # Uruchom kod bez zewnętrznych zależności
    print("\n=== Test 2: Uruchamianie kodu bez zewnętrznych zależności ===")
    result = sandbox.run_code(simple_code)
    display_results(result, "Wyniki dla kodu bez zewnętrznych zależności")

    # Przykład 3: Kod z błędem składni
    code_with_syntax_error = "print('Ten kod zawiera błąd składni')\n"
    code_with_syntax_error += "if True:\n"
    code_with_syntax_error += "    print('Ten kod jest poprawny')\n"
    code_with_syntax_error += "else\n"  # Celowo brakuje dwukropka po else
    code_with_syntax_error += "    print('Brakuje dwukropka po else')"

    # Przykład 4: Kod z błędem wykonania
    code_with_runtime_error = "print('Ten kod zawiera błąd wykonania')\n"
    code_with_runtime_error += "x = 10 / 0  # Dzielenie przez zero\n"
    code_with_runtime_error += "print('Ta linia nie zostanie wykonana')"

    # Tworzymy instancję sandboxa tylko raz
    sandbox = PythonSandbox(use_docker=True)

    # Uruchamianie testów
    print("\n=== Test 1: Uruchamianie kodu z zewnętrznymi zależnościami (numpy, pandas) ===")
    result = sandbox.run_code(example_code)
    display_results(result, "Wyniki dla kodu z zewnętrznymi zależnościami")

    print("\n=== Test 2: Uruchamianie kodu bez zewnętrznych zależności ===")
    result = sandbox.run_code(simple_code)
    display_results(result, "Wyniki dla kodu bez zewnętrznych zależności")

    print("\n=== Test 3: Uruchamianie kodu z błędem składni ===")
    result = sandbox.run_code(code_with_syntax_error)
    display_results(result, "Wyniki dla kodu z błędem składni")

    print("\n=== Test 4: Uruchamianie kodu z błędem wykonania ===")
    result = sandbox.run_code(code_with_runtime_error)
    display_results(result, "Wyniki dla kodu z błędem wykonania")


if __name__ == "__main__":
    main()
