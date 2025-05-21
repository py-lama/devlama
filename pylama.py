# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from typing import List, Dict, Any, Tuple, Optional
import logging
from pathlib import Path
from dotenv import load_dotenv
from DependencyManager import DependencyManager
from OllamaRunner import OllamaRunner

# Create .pylama directory
PACKAGE_DIR = os.path.join(os.path.expanduser('~'), '.pylama')
os.makedirs(PACKAGE_DIR, exist_ok=True)

# Konfiguracja logowania
log_file = os.path.join(PACKAGE_DIR, 'pylama.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)

logger = logging.getLogger('pylama')
logger.info(f'Logi zapisywane w: {log_file}')

# Załaduj zmienne środowiskowe
load_dotenv()

# Funkcja do instalacji podstawowych zależności
def ensure_basic_dependencies():
    """Sprawdza i instaluje podstawowe zależności potrzebne do działania skryptu."""
    basic_dependencies = ['setuptools', 'requests', 'importlib-metadata', 'python-dotenv']

    for dep in basic_dependencies:
        try:
            # Próba importu, aby sprawdzić czy jest zainstalowany
            if dep == 'setuptools':
                import setuptools
            elif dep == 'requests':
                import requests
            elif dep == 'importlib-metadata':
                try:
                    # Python 3.8+ ma to wbudowane
                    from importlib import metadata
                except ImportError:
                    # Dla starszych wersji Pythona
                    import importlib_metadata
            elif dep == 'python-dotenv':
                from dotenv import load_dotenv
        except ImportError:
            logger.info(f"Instalowanie podstawowej zależności: {dep}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                logger.info(f"Zainstalowano {dep}")
            except subprocess.CalledProcessError:
                logger.error(f"Nie udało się zainstalować {dep}. Przerwanie.")
                sys.exit(1)


# Instalacja podstawowych zależności przed importowaniem pozostałych modułów
ensure_basic_dependencies()



def main():
    """Główna funkcja programu."""
    try:
        # Sprawdź, czy Ollama jest zainstalowana
        try:
            result = subprocess.run([os.environ.get("OLLAMA_PATH", "ollama"), "--version"],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            if result.returncode != 0:
                print("Ollama nie jest prawidłowo zainstalowana.")
                print("Proszę zainstalować Ollama: https://ollama.ai/download")
                return
            print(f"Znaleziono Ollama: {result.stdout.decode('utf-8').strip()}")
        except FileNotFoundError:
            print("Ollama nie jest zainstalowana lub nie jest dostępna w ścieżce systemowej.")
            print("Proszę zainstalować Ollama: https://ollama.ai/download")
            return

        # Utwórz instancje klas
        ollama = OllamaRunner()
        dependency_manager = DependencyManager()

        # Uruchom Ollama
        ollama.start_ollama()

        # Zapytanie takie samo jak w przykładzie
        prompt = "create the sentence as python code: Create screenshot on browser"

        # Wyślij zapytanie do Ollama
        response = ollama.query_ollama(prompt)

        if not response:
            print("Nie otrzymano odpowiedzi od Ollama.")
            return

        print("\nOtrzymano odpowiedź od Ollama. Wyodrębniam kod Python...")

        # Wyodrębnij kod Python z odpowiedzi
        code = ollama.extract_python_code(response)

        if not code:
            print("Nie udało się wyodrębnić kodu Python z odpowiedzi.")
            print("Sprawdź plik 'ollama_response_debug.txt' lub 'ollama_raw_response.json' dla pełnej odpowiedzi.")
            return

        print("\nWyodrębniony kod Python:")
        print("-" * 40)
        print(code)
        print("-" * 40)

        # Zapisz kod do pliku w katalogu .pylama
        code_file = ollama.save_code_to_file(code, os.path.join(PACKAGE_DIR, 'generated_script.py'))
        print(f"\nKod zapisany do pliku: {code_file}")

        # Znajdź i zainstaluj zależności
        modules = dependency_manager.extract_imports(code)
        installed, missing = dependency_manager.check_dependencies(modules)

        print(f"\nZnalezione moduły: {', '.join(modules) if modules else 'brak'}")
        print(f"Zainstalowane moduły: {', '.join(installed) if installed else 'brak'}")

        if missing:
            print(f"Brakujące zależności: {', '.join(missing)}")
            if not dependency_manager.install_dependencies(missing):
                print("Przerwano wykonywanie skryptu z powodu błędu instalacji zależności.")
                return
        else:
            print("Wszystkie zależności są już zainstalowane")

        # Automatycznie uruchom kod z debugowaniem
        ollama.run_code_with_debug(code_file, prompt, code)

    except Exception as e:
        print(f"Wystąpił błąd: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Zatrzymaj Ollama jeśli została uruchomiona przez ten skrypt
        if 'ollama' in locals():
            ollama.stop_ollama()


if __name__ == "__main__":
    # Sprawdź czy skrypt jest uruchomiony bezpośrednio (nie zaimportowany)
    # Najpierw zainstaluj podstawowe zależności
    ensure_basic_dependencies()
    main()