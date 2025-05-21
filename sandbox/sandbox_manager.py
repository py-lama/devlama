#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moduu0142 do zarzu0105dzania ru00f3u017cnymi typami sandboxu00f3w.
"""

import os
import logging
from typing import Dict, Any, Optional, Union

from sandbox.python_sandbox import PythonSandbox
from sandbox.docker_sandbox import DockerSandbox
from sandbox.utils import get_system_info, format_execution_result

# Konfiguracja loggera
logger = logging.getLogger(__name__)


class SandboxManager:
    """Klasa do zarzu0105dzania ru00f3u017cnymi typami sandboxu00f3w."""

    def __init__(self, use_docker: bool = False, docker_image: Optional[str] = None):
        """Inicjalizuje menadu017cera sandboxu00f3w.

        Args:
            use_docker: Czy uu017cywau0107 Dockera do uruchamiania kodu.
            docker_image: Nazwa obrazu Docker do uu017cycia (opcjonalnie).
        """
        self.use_docker = use_docker
        self.docker_image = docker_image or "python:3.9-slim"
        
        # Inicjalizacja sandboxu00f3w
        self.python_sandbox = PythonSandbox()
        self.docker_sandbox = DockerSandbox(base_image=self.docker_image) if use_docker else None
        
        # Informacje o systemie
        self.system_info = get_system_info()
        
        logger.info(f"Zainicjalizowano SandboxManager (use_docker={use_docker})")
        if use_docker:
            logger.info(f"Uu017cywany obraz Docker: {self.docker_image}")

    def run_code(self, code: str, timeout: int = 30, force_docker: bool = None) -> Dict[str, Any]:
        """Uruchamia kod Python w odpowiednim sandboxie.

        Args:
            code: Kod Python do uruchomienia.
            timeout: Limit czasu wykonania w sekundach.
            force_docker: Wymusza uu017cycie Dockera (True) lub lokalnego u015brodowiska (False).
                          Jeu015bli None, uu017cywane jest ustawienie z inicjalizacji.

        Returns:
            Dict[str, Any]: Wyniki wykonania kodu.
        """
        use_docker = self.use_docker if force_docker is None else force_docker
        
        if use_docker and self.docker_sandbox:
            logger.info("Uruchamianie kodu w kontenerze Docker...")
            result = self.docker_sandbox.run_code(code, timeout)
        else:
            logger.info("Uruchamianie kodu lokalnie...")
            result = self.python_sandbox.run_code(code, timeout)
        
        return result

    def format_result(self, result: Dict[str, Any]) -> str:
        """Formatuje wynik wykonania kodu do czytelnej postaci.

        Args:
            result: Su0142ownik z wynikami wykonania kodu.

        Returns:
            str: Sformatowany wynik wykonania kodu.
        """
        return format_execution_result(result)

    def get_sandbox(self, use_docker: bool = None) -> Union[PythonSandbox, DockerSandbox]:
        """Zwraca odpowiedni sandbox.

        Args:
            use_docker: Czy zwru00f3ciu0107 sandbox Dockera. Jeu015bli None, uu017cywane jest ustawienie z inicjalizacji.

        Returns:
            Union[PythonSandbox, DockerSandbox]: Instancja sandboxa.
        """
        use_docker = self.use_docker if use_docker is None else use_docker
        
        if use_docker and self.docker_sandbox:
            return self.docker_sandbox
        else:
            return self.python_sandbox

    @staticmethod
    def from_env() -> 'SandboxManager':
        """Tworzy instancju0119 SandboxManager na podstawie zmiennych u015brodowiskowych.

        Returns:
            SandboxManager: Instancja SandboxManager.
        """
        use_docker = os.environ.get('USE_DOCKER', 'False').lower() in ('true', '1', 't')
        docker_image = os.environ.get('DOCKER_IMAGE', 'python:3.9-slim')
        
        return SandboxManager(use_docker=use_docker, docker_image=docker_image)
