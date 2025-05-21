#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moduu0142 do bezpiecznego uruchamiania kodu Python w lokalnym u015brodowisku.
"""

import os
import sys
import ast
import tempfile
import subprocess
import logging
from typing import Dict, Any

from sandbox.dependency_manager import DependencyManager

# Konfiguracja loggera
logger = logging.getLogger(__name__)


class PythonSandbox:
    """Klasa do bezpiecznego uruchamiania kodu Python w lokalnym u015brodowisku."""

    def __init__(self):
        self.dependency_manager = DependencyManager()

    def run_code(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Uruchamia kod Python w bezpiecznym u015brodowisku.

        Args:
            code: Kod Python do uruchomienia.
            timeout: Limit czasu wykonania w sekundach.

        Returns:
            Dict[str, Any]: Wyniki wykonania kodu.
        """
        # Analiza zaleu017cnou015bci
        dependencies_result = self.dependency_manager.analyze_dependencies(code)

        # Sprawdzenie, czy kod ma bu0142u0119dy sku0142adni
        try:
            ast.parse(code)
        except SyntaxError as e:
            logger.error(f"Bu0142u0105d sku0142adni w kodzie: {e}")
            return {
                **dependencies_result,
                'success': False,
                'stdout': '',
                'stderr': f"Bu0142u0105d sku0142adni: {str(e)}",
                'error_type': 'SyntaxError',
                'error_message': str(e)
            }

        # Uruchomienie kodu lokalnie
        return self._run_locally(code, timeout, dependencies_result)

    def _run_locally(self, code: str, timeout: int, dependencies_result: Dict[str, Any]) -> Dict[str, Any]:
        """Uruchamia kod lokalnie w podprocesie.

        Args:
            code: Kod Python do uruchomienia.
            timeout: Limit czasu wykonania w sekundach.
            dependencies_result: Wyniki analizy zaleu017cnou015bci.

        Returns:
            Dict[str, Any]: Wyniki wykonania kodu.
        """
        # Utworzenie tymczasowego pliku z kodem
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name

        try:
            # Instalacja brakuju0105cych zaleu017cnou015bci
            missing_packages = dependencies_result.get('missing_packages', [])
            if missing_packages:
                logger.info(f"Instalowanie brakuju0105cych zaleu017cnou015bci: {', '.join(missing_packages)}")
                for package in missing_packages:
                    self.dependency_manager.install_package(package)

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
                'stderr': f"Bu0142u0105d podczas wykonania kodu: {str(e)}",
                'error_type': type(e).__name__,
                'error_message': str(e)
            }

        finally:
            # Usunięcie tymczasowego pliku
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
