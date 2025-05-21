#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import ast
import json
import logging
import tempfile
import uuid
import shutil
import importlib
import importlib.util  # Dodanie importlib.util
from typing import Dict, List, Any, Optional, Union, Tuple

# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Próba importu opcjonalnych modułów
try:
    import pkg_resources
except ImportError:
    logger.warning("Moduł pkg_resources nie jest dostępny. Niektóre funkcje mogą być ograniczone.")
    pkg_resources = None

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    logger.warning("Moduł python-dotenv nie jest dostępny. Zmienne środowiskowe z pliku .env nie zostaną załadowane.")


class CodeAnalyzer:
    """Klasa do analizy kodu Python i wykrywania zależności."""

    def __init__(self):
        # Standardowe moduły Pythona
        self.std_lib_modules = set(sys.builtin_module_names)

        # Dodanie innych standardowych modułów
        for module in sys.modules:
            if module and '.' not in module:
                self.std_lib_modules.add(module)

        # Dodanie dodatkowych standardowych modułów
        additional_std_libs = [
            'os', 'sys', 'math', 'random', 'datetime', 'time', 'json',
            'csv', 're', 'collections', 'itertools', 'functools', 'typing',
            'pathlib', 'io', 'tempfile', 'shutil', 'glob', 'argparse',
            'logging', 'unittest', 'pickle', 'hashlib', 'uuid', 'copy',
            'subprocess', 'multiprocessing', 'threading', 'queue', 'socket',
            'email', 'http', 'urllib', 'base64', 'html', 'xml', 'zipfile',
            'tarfile', 'gzip', 'bz2', 'lzma', 'zlib', 'struct', 'array',
            'enum', 'statistics', 'decimal', 'fractions', 'numbers',
            'cmath', 'contextlib', 'abc', 'ast', 'dis', 'inspect',
            'importlib', 'pkgutil', 'traceback', 'warnings', 'weakref',
            'types', 'operator', 'string', 'calendar', 'locale', 'gettext',
            'platform', 'signal', 'gc', 'atexit', 'builtins', 'code',
            'codecs', 'codeop', 'msvcrt', 'winreg', 'winsound', 'posix',
            'pwd', 'spwd', 'grp', 'crypt', 'termios', 'tty', 'pty', 'fcntl',
            'pipes', 'resource', 'nis', 'syslog', 'optparse', 'getopt',
            'cmd', 'shlex', 'pdb', 'profile', 'pstats', 'timeit',
            'trace', 'tracemalloc', 'distutils', 'ensurepip', 'venv',
            'zipapp', 'turtle', 'cmd', 'asyncio', 'concurrent', 'contextvars',
            'dataclasses', 'graphlib', 'zoneinfo'
        ]

        self.std_lib_modules.update(additional_std_libs)

    def analyze_code(self, code: str) -> Dict[str, Any]:
        """Analizuje kod Python i wykrywa importowane moduły."""
        try:
            tree = ast.parse(code)
            imports = {}

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        module_name = name.name.split('.')[0]
                        imports[module_name] = self._classify_module(module_name)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split('.')[0]
                        imports[module_name] = self._classify_module(module_name)

            # Filtrowanie i kategoryzacja importów
            std_lib_imports = [name for name, category in imports.items() if category == 'standard_library']
            third_party_imports = [name for name, category in imports.items() if category == 'third_party']
            unknown_imports = [name for name, category in imports.items() if category == 'unknown']

            return {
                'imports': imports,
                'standard_library': std_lib_imports,
                'third_party': third_party_imports,
                'unknown': unknown_imports,
                'required_packages': third_party_imports + unknown_imports
            }

        except SyntaxError as e:
            logger.error(f"Błąd składni w kodzie: {e}")
            return {
                'imports': {},
                'standard_library': [],
                'third_party': [],
                'unknown': [],
                'required_packages': [],
                'error': str(e)
            }

        except Exception as e:
            logger.error(f"Błąd podczas analizy kodu: {e}")
            return {
                'imports': {},
                'standard_library': [],
                'third_party': [],
                'unknown': [],
                'required_packages': [],
                'error': str(e)
            }

    def _classify_module(self, module_name: str) -> str:
        """Klasyfikuje moduł jako standardowy, zewnętrzny lub nieznany."""
        if module_name in self.std_lib_modules:
            return 'standard_library'

        try:
            spec = importlib.util.find_spec(module_name)
            if spec is not None:
                return 'third_party'
        except (ImportError, ValueError):
            pass

        return 'unknown'


class DependencyManager:
    """Klasa do zarządzania zależnościami i instalacji pakietów."""

    def __init__(self):
        self.analyzer = CodeAnalyzer()

        # Mapowanie popularnych modułów do nazw pakietów
        self.module_to_package = {
            'numpy': 'numpy',
            'pandas': 'pandas',
            'matplotlib': 'matplotlib',
            'scipy': 'scipy',
            'sklearn': 'scikit-learn',
            'tensorflow': 'tensorflow',
            'torch': 'torch',
            'keras': 'keras',
            'django': 'django',
            'flask': 'flask',
            'requests': 'requests',
            'bs4': 'beautifulsoup4',
            'beautifulsoup4': 'beautifulsoup4',
            'lxml': 'lxml',
            'html5lib': 'html5lib',
            'selenium': 'selenium',
            'PIL': 'pillow',
            'cv2': 'opencv-python',
            'pytest': 'pytest',
            'sqlalchemy': 'sqlalchemy',
            'psycopg2': 'psycopg2-binary',
            'pymysql': 'pymysql',
            'sqlite3': 'pysqlite3',
            'nltk': 'nltk',
            'gensim': 'gensim',
            'spacy': 'spacy',
            'transformers': 'transformers',
            'networkx': 'networkx',
            'plotly': 'plotly',
            'dash': 'dash',
            'bokeh': 'bokeh',
            'seaborn': 'seaborn',
            'sympy': 'sympy',
            'statsmodels': 'statsmodels',
            'xgboost': 'xgboost',
            'lightgbm': 'lightgbm',
            'catboost': 'catboost',
            'pyspark': 'pyspark',
            'dask': 'dask',
            'ray': 'ray',
            'fastapi': 'fastapi',
            'uvicorn': 'uvicorn',
            'streamlit': 'streamlit',
            'gradio': 'gradio',
            'pytest': 'pytest',
            'tqdm': 'tqdm',
            'rich': 'rich',
            'typer': 'typer',
            'click': 'click',
            'pydantic': 'pydantic',
            'jinja2': 'jinja2',
            'yaml': 'pyyaml',
            'toml': 'toml',
            'json5': 'json5',
            'ujson': 'ujson',
            'orjson': 'orjson',
            'redis': 'redis',
            'pymongo': 'pymongo',
            'boto3': 'boto3',
            'google': 'google-api-python-client',
            'azure': 'azure-storage-blob',
            'openai': 'openai',
            'langchain': 'langchain',
            'huggingface_hub': 'huggingface_hub',
            'tiktoken': 'tiktoken',
            'tokenizers': 'tokenizers',
            'sentencepiece': 'sentencepiece',
            'diffusers': 'diffusers',
            'accelerate': 'accelerate',
            'onnx': 'onnx',
            'onnxruntime': 'onnxruntime',
            'tflite': 'tflite',
            'openvino': 'openvino',
            'timm': 'timm',
            'albumentations': 'albumentations',
            'kornia': 'kornia',
            'fastai': 'fastai',
            'pytorch_lightning': 'pytorch-lightning',
            'wandb': 'wandb',
            'mlflow': 'mlflow',
            'optuna': 'optuna',
            'ray': 'ray[tune]',
            'hydra': 'hydra-core',
            'prefect': 'prefect',
            'airflow': 'apache-airflow',
            'dagster': 'dagster',
            'kedro': 'kedro',
            'great_expectations': 'great_expectations',
            'dbt': 'dbt-core',
            'polars': 'polars',
            'vaex': 'vaex',
            'datatable': 'datatable',
            'modin': 'modin',
            'cudf': 'cudf',
            'cupy': 'cupy',
            'jax': 'jax',
            'flax': 'flax',
            'optax': 'optax',
            'haiku': 'dm-haiku',
            'numpyro': 'numpyro',
            'pyro': 'pyro-ppl',
            'pystan': 'pystan',
            'pymc': 'pymc',
            'arviz': 'arviz',
            'corner': 'corner',
            'emcee': 'emcee',
            'dynesty': 'dynesty',
            'astropy': 'astropy',
            'sunpy': 'sunpy',
            'healpy': 'healpy',
            'astroquery': 'astroquery',
            'astroplan': 'astroplan',
            'astroml': 'astroml',
            'astroscrappy': 'astroscrappy',
            'astrowidgets': 'astrowidgets',
            'ccdproc': 'ccdproc',
            'photutils': 'photutils',
            'specutils': 'specutils',
            'reproject': 'reproject',
            'regions': 'regions',
            'gala': 'gala',
            'pyia': 'pyia',
            'galpy': 'galpy',
            'ginga': 'ginga',
            'glue': 'glue-vispy-viewers',
            'pywwt': 'pywwt',
            'aplpy': 'aplpy',
            'rebound': 'rebound',
            'reboundx': 'reboundx',
            'exoplanet': 'exoplanet',
            'batman': 'batman-package',
            'radvel': 'radvel',
            'lightkurve': 'lightkurve',
            'astroplan': 'astroplan',
            'astroquery': 'astroquery',
            'astropy': 'astropy',
            'sunpy': 'sunpy',
            'healpy': 'healpy',
            'astroquery': 'astroquery',
            'astroplan': 'astroplan',
            'astroml': 'astroml',
            'astroscrappy': 'astroscrappy',
            'astrowidgets': 'astrowidgets',
            'ccdproc': 'ccdproc',
            'photutils': 'photutils',
            'specutils': 'specutils',
            'reproject': 'reproject',
            'regions': 'regions',
            'gala': 'gala',
            'pyia': 'pyia',
            'galpy': 'galpy',
            'ginga': 'ginga',
            'glue': 'glue-vispy-viewers',
            'pywwt': 'pywwt',
            'aplpy': 'aplpy',
            'rebound': 'rebound',
            'reboundx': 'reboundx',
            'exoplanet': 'exoplanet',
            'batman': 'batman-package',
            'radvel': 'radvel',
            'lightkurve': 'lightkurve'
        }

    def analyze_dependencies(self, code: str) -> Dict[str, Any]:
        """Analizuje zależności w kodzie Python."""
        try:
            analysis_result = self.analyzer.analyze_code(code)
            required_modules = analysis_result.get('required_packages', [])

            # Mapowanie modułów na pakiety
            required_packages = []
            for module in required_modules:
                package = self.module_to_package.get(module, module)
                if package not in required_packages:
                    required_packages.append(package)

            # Instalacja pakietów
            installed_packages = []
            missing_packages = []

            for package in required_packages:
                if self.install_package(package):
                    installed_packages.append(package)
                else:
                    missing_packages.append(package)

            return {
                'imports': analysis_result.get('imports', {}),
                'required_packages': required_packages,
                'installed_packages': installed_packages,
                'missing_packages': missing_packages,
                'installed_packages_count': len(installed_packages)
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
            package_name: Nazwa pakietu do zainstalowania.

        Returns:
            bool: True, jeśli instalacja się powiodła, False w przeciwnym razie.
        """
        try:
            logger.info(f"Instalowanie pakietu: {package_name}")

            # Użyj pip do instalacji pakietu
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package_name],
                capture_output=True,
                text=True,
                check=True
            )

            logger.info(f"Pakiet {package_name} zainstalowany pomyślnie.")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Błąd podczas instalacji pakietu {package_name}: {e}")
            return False

        except Exception as e:
            logger.error(f"Nieoczekiwany błąd podczas instalacji pakietu {package_name}: {e}")
            return False

    def check_package_installed(self, package_name: str) -> bool:
        """
        Sprawdza, czy pakiet jest zainstalowany.

        Args:
            package_name: Nazwa pakietu do sprawdzenia.

        Returns:
            bool: True, jeśli pakiet jest zainstalowany, False w przeciwnym razie.
        """
        try:
            # Próba importu modułu
            __import__(package_name)
            return True
        except ImportError:
            pass

        # Sprawdzenie za pomocą pkg_resources
        if pkg_resources is not None:
            try:
                pkg_resources.get_distribution(package_name)
                return True
            except pkg_resources.DistributionNotFound:
                pass

        # Sprawdzenie za pomocą pip list
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', package_name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            pass

        return False


class PythonSandbox:
    """Klasa do bezpiecznego uruchamiania kodu Python w izolowanym środowisku."""

    def __init__(self, use_docker: bool = False):
        self.use_docker = use_docker
        self.dependency_manager = DependencyManager()

        # Sprawdzenie, czy Docker jest zainstalowany, jeśli ma być używany
        if self.use_docker:
            self._check_docker_installed()

    def _check_docker_installed(self) -> bool:
        """Sprawdza, czy Docker jest zainstalowany w systemie."""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Docker zainstalowany: {result.stdout.strip()}")
                return True
            else:
                logger.warning("Docker nie jest zainstalowany lub nie działa poprawnie.")
                return False
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania instalacji Dockera: {e}")
            return False

    def run_code(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Uruchamia kod Python w bezpiecznym środowisku.

        Args:
            code: Kod Python do uruchomienia.
            timeout: Limit czasu wykonania w sekundach.

        Returns:
            Dict[str, Any]: Wyniki wykonania kodu.
        """
        # Analiza zależności
        dependencies_result = self.dependency_manager.analyze_dependencies(code)

        # Sprawdzenie, czy kod ma błędy składni
        try:
            ast.parse(code)
        except SyntaxError as e:
            logger.error(f"Błąd składni w kodzie: {e}")
            return {
                **dependencies_result,
                'success': False,
                'stdout': '',
                'stderr': f"Błąd składni: {str(e)}",
                'error_type': 'SyntaxError',
                'error_message': str(e)
            }

        # Uruchomienie kodu w odpowiednim środowisku
        if self.use_docker:
            return self._run_in_docker(code, timeout, dependencies_result)
        else:
            return self._run_locally(code, timeout, dependencies_result)

    def _run_locally(self, code: str, timeout: int, dependencies_result: Dict[str, Any]) -> Dict[str, Any]:
        """Uruchamia kod lokalnie w podprocesie."""
        # Utworzenie tymczasowego pliku z kodem
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name

        try:
            # Uruchomienie kodu w podprocesie z limitem czasu
            result = subprocess.run(
                [sys.executable, temp_file_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                **dependencies_result,
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'exit_code': result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                **dependencies_result,
                'success': False,
                'stdout': '',
                'stderr': f"Przekroczono limit czasu wykonania ({timeout} sekund).",
                'error_type': 'TimeoutError',
                'error_message': f"Execution timed out after {timeout} seconds"
            }

        except Exception as e:
            return {
                **dependencies_result,
                'success': False,
                'stdout': '',
                'stderr': f"Błąd podczas wykonania kodu: {str(e)}",
                'error_type': type(e).__name__,
                'error_message': str(e)
            }

        finally:
            # Usunięcie tymczasowego pliku
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass

    def _run_in_docker(self, code: str, timeout: int, dependencies_result: Dict[str, Any]) -> Dict[str, Any]:
        """Uruchamia kod w kontenerze Docker."""
        # Utworzenie unikalnego ID dla kontenera
        container_id = f"pylama-sandbox-{uuid.uuid4().hex[:8]}"

        # Utworzenie tymczasowego katalogu na pliki
        temp_dir = tempfile.mkdtemp()
        code_file_path = os.path.join(temp_dir, 'code.py')

        try:
            # Zapisanie kodu do pliku
            with open(code_file_path, 'w') as f:
                f.write(code)

            # Przygotowanie polecenia Docker
            docker_cmd = [
                'docker', 'run',
                '--name', container_id,
                '--rm',  # Automatyczne usunięcie kontenera po zakończeniu
                '-v', f"{temp_dir}:/app",  # Montowanie katalogu z kodem
                '-w', '/app',  # Ustawienie katalogu roboczego
                '--network=none',  # Brak dostępu do sieci
                '--memory=512m',  # Limit pamięci
                '--cpus=1',  # Limit CPU
                'python:3.9-slim',  # Obraz bazowy
                'python', 'code.py'  # Polecenie do wykonania
            ]

            # Dodanie wymaganych pakietów
            required_packages = dependencies_result.get('required_packages', [])
            if required_packages:
                # Utworzenie pliku requirements.txt
                requirements_path = os.path.join(temp_dir, 'requirements.txt')
                with open(requirements_path, 'w') as f:
                    f.write('\n'.join(required_packages))

                # Modyfikacja polecenia Docker, aby najpierw zainstalować zależności
                docker_cmd = [
                    'docker', 'run',
                    '--name', container_id,
                    '--rm',
                    '-v', f"{temp_dir}:/app",
                    '-w', '/app',
                    '--network=host',  # Tymczasowo włączamy sieć do instalacji pakietów
                    '--memory=1024m',  # Zwiększenie limitu pamięci dla instalacji pakietów
                    '--cpus=2',  # Zwiększenie limitów CPU dla szybszej instalacji
                    'python:3.9-slim',
                    'sh', '-c', f"pip install --no-cache-dir -r requirements.txt && python code.py"
                ]

            logger.info(f"Uruchamianie kontenera '{container_id}'...")

            # Uruchomienie kontenera z limitem czasu
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            logger.info(f"Kontener '{container_id}' uruchomiony.")

            return {
                **dependencies_result,
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'exit_code': result.returncode
            }

        except subprocess.TimeoutExpired:
            # Zatrzymanie kontenera, jeśli przekroczono limit czasu
            try:
                subprocess.run(['docker', 'stop', container_id], capture_output=True)
            except Exception:
                pass

            return {
                **dependencies_result,
                'success': False,
                'stdout': '',
                'stderr': f"Przekroczono limit czasu wykonania ({timeout} sekund).",
                'error_type': 'TimeoutError',
                'error_message': f"Execution timed out after {timeout} seconds"
            }

        except Exception as e:
            return {
                **dependencies_result,
                'success': False,
                'stdout': '',
                'stderr': f"Błąd podczas wykonania kodu w Dockerze: {str(e)}",
                'error_type': type(e).__name__,
                'error_message': str(e)
            }

        finally:
            # Usunięcie tymczasowego katalogu
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

            # Upewnienie się, że kontener został zatrzymany i usunięty
            try:
                subprocess.run(['docker', 'stop', container_id], capture_output=True)
                subprocess.run(['docker', 'rm', container_id], capture_output=True)
            except Exception:
                pass


# Funkcja główna do testowania
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
