#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for analyzing Python code and detecting dependencies.
"""

import sys
import ast
import importlib.util
import logging
from typing import Dict, Any, Set

# Logger configuration
logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Class for analyzing Python code and detecting dependencies."""

    def __init__(self):
        # Standard Python modules
        self.std_lib_modules = set(sys.builtin_module_names)

        # Add other standard modules
        for module in sys.modules:
            if module and '.' not in module:
                self.std_lib_modules.add(module)

        # Add additional standard modules
        self._add_standard_libraries()

    def _add_standard_libraries(self) -> None:
        """Dodaje znane standardowe biblioteki do listy."""
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
        """Analizuje kod Python i wykrywa importowane moduu0142y.

        Args:
            code: Kod Python do analizy.

        Returns:
            Dict[str, Any]: Wyniki analizy zawieraju0105ce informacje o importach.
        """
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

            # Filtrowanie i kategoryzacja importu00f3w
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
            logger.error(f"Bu0142u0105d sku0142adni w kodzie: {e}")
            return {
                'imports': {},
                'standard_library': [],
                'third_party': [],
                'unknown': [],
                'required_packages': [],
                'error': str(e)
            }

        except Exception as e:
            logger.error(f"Bu0142u0105d podczas analizy kodu: {e}")
            return {
                'imports': {},
                'standard_library': [],
                'third_party': [],
                'unknown': [],
                'required_packages': [],
                'error': str(e)
            }

    def _classify_module(self, module_name: str) -> str:
        """Klasyfikuje moduu0142 jako standardowy, zewnu0119trzny lub nieznany.

        Args:
            module_name: Nazwa moduu0142u do klasyfikacji.

        Returns:
            str: Kategoria moduu0142u ('standard_library', 'third_party' lub 'unknown').
        """
        if module_name in self.std_lib_modules:
            return 'standard_library'

        try:
            spec = importlib.util.find_spec(module_name)
            if spec is not None:
                return 'third_party'
        except (ImportError, ValueError):
            pass

        return 'unknown'

    def get_standard_libraries(self) -> Set[str]:
        """Zwraca zestaw nazw standardowych bibliotek.

        Returns:
            Set[str]: Zestaw nazw standardowych bibliotek.
        """
        return self.std_lib_modules.copy()
