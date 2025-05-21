#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import tempfile
import shutil
import logging
import time
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from dotenv import load_dotenv

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sandbox.log')
    ]
)

logger = logging.getLogger('sandbox_docker')

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()


class DockerSandbox:
    """Klasa do uruchamiania kodu w bezpiecznym środowisku Docker."""

    def __init__(self):
        """Inicjalizacja środowiska sandbox."""
        self.docker_image = os.getenv('DOCKER_IMAGE', 'ollama/ollama:latest')
        self.container_name = os.getenv('DOCKER_CONTAINER_NAME', 'pylama-sandbox')
        self.docker_port = os.getenv('DOCKER_PORT', '11434')
        self.log_dir = os.getenv('LOG_DIR', './logs')
        self.output_dir = os.getenv('OUTPUT_DIR', './output')

        # Upewnij się, że katalogi istnieją
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        # Sprawdź, czy Docker jest zainstalowany
        self._check_docker_installation()

    def _check_docker_installation(self) -> None:
        """Sprawdza, czy Docker jest zainstalowany i dostępny."""
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
                raise RuntimeError("Docker nie jest zainstalowany lub dostępny.")

            logger.info(f"Docker zainstalowany: {result.stdout.strip()}")
        except FileNotFoundError:
            logger.error("Docker nie jest zainstalowany lub nie jest dostępny w ścieżce systemowej.")
            raise RuntimeError("Docker nie jest zainstalowany.")

    def is_container_running(self) -> bool:
        """Sprawdza, czy kontener Docker jest już uruchomiony."""
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
        """Uruchamia kontener Docker z Ollama, jeśli nie jest już uruchomiony."""
        if self.is_container_running():
            logger.info(f"Kontener '{self.container_name}' już działa.")
            return True

        logger.info(f"Uruchamianie kontenera '{self.container_name}'...")

        try:
            # Najpierw sprawdź, czy obrazu nie trzeba pobrać
            result = subprocess.run(
                ['docker', 'image', 'inspect', self.docker_image],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )

            if result.returncode != 0:
                logger.info(f"Pobieranie obrazu Docker '{self.docker_image}'...")
                pull_result = subprocess.run(
                    ['docker', 'pull', self.docker_image],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                    text=True
                )
                logger.info(f"Obraz Docker pobrany: {self.docker_image}")

            # Uruchom kontener
            run_result = subprocess.run(
                [
                    'docker', 'run',
                    '--name', self.container_name,
                    '-d',  # Uruchom w tle
                    '-p', f'{self.docker_port}:11434',  # Przekierowanie portu
                    '--rm',  # Usuń kontener po zatrzymaniu
                    '-v', f'{os.path.abspath(self.output_dir)}:/output',  # Montowanie katalogu wyjściowego
                    self.docker_image
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True
            )

            if run_result.returncode != 0:
                logger.error(f"Błąd podczas uruchamiania kontenera: {run_result.stderr}")
                return False

            # Daj kontenerowi czas na uruchomienie
            logger.info("Czekanie na uruchomienie kontenera...")
            time.sleep(5)

            # Sprawdź czy faktycznie działa
            if self.is_container_running():
                logger.info(f"Kontener '{self.container_name}' uruchomiony pomyślnie.")
                return True
            else:
                logger.error("Kontener nie uruchomił się poprawnie.")
                return False

        except subprocess.CalledProcessError as e:
            logger.error(f"Błąd podczas uruchamiania kontenera Docker: {e}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd: {e}")
            return False

    def stop_container(self) -> bool:
        """Zatrzymuje kontener Docker, jeśli jest uruchomiony."""
        if not self.is_container_running():
            logger.info(f"Kontener '{self.container_name}' nie jest uruchomiony.")
            return True

        logger.info(f"Zatrzymywanie kontenera '{self.container_name}'...")

        try:
            result = subprocess.run(
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
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd: {e}")
            return False

    def execute_code(self, code: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """
        Wykonuje kod Python w kontenerze Docker.

        Args:
            code: Kod Python do wykonania
            timeout: Limit czasu wykonania w sekundach

        Returns:
            Tuple zawierający (sukces, stdout, stderr)
        """
        if not self.is_container_running():
            if not self.start_container():
                return False, "", "Nie udało się uruchomić kontenera Docker."

        # Utwórz tymczasowy plik z kodem
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(code)
            temp_filename = temp_file.name

        try:
            # Kopiuj plik do kontenera
            container_filename = f"/tmp/{os.path.basename(temp_filename)}"
            copy_result = subprocess.run(
                ['docker', 'cp', temp_filename, f"{self.container_name}:{container_filename}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True
            )

            if copy_result.returncode != 0:
                return False, "", f"Błąd podczas kopiowania pliku do kontenera: {copy_result.stderr}"

            # Wykonaj kod w kontenerze
            run_result = subprocess.run(
                [
                    'docker', 'exec',
                    self.container_name,
                    'python3', container_filename
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True,
                timeout=timeout
            )

            success = run_result.returncode == 0
            stdout = run_result.stdout
            stderr = run_result.stderr

            # Zapisz logi
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            log_file = os.path.join(self.log_dir, f"execution-{timestamp}.log")

            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== KOD ===\n{code}\n\n")
                f.write(f"=== STDOUT ===\n{stdout}\n\n")
                f.write(f"=== STDERR ===\n{stderr}\n\n")
                f.write(f"=== STATUS ===\n{'Sukces' if success else 'Błąd'} (kod wyjścia: {run_result.returncode})")

            return success, stdout, stderr

        except subprocess.TimeoutExpired:
            return False, "", f"Przekroczony limit czasu wykonania ({timeout}s)"
        except Exception as e:
            logger.error(f"Błąd podczas wykonywania kodu: {e}")
            return False, "", str(e)
        finally:
            # Usuń tymczasowy plik
            try:
                os.unlink(temp_filename)
            except Exception:
                pass

    def install_dependencies(self, packages: List[str]) -> Tuple[bool, str, str]:
        """
        Instaluje zależności w kontenerze Docker.

        Args:
            packages: Lista pakietów do zainstalowania

        Returns:
            Tuple zawierający (sukces, stdout, stderr)
        """
        if not packages:
            return True, "", ""

        if not self.is_container_running():
            if not self.start_container():
                return False, "", "Nie udało się uruchomić kontenera Docker."

        try:
            packages_str = ' '.join(packages)
            install_cmd = f"pip install {packages_str}"

            run_result = subprocess.run(
                [
                    'docker', 'exec',
                    self.container_name,
                    'bash', '-c', install_cmd
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True,
                timeout=180  # Dłuższy timeout dla instalacji pakietów
            )

            success = run_result.returncode == 0
            stdout = run_result.stdout
            stderr = run_result.stderr

            # Zapisz logi
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            log_file = os.path.join(self.log_dir, f"pip-install-{timestamp}.log")

            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== INSTALACJA PAKIETÓW ===\n{packages_str}\n\n")
                f.write(f"=== STDOUT ===\n{stdout}\n\n")
                f.write(f"=== STDERR ===\n{stderr}\n\n")
                f.write(f"=== STATUS ===\n{'Sukces' if success else 'Błąd'} (kod wyjścia: {run_result.returncode})")

            if success:
                logger.info(f"Pakiety zainstalowane pomyślnie: {packages_str}")
            else:
                logger.error(f"Błąd podczas instalacji pakietów: {stderr}")

            return success, stdout, stderr

        except subprocess.TimeoutExpired:
            return False, "", "Przekroczony limit czasu instalacji pakietów (180s)"
        except Exception as e:
            logger.error(f"Błąd podczas instalacji pakietów: {e}")
            return False, "", str(e)

    def pull_ollama_model(self, model_name: str) -> Tuple[bool, str, str]:
        """
        Pobiera model Ollama w kontenerze Docker.

        Args:
            model_name: Nazwa modelu do pobrania

        Returns:
            Tuple zawierający (sukces, stdout, stderr)
        """
        if not self.is_container_running():
            if not self.start_container():
                return False, "", "Nie udało się uruchomić kontenera Docker."

        try:
            run_result = subprocess.run(
                [
                    'docker', 'exec',
                    self.container_name,
                    'ollama', 'pull', model_name
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True,
                timeout=600  # Dłuższy timeout dla pobierania modelu (10 minut)
            )

            success = run_result.returncode == 0
            stdout = run_result.stdout
            stderr = run_result.stderr

            # Zapisz logi
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            log_file = os.path.join(self.log_dir, f"ollama-pull-{model_name}-{timestamp}.log")

            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== POBIERANIE MODELU ===\n{model_name}\n\n")
                f.write(f"=== STDOUT ===\n{stdout}\n\n")
                f.write(f"=== STDERR ===\n{stderr}\n\n")
                f.write(f"=== STATUS ===\n{'Sukces' if success else 'Błąd'} (kod wyjścia: {run_result.returncode})")

            if success:
                logger.info(f"Model '{model_name}' pobrany pomyślnie.")
            else:
                logger.error(f"Błąd podczas pobierania modelu '{model_name}': {stderr}")

            return success, stdout, stderr

        except subprocess.TimeoutExpired:
            return False, "", f"Przekroczony limit czasu pobierania modelu '{model_name}' (600s)"
        except Exception as e:
            logger.error(f"Błąd podczas pobierania modelu: {e}")
            return False, "", str(e)


# Przykład użycia
if __name__ == "__main__":
    sandbox = DockerSandbox()

    try:
        # Uruchom kontener
        if not sandbox.start_container():
            sys.exit(1)

        # Testowy kod Python
        test_code = """
import os
import platform
import sys

print("=== Informacje o środowisku ===")
print(f"Python: {sys.version}")
print(f"Platforma: {platform.platform()}")
print(f"Katalogi: {os.listdir('/')}")
print("=== Koniec ===")
"""

        # Wykonaj kod
        success, stdout, stderr = sandbox.execute_code(test_code)

        print("\n=== Wyniki testu ===")
        print(f"Sukces: {success}")
        print(f"STDOUT:\n{stdout}")

        if stderr:
            print(f"STDERR:\n{stderr}")

    finally:
        # Zatrzymaj kontener
        sandbox.stop_container()