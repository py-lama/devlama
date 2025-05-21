#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ulepszona wersja modułu sandbox z dodatkowymi funkcjami i lepszą obsługą błędów.

Ten moduł zapewnia rozszerzoną funkcjonalność w porównaniu do oryginalnego modułu sandbox.py,
jednocześnie zachowując kompatybilność wsteczną.
"""

import os
import sys
import logging
import tempfile
import traceback
import subprocess
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

# Import komponentów z pakietu sandbox
from sandbox.code_analyzer import CodeAnalyzer
from sandbox.dependency_manager import DependencyManager
from sandbox.python_sandbox import PythonSandbox
from sandbox.docker_sandbox import DockerSandbox
from sandbox.sandbox_manager import SandboxManager
from sandbox.utils import get_system_info, format_execution_result, ensure_dependencies

# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class EnhancedSandboxManager(SandboxManager):
    """
    Rozszerzona wersja SandboxManager z dodatkowymi funkcjami i lepszą obsługą błędów.
    """

    def __init__(self, use_docker: bool = None):
        """
        Inicjalizuje EnhancedSandboxManager.

        Args:
            use_docker: Czy używać Dockera do uruchamiania kodu. Jeśli None, wartość zostanie
                        pobrana ze zmiennej środowiskowej USE_DOCKER.
        """
        super().__init__(use_docker)
        self.code_analyzer = CodeAnalyzer()
        self.dependency_manager = DependencyManager()

    def run_code_with_retry(self, code: str, timeout: int = 30, max_retries: int = 3) -> Dict[str, Any]:
        """
        Uruchamia kod Python z automatycznym ponowieniem próby w przypadku błędów zależności.

        Args:
            code: Kod Python do uruchomienia.
            timeout: Limit czasu wykonania w sekundach.
            max_retries: Maksymalna liczba ponownych prób w przypadku błędów zależności.

        Returns:
            Dict[str, Any]: Wyniki wykonania kodu.
        """
        result = None
        retries = 0
        missing_deps = []

        while retries < max_retries:
            # Analizuj kod i zainstaluj zależności
            deps_analysis = self.dependency_manager.analyze_dependencies(code)
            missing_deps = deps_analysis.get('missing_packages', [])

            if missing_deps:
                logger.info(f"Instalowanie brakujących zależności: {', '.join(missing_deps)}")
                for pkg in missing_deps:
                    self.dependency_manager.install_package(pkg)

            # Uruchom kod
            result = self.run_code(code, timeout)

            # Sprawdź, czy wystąpiły błędy związane z zależnościami
            if result['success'] or 'ModuleNotFoundError' not in result.get('error', ''):
                break

            # Wyodrębnij nazwę brakującego modułu z błędu
            error_msg = result.get('error', '')
            import_error_match = None

            if 'ModuleNotFoundError: No module named' in error_msg:
                # Przykład: ModuleNotFoundError: No module named 'numpy'
                import_name = error_msg.split("'")
                if len(import_name) >= 2:
                    import_error_match = import_name[1]

            if import_error_match and import_error_match not in missing_deps:
                logger.info(f"Wykryto brakujący moduł: {import_error_match}")
                self.dependency_manager.install_package(import_error_match)
                missing_deps.append(import_error_match)

            retries += 1
            logger.info(f"Ponowna próba uruchomienia kodu ({retries}/{max_retries})")

        # Dodaj informacje o zainstalowanych zależnościach do wyniku
        if result:
            result['installed_dependencies'] = missing_deps

        return result

    def run_code_with_callback(self, code: str, callback: Callable[[Dict[str, Any]], None],
                               timeout: int = 30) -> None:
        """
        Uruchamia kod Python i wywołuje funkcję callback z wynikami.

        Args:
            code: Kod Python do uruchomienia.
            callback: Funkcja, która zostanie wywołana z wynikami wykonania kodu.
            timeout: Limit czasu wykonania w sekundach.
        """
        result = self.run_code_with_retry(code, timeout)
        callback(result)

    def run_code_in_file(self, file_path: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Uruchamia kod Python z pliku.

        Args:
            file_path: Ścieżka do pliku z kodem Python.
            timeout: Limit czasu wykonania w sekundach.

        Returns:
            Dict[str, Any]: Wyniki wykonania kodu.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            return self.run_code_with_retry(code, timeout)
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': traceback.format_exc(),
                'execution_time': 0
            }

    def run_interactive_session(self, initial_code: str = "") -> None:
        """
        Uruchamia interaktywną sesję Python z możliwością wykonywania kodu.

        Args:
            initial_code: Kod Python do wykonania na początku sesji.
        """
        print("=== Interaktywna sesja Python ===")
        print("Wpisz 'exit()' lub 'quit()' aby zakończyć sesję.")
        print("Wpisz 'help()' aby uzyskać pomoc.")

        # Wykonaj początkowy kod, jeśli istnieje
        if initial_code:
            print("\nWykonywanie początkowego kodu:")
            result = self.run_code_with_retry(initial_code)
            if result['stdout']:
                print(result['stdout'])
            if result['stderr']:
                print(f"Błędy:\n{result['stderr']}")

        # Główna pętla interaktywna
        context = {}
        while True:
            try:
                user_input = input(">>> ")

                if user_input.lower() in ('exit()', 'quit()'):
                    break
                elif user_input.lower() == 'help()':
                    print("\nPomoc interaktywnej sesji Python:")
                    print("  exit(), quit() - Zakończ sesję")
                    print("  help() - Wyświetl tę pomoc")
                    print("  clear() - Wyczyść ekran")
                    print("  reset() - Zresetuj kontekst sesji")
                    continue
                elif user_input.lower() == 'clear()':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue
                elif user_input.lower() == 'reset()':
                    context = {}
                    print("Kontekst sesji został zresetowany.")
                    continue

                # Wykonaj kod użytkownika
                result = self.run_code_with_retry(user_input)
                if result['stdout']:
                    print(result['stdout'])
                if result['stderr']:
                    print(f"Błędy:\n{result['stderr']}")

            except KeyboardInterrupt:
                print("\nPrzerwano przez użytkownika. Wpisz 'exit()' aby zakończyć sesję.")
            except Exception as e:
                print(f"Błąd: {str(e)}")

        print("\nSesja zakończona.")


# Utworzenie instancji EnhancedSandboxManager dla kompatybilności wstecznej
_enhanced_sandbox_manager = EnhancedSandboxManager.from_env()


# Funkcje dla kompatybilności wstecznej i nowe funkcje

def run_code_with_retry(code: str, timeout: int = 30, max_retries: int = 3) -> Dict[str, Any]:
    """
    Uruchamia kod Python z automatycznym ponowieniem próby w przypadku błędów zależności.

    Args:
        code: Kod Python do uruchomienia.
        timeout: Limit czasu wykonania w sekundach.
        max_retries: Maksymalna liczba ponownych prób w przypadku błędów zależności.

    Returns:
        Dict[str, Any]: Wyniki wykonania kodu.
    """
    return _enhanced_sandbox_manager.run_code_with_retry(code, timeout, max_retries)


def run_code_in_file(file_path: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Uruchamia kod Python z pliku.

    Args:
        file_path: Ścieżka do pliku z kodem Python.
        timeout: Limit czasu wykonania w sekundach.

    Returns:
        Dict[str, Any]: Wyniki wykonania kodu.
    """
    return _enhanced_sandbox_manager.run_code_in_file(file_path, timeout)


def run_interactive_session(initial_code: str = "") -> None:
    """
    Uruchamia interaktywną sesję Python z możliwością wykonywania kodu.

    Args:
        initial_code: Kod Python do wykonania na początku sesji.
    """
    _enhanced_sandbox_manager.run_interactive_session(initial_code)


# Funkcja główna do testowania
def main():
    """
    Funkcja główna do testowania modułu sandbox_new.
    """
    print("=== Test modułu sandbox_new ===\n")

    # Przykładowy kod do testu
    code = """
import os
import sys
import math
import platform

print('Informacje o systemie:')
print(f'System operacyjny: {platform.system()} {platform.release()}')
print(f'Wersja Pythona: {sys.version}')
print(f'Katalog bieżący: {os.getcwd()}')

# Przykład obliczeń matematycznych
print('\nObliczenia matematyczne:')
print(f'Pi: {math.pi}')
print(f'Pierwiastek z 16: {math.sqrt(16)}')
print(f'Silnia z 5: {math.factorial(5)}')
"""

    # Uruchomienie kodu z automatycznym ponowieniem próby
    print("Uruchamianie kodu z automatycznym ponowieniem próby:")
    result = run_code_with_retry(code)
    print(f"Sukces: {result['success']}")
    print(f"Standardowe wyjście:\n{result['stdout']}")

    # Zapisz kod do pliku tymczasowego i uruchom go
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name

    print("\nUruchamianie kodu z pliku:")
    result = run_code_in_file(temp_path)
    print(f"Sukces: {result['success']}")
    print(f"Standardowe wyjście:\n{result['stdout']}")

    # Usuń plik tymczasowy
    os.unlink(temp_path)

    print("\nTest zakończony.")

    # Zapytaj użytkownika, czy chce uruchomić interaktywną sesję
    choice = input("\nCzy chcesz uruchomić interaktywną sesję? (t/n): ")
    if choice.lower() in ('t', 'tak', 'y', 'yes'):
        run_interactive_session()


if __name__ == "__main__":
    main()
