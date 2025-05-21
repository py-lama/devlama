#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moduu0142 do bezpiecznego uruchamiania kodu Python w kontenerze Docker.
"""

import os
import sys
import ast
import uuid
import shutil
import tempfile
import subprocess
import logging
from typing import Dict, Any, Optional

from sandbox.dependency_manager import DependencyManager

# Konfiguracja loggera
logger = logging.getLogger(__name__)


class DockerSandbox:
    """Klasa do bezpiecznego uruchamiania kodu Python w kontenerze Docker."""

    def __init__(self, base_image: str = "python:3.9-slim"):
        self.dependency_manager = DependencyManager()
        self.base_image = base_image
        self._check_docker_installed()

    def _check_docker_installed(self) -> bool:
        """Sprawdza, czy Docker jest zainstalowany w systemie.

        Returns:
            bool: True, jeu015bli Docker jest zainstalowany, False w przeciwnym razie.
        """
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Docker zainstalowany: {result.stdout.strip()}")
                return True
            else:
                logger.warning("Docker nie jest zainstalowany lub nie dziau0142a poprawnie.")
                return False
        except Exception as e:
            logger.error(f"Bu0142u0105d podczas sprawdzania instalacji Dockera: {e}")
            return False

    def run_code(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Uruchamia kod Python w bezpiecznym u015brodowisku Docker.

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

        # Uruchomienie kodu w kontenerze Docker
        return self._run_in_docker(code, timeout, dependencies_result)

    def _run_in_docker(self, code: str, timeout: int, dependencies_result: Dict[str, Any]) -> Dict[str, Any]:
        """Uruchamia kod w kontenerze Docker.

        Args:
            code: Kod Python do uruchomienia.
            timeout: Limit czasu wykonania w sekundach.
            dependencies_result: Wyniki analizy zaleu017cnou015bci.

        Returns:
            Dict[str, Any]: Wyniki wykonania kodu.
        """
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
                '--rm',  # Automatyczne usuniu0119cie kontenera po zakou0144czeniu
                '-v', f"{temp_dir}:/app",  # Montowanie katalogu z kodem
                '-w', '/app',  # Ustawienie katalogu roboczego
                '--network=none',  # Brak dostu0119pu do sieci
                '--memory=512m',  # Limit pamiu0119ci
                '--cpus=1',  # Limit CPU
                self.base_image,  # Obraz bazowy
                'python', 'code.py'  # Polecenie do wykonania
            ]

            # Dodanie wymaganych pakietu00f3w
            required_packages = dependencies_result.get('required_packages', [])
            if required_packages:
                # Utworzenie pliku requirements.txt
                requirements_path = os.path.join(temp_dir, 'requirements.txt')
                with open(requirements_path, 'w') as f:
                    f.write('\n'.join(required_packages))

                # Modyfikacja polecenia Docker, aby najpierw zainstalowau0107 zaleu017cnou015bci
                docker_cmd = [
                    'docker', 'run',
                    '--name', container_id,
                    '--rm',
                    '-v', f"{temp_dir}:/app",
                    '-w', '/app',
                    '--network=host',  # Tymczasowo wu0142u0105czamy sieu0107 do instalacji pakietu00f3w
                    '--memory=1024m',  # Zwiu0119kszenie limitu pamiu0119ci dla instalacji pakietu00f3w
                    '--cpus=2',  # Zwiu0119kszenie limitu00f3w CPU dla szybszej instalacji
                    self.base_image,
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
            # Zatrzymanie kontenera, jeu015bli przekroczono limit czasu
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
                'stderr': f"Bu0142u0105d podczas wykonania kodu w Dockerze: {str(e)}",
                'error_type': type(e).__name__,
                'error_message': str(e)
            }

        finally:
            # Usuniu0119cie tymczasowego katalogu
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

            # Upewnienie siu0119, u017ce kontener zostau0142 zatrzymany i usuniu0119ty
            try:
                subprocess.run(['docker', 'stop', container_id], capture_output=True)
                subprocess.run(['docker', 'rm', container_id], capture_output=True)
            except Exception:
                pass

    def start_container(self, image: Optional[str] = None) -> bool:
        """Uruchamia kontener Docker z podanym obrazem.

        Args:
            image: Nazwa obrazu Docker do uruchomienia. Jeu015bli nie podano, uu017cywany jest obraz bazowy.

        Returns:
            bool: True, jeu015bli kontener zostau0142 uruchomiony, False w przeciwnym razie.
        """
        try:
            container_image = image or self.base_image
            logger.info(f"Uruchamianie kontenera z obrazem {container_image}...")

            # Sprawdzenie, czy obraz istnieje lokalnie
            check_image = subprocess.run(
                ['docker', 'image', 'inspect', container_image],
                capture_output=True,
                text=True
            )

            # Jeu015bli obraz nie istnieje, pobierz go
            if check_image.returncode != 0:
                logger.info(f"Pobieranie obrazu {container_image}...")
                pull_result = subprocess.run(
                    ['docker', 'pull', container_image],
                    capture_output=True,
                    text=True
                )
                if pull_result.returncode != 0:
                    logger.error(f"Nie udau0142o siu0119 pobrau0107 obrazu {container_image}: {pull_result.stderr}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Bu0142u0105d podczas uruchamiania kontenera: {e}")
            return False

    def stop_container(self, container_id: Optional[str] = None) -> bool:
        """Zatrzymuje kontener Docker.

        Args:
            container_id: ID kontenera do zatrzymania. Jeu015bli nie podano, zatrzymywane su0105 wszystkie kontenery pylama-sandbox.

        Returns:
            bool: True, jeu015bli kontener zostau0142 zatrzymany, False w przeciwnym razie.
        """
        try:
            if container_id:
                logger.info(f"Zatrzymywanie kontenera {container_id}...")
                stop_result = subprocess.run(
                    ['docker', 'stop', container_id],
                    capture_output=True,
                    text=True
                )
                return stop_result.returncode == 0
            else:
                # Znajdu017a wszystkie kontenery pylama-sandbox
                find_cmd = [
                    'docker', 'ps', '-a',
                    '--filter', 'name=pylama-sandbox',
                    '--format', '{{.ID}}'
                ]
                find_result = subprocess.run(find_cmd, capture_output=True, text=True)
                
                if find_result.stdout.strip():
                    container_ids = find_result.stdout.strip().split('\n')
                    for cid in container_ids:
                        if cid:
                            logger.info(f"Zatrzymywanie kontenera {cid}...")
                            subprocess.run(['docker', 'stop', cid], capture_output=True)
                            subprocess.run(['docker', 'rm', cid], capture_output=True)
                    return True
                return True  # Brak konteneru00f3w do zatrzymania

        except Exception as e:
            logger.error(f"Bu0142u0105d podczas zatrzymywania kontenera: {e}")
            return False
