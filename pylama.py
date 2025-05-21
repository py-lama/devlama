# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import platform
from typing import List, Dict, Any, Tuple, Optional
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv
from DependencyManager import DependencyManager
from OllamaRunner import OllamaRunner
from templates import get_template

# Create .pylama directory
PACKAGE_DIR = os.path.join(os.path.expanduser('~'), '.pylama')
os.makedirs(PACKAGE_DIR, exist_ok=True)

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels"""
    grey = "\x1b[38;21m"
    blue = "\x1b[34;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    COLORS = {
        logging.DEBUG: blue,
        logging.INFO: grey,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: bold_red
    }
    
    def format(self, record):
        log_fmt = f"%(asctime)s - %(levelname)8s - %(message)s"
        if record.levelno in self.COLORS:
            log_fmt = f"{self.COLORS[record.levelno]}{log_fmt}{self.reset}"
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

# Configure root logger
log_file = os.path.join(PACKAGE_DIR, 'pylama.log')
logger = logging.getLogger('pylama')
logger.setLevel(logging.INFO)

# Create console handler with colored output
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter())

# Create file handler
file_handler = logging.FileHandler(log_file)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)

# Add handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)

logger.info('Application started')
logger.debug(f'Logs directory: {PACKAGE_DIR}')

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



def parse_arguments():
    """Parsuje argumenty wiersza poleceń."""
    parser = argparse.ArgumentParser(description='PyLama - Generator kodu Python z użyciem modeli LLM')
    parser.add_argument('prompt', nargs='*', help='Zadanie do wykonania przez kod Python')
    parser.add_argument('-t', '--template', choices=['basic', 'platform_aware', 'dependency_aware', 'testable', 'secure', 'performance', 'pep8'], 
                        default='platform_aware', help='Typ szablonu do użycia')
    parser.add_argument('-d', '--dependencies', help='Lista dozwolonych zależności (tylko dla template=dependency_aware)')
    parser.add_argument('-m', '--model', help='Nazwa modelu Ollama do użycia')
    return parser.parse_args()

def main():
    """Główna funkcja programu."""
    try:
        # Parsuj argumenty wiersza poleceń
        args = parse_arguments()
        
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
        ollama = OllamaRunner(model=args.model) if args.model else OllamaRunner()
        dependency_manager = DependencyManager()

        # Uruchom Ollama
        ollama.start_ollama()

        # Pobierz zapytanie od użytkownika
        if args.prompt:
            # Jeśli podano argumenty, połącz je w jeden prompt
            prompt = ' '.join(args.prompt)
        else:
            # W przeciwnym razie użyj domyślnego promptu z zmiennych środowiskowych lub zapytaj użytkownika
            prompt = os.environ.get("TEST_PROMPT_1")
            if not prompt:
                prompt = input("Podaj zadanie do wykonania przez kod Python: ")

        # Przygotuj argumenty dla szablonu
        template_args = {}
        
        # Dodaj argumenty specyficzne dla wybranego szablonu
        if args.template == 'platform_aware':
            template_args['platform'] = platform.system()
            template_args['os'] = f"{platform.system()} {platform.release()}"
        elif args.template == 'dependency_aware' and args.dependencies:
            template_args['dependencies'] = args.dependencies
        
        # Wyślij zapytanie do Ollama z użyciem wybranego szablonu
        logger.info(f"Używanie szablonu: {args.template}")
        response = ollama.query_ollama(
            prompt,  # Podstawowe zadanie
            template_type=args.template,  # Użyj wybranego szablonu
            **template_args  # Przekaz dodatkowe argumenty dla szablonu
        )

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