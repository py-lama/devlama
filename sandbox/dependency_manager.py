#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moduu0142 do zarzu0105dzania zaleu017cnou015bciami i instalacji pakietu00f3w.
"""

import sys
import subprocess
import logging
from typing import Dict, List, Any, Optional, Tuple

from sandbox.code_analyzer import CodeAnalyzer

# Konfiguracja loggera
logger = logging.getLogger(__name__)

# Pru00f3ba importu opcjonalnych moduu0142u00f3w
try:
    import pkg_resources
except ImportError:
    logger.warning("Moduu0142 pkg_resources nie jest dostu0119pny. Niektu00f3re funkcje mogu0105 byu0107 ograniczone.")
    pkg_resources = None


class DependencyManager:
    """Klasa do zarzu0105dzania zaleu017cnou015bciami i instalacji pakietu00f3w."""

    def __init__(self):
        self.analyzer = CodeAnalyzer()
        self.module_to_package = self._create_module_package_mapping()

    def _create_module_package_mapping(self) -> Dict[str, str]:
        """Tworzy mapowanie popularnych moduu0142u00f3w do nazw pakietu00f3w.

        Returns:
            Dict[str, str]: Mapowanie moduu0142u00f3w do nazw pakietu00f3w.
        """
        # Mapowanie popularnych moduu0142u00f3w do nazw pakietu00f3w
        return {
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
            'lightkurve': 'lightkurve'
        }

    def analyze_dependencies(self, code: str) -> Dict[str, Any]:
        """Analizuje zaleu017cnou015bci w kodzie Python.

        Args:
            code: Kod Python do analizy.

        Returns:
            Dict[str, Any]: Wyniki analizy zaleu017cnou015bci.
        """
        try:
            analysis_result = self.analyzer.analyze_code(code)
            required_modules = analysis_result.get('required_packages', [])

            # Mapowanie moduu0142u00f3w na pakiety
            required_packages = []
            for module in required_modules:
                package = self.module_to_package.get(module, module)
                if package not in required_packages:
                    required_packages.append(package)

            # Sprawdzenie zainstalowanych pakietu00f3w
            installed_packages = []
            missing_packages = []

            for package in required_packages:
                if self.check_package_installed(package):
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
            logger.error(f"Bu0142u0105d podczas analizy zaleu017cnou015bci: {e}")
            return {
                'imports': {},
                'required_packages': [],
                'installed_packages': [],
                'missing_packages': [],
                'installed_packages_count': 0,
                'error': str(e)
            }

    def install_package(self, package_name: str) -> bool:
        """Instaluje pakiet Python za pomocu0105 pip.

        Args:
            package_name: Nazwa pakietu do zainstalowania.

        Returns:
            bool: True, jeu015bli instalacja siu0119 powiodu0142a, False w przeciwnym razie.
        """
        try:
            logger.info(f"Instalowanie pakietu: {package_name}")

            # Uu017cyj pip do instalacji pakietu
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package_name],
                capture_output=True,
                text=True,
                check=True
            )

            logger.info(f"Pakiet {package_name} zainstalowany pomu015blnie.")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Bu0142u0105d podczas instalacji pakietu {package_name}: {e}")
            return False

        except Exception as e:
            logger.error(f"Nieoczekiwany bu0142u0105d podczas instalacji pakietu {package_name}: {e}")
            return False

    def check_package_installed(self, package_name: str) -> bool:
        """Sprawdza, czy pakiet jest zainstalowany.

        Args:
            package_name: Nazwa pakietu do sprawdzenia.

        Returns:
            bool: True, jeu015bli pakiet jest zainstalowany, False w przeciwnym razie.
        """
        try:
            # Pru00f3ba importu moduu0142u
            __import__(package_name)
            return True
        except ImportError:
            pass

        # Sprawdzenie za pomocu0105 pkg_resources
        if pkg_resources is not None:
            try:
                pkg_resources.get_distribution(package_name)
                return True
            except pkg_resources.DistributionNotFound:
                pass

        # Sprawdzenie za pomocu0105 pip list
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

    def install_dependencies(self, packages: List[str]) -> bool:
        """Instaluje liste pakietu00f3w.

        Args:
            packages: Lista nazw pakietu00f3w do zainstalowania.

        Returns:
            bool: True, jeu015bli wszystkie pakiety zostu0142y zainstalowane, False w przeciwnym razie.
        """
        if not packages:
            return True

        logger.info(f"Instalowanie zaleu017cnou015bci: {', '.join(packages)}")
        success = True

        for package in packages:
            if not self.install_package(package):
                success = False

        return success

    def extract_imports(self, code: str) -> List[str]:
        """Wyodru0119bnia nazwy importowanych moduu0142u00f3w z kodu.

        Args:
            code: Kod Python do analizy.

        Returns:
            List[str]: Lista nazw importowanych moduu0142u00f3w.
        """
        analysis_result = self.analyzer.analyze_code(code)
        return analysis_result.get('required_packages', [])

    def check_dependencies(self, modules: List[str]) -> Tuple[List[str], List[str]]:
        """Sprawdza, ktu00f3re z podanych moduu0142u00f3w su0105 zainstalowane.

        Args:
            modules: Lista nazw moduu0142u00f3w do sprawdzenia.

        Returns:
            Tuple[List[str], List[str]]: Krotka zawieraju0105ca liste zainstalowanych i brakuju0105cych moduu0142u00f3w.
        """
        installed = []
        missing = []

        for module in modules:
            package = self.module_to_package.get(module, module)
            if self.check_package_installed(package):
                installed.append(module)
            else:
                missing.append(module)

        return installed, missing
