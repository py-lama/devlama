import os
import json
import time
import subprocess
import sys
import re
import requests
import importlib
import logging
import platform
from typing import List, Dict, Any, Tuple, Optional
from templates import get_template

# Create .pylama directory if it doesn't exist
PACKAGE_DIR = os.path.join(os.path.expanduser('~'), '.pylama')
os.makedirs(PACKAGE_DIR, exist_ok=True)

# Configure logger for OllamaRunner
logger = logging.getLogger('pylama.ollama')
logger.setLevel(logging.INFO)

# Create file handler for Ollama-specific logs
ollama_log_file = os.path.join(PACKAGE_DIR, 'pylama_ollama.log')
file_handler = logging.FileHandler(ollama_log_file)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

logger.debug('OllamaRunner initialized')

# Użyj importlib.metadata zamiast pkg_resources
try:
    # Python 3.8+
    from importlib import metadata
except ImportError:
    # Dla starszych wersji Pythona
    import importlib_metadata as metadata

# Importuj sandbox, jeżeli używamy trybu Docker
USE_DOCKER = os.getenv('USE_DOCKER', 'False').lower() in ('true', '1', 't')
if USE_DOCKER:
    try:
        from sandbox import DockerSandbox
    except ImportError:
        logger.error("Nie można zaimportować modułu sandbox. Upewnij się, że plik sandbox.py jest dostępny.")
        sys.exit(1)


class OllamaRunner:
    """Klasa do uruchamiania Ollama i wykonywania wygenerowanego kodu."""

    def __init__(self, ollama_path: str = None, model: str = None):
        self.ollama_path = ollama_path or os.getenv('OLLAMA_PATH', 'ollama')
        self.model = model or os.getenv('OLLAMA_MODEL', 'llama3')
        self.fallback_models = os.getenv('OLLAMA_FALLBACK_MODELS', '').split(',')
        self.ollama_process = None

        # Aktualizacja do prawidłowych endpointów API Ollama
        self.generate_api_url = "http://localhost:11434/api/generate"
        self.chat_api_url = "http://localhost:11434/api/chat"
        self.version_api_url = "http://localhost:11434/api/version"

        # Konfiguracja Docker
        self.use_docker = USE_DOCKER
        self.docker_sandbox = None
        if self.use_docker:
            self.docker_sandbox = DockerSandbox()
            logger.info("Używanie trybu Docker dla Ollama.")

    def start_ollama(self) -> None:
        """Uruchom serwer Ollama jeśli nie jest już uruchomiony."""
        if self.use_docker:
            # Uruchom Ollama w kontenerze Docker
            if not self.docker_sandbox.start_container():
                raise RuntimeError("Nie udało się uruchomić kontenera Docker z Ollama.")
            return

        try:
            # Sprawdź czy Ollama już działa poprzez zapytanie o wersję
            response = requests.get(self.version_api_url)
            logger.info(f"Ollama is running (version: {response.json().get('version', 'unknown')})")
            return

        except requests.exceptions.ConnectionError:
            logger.info("Uruchamianie serwera Ollama...")
            # Uruchom Ollama w tle
            self.ollama_process = subprocess.Popen(
                [self.ollama_path, "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # Poczekaj na uruchomienie serwera
            time.sleep(5)

            # Sprawdź czy serwer faktycznie się uruchomił
            try:
                response = requests.get(self.version_api_url)
                logger.info(f"Serwer Ollama uruchomiony (version: {response.json().get('version', 'unknown')})")
            except requests.exceptions.ConnectionError:
                logger.error("BŁĄD: Nie udało się uruchomić serwera Ollama.")
                if self.ollama_process:
                    logger.error("Szczegóły błędu:")
                    out, err = self.ollama_process.communicate(timeout=1)
                    logger.error(f"STDOUT: {out.decode('utf-8', errors='ignore')}")
                    logger.error(f"STDERR: {err.decode('utf-8', errors='ignore')}")
                raise RuntimeError("Nie udało się uruchomić serwera Ollama")

    def stop_ollama(self) -> None:
        """Zatrzymaj serwer Ollama jeśli został uruchomiony przez ten skrypt."""
        if self.use_docker:
            if self.docker_sandbox:
                self.docker_sandbox.stop_container()
            return

        if self.ollama_process:
            logger.info("Zatrzymywanie serwera Ollama...")
            self.ollama_process.terminate()
            self.ollama_process.wait()
            logger.info("Serwer Ollama zatrzymany")

    def query_ollama(self, prompt: str, template_type: str = None, **template_args) -> str:
        """
        Wyślij zapytanie do API Ollama i zwróć odpowiedź.
        
        Args:
            prompt: Podstawowe zapytanie lub zadanie do wykonania
            template_type: Typ szablonu do użycia (opcjonalnie)
            **template_args: Dodatkowe argumenty dla szablonu
        
        Returns:
            Odpowiedź od modelu LLM
        """
        # Jeśli podano typ szablonu, użyj go do sformatowania zapytania
        if template_type:
            formatted_prompt = get_template(prompt, template_type, **template_args)
            logger.debug(f"Użyto szablonu {template_type} dla zapytania")
        else:
            formatted_prompt = prompt
            
        logger.info(f"Wysyłanie zapytania do modelu {self.model}...")

        # Najpierw sprawdźmy, czy model istnieje i jest dostępny
        try:
            tags_response = requests.get("http://localhost:11434/api/tags")
            models = tags_response.json().get("models", [])
            model_exists = any(m.get("name").split(":")[0] == self.model for m in models)

            if not model_exists:
                logger.warning(f"Model '{self.model}' is not installed. Available models:")
                for model in models:
                    logger.info(f" - {model.get('name')}")

                # Szukaj modelów alternatywnych z listy fallback
                found_fallback = False
                for fallback_model in self.fallback_models:
                    if fallback_model and any(m.get("name").split(":")[0] == fallback_model for m in models):
                        self.model = fallback_model
                        logger.info(f"Używam modelu '{self.model}' zamiast tego.")
                        found_fallback = True
                        break

                # Użyj pierwszego dostępnego, jeśli nie znaleziono w fallback
                if not found_fallback:
                    if models:
                        self.model = models[0].get('name').split(":")[0]
                        logger.info(f"Używam modelu '{self.model}' zamiast tego.")
                    else:
                        logger.error("Brak dostępnych modeli. Proszę zainstalować model za pomocą 'ollama pull <model>'.")
                        return ""
        except Exception as e:
            logger.error(f"Nie można sprawdzić dostępnych modeli: {e}")

        # Używamy API generate z wyłączonym streamingiem
        data = {
            "model": self.model,
            "prompt": formatted_prompt,
            "stream": False
        }

        try:
            # Próbujemy najpierw z /api/generate
            response = requests.post(self.generate_api_url, json=data)
            response.raise_for_status()  # Sprawdź, czy nie wystąpił błąd HTTP
            response_json = response.json()

            # Zapisz surową odpowiedź do pliku dla debugowania
            if os.getenv('SAVE_RAW_RESPONSES', 'False').lower() in ('true', '1', 't'):
                debug_file = os.path.join(PACKAGE_DIR, "ollama_raw_response.json")
                with open(debug_file, "w", encoding="utf-8") as f:
                    json.dump(response_json, f, indent=2)
                logger.debug(f'Zapisano surową odpowiedź do {debug_file}')

            return response_json.get("response", "")
        except Exception as e:
            logger.error(f"Błąd podczas komunikacji z API generate: {e}")

            try:
                # Spróbuj użyć /api/chat jako alternatywnego API
                logger.info("Próba użycia API chat...")
                chat_data = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": formatted_prompt}],
                    "stream": False
                }

                chat_response = requests.post(self.chat_api_url, json=chat_data)
                chat_response.raise_for_status()
                chat_json = chat_response.json()

                # Zapisz surową odpowiedź do pliku dla debugowania
                if os.getenv('SAVE_RAW_RESPONSES', 'False').lower() in ('true', '1', 't'):
                    debug_file = os.path.join(PACKAGE_DIR, "ollama_raw_chat_response.json")
                    with open(debug_file, "w", encoding="utf-8") as f:
                        json.dump(chat_json, f, indent=2)
                    logger.debug(f'Zapisano surową odpowiedź czatu do {debug_file}')

                # Ekstrakcja odpowiedzi z innego formatu
                if "message" in chat_json and "content" in chat_json["message"]:
                    return chat_json["message"]["content"]
                return ""
            except Exception as chat_e:
                logger.error(f"Błąd podczas komunikacji z API chat: {chat_e}")
                return ""

    def extract_python_code(self, text: str) -> str:
        """Wyodrębnij kod Python z odpowiedzi."""
        # Sprawdź różne możliwe formaty kodu w odpowiedzi
        patterns = [
            r"```python\s*(.*?)\s*```",  # Markdown code block
            r"```\s*(.*?)\s*```",  # Generic code block
            r"import .*?\n(.*?)(?:\n\n|$)"  # Kod zaczynający się od import
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                return matches[0]

        # Jeśli nie znaleziono kodu za pomocą wyrażeń regularnych,
        # spróbuj znaleźć po linii importu
        lines = text.split('\n')
        import_lines = []
        code_lines = []
        collecting = False

        for line in lines:
            if 'import' in line and not collecting:
                collecting = True

            if collecting:
                code_lines.append(line)

        if code_lines:
            return '\n'.join(code_lines)

        # Jeśli wszystko inne zawiedzie, wypisz odpowiedź do pliku debug
        debug_dir = os.path.join(PACKAGE_DIR, 'debug')
        os.makedirs(debug_dir, exist_ok=True)

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        debug_file = os.path.join(debug_dir, f"ollama_response_debug_{timestamp}.txt")

        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(text)

        logger.info(f"DEBUG: Zapisano pełną odpowiedź do pliku '{debug_file}'")
        return ""

    def save_code_to_file(self, code: str, filename: str = None) -> str:
        """Save the generated code to a file and return the path to the file."""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(PACKAGE_DIR, f"generated_script_{timestamp}.py")
        
        # Ensure the target directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)
        
        logger.info(f'Saved script to file: {filename}')
        return os.path.abspath(filename)

    def run_code_with_debug(self, code_file: str, original_prompt: str, original_code: str) -> bool:
        """Uruchamia kod i obsługuje ewentualne błędy."""
        try:
            # Run code in a new process
            print("\nRunning generated code...")
            process = subprocess.Popen(
                [sys.executable, code_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Poczekaj na zakończenie procesu z limitem czasu
            try:
                stdout, stderr = process.communicate(timeout=30)  # 30 sekund limitu
                stdout = stdout.decode('utf-8', errors='ignore')
                stderr = stderr.decode('utf-8', errors='ignore')

                # Check exit code
                if process.returncode != 0:
                    print(f"Code execution failed with error code: {process.returncode}.")
                    if stderr:
                        print(f"Error: {stderr}")

                    # Attempt debugging and code regeneration
                    debugged_code = self.debug_and_regenerate_code(original_prompt, stderr, original_code)

                    if debugged_code:
                        print("\nReceived fixed code:")
                        print("-" * 40)
                        print(debugged_code)
                        print("-" * 40)

                        # Save the fixed code to a file
                        fixed_code_file = self.save_code_to_file(debugged_code, os.path.join(PACKAGE_DIR, "fixed_script.py"))
                        print(f"Fixed code saved to file: {fixed_code_file}")

                        # Ask the user if they want to run the fixed code
                        user_input = input("\nDo you want to run the fixed code? (y/n): ").lower()
                        if user_input.startswith('y'):
                            # Recursive call, but without further debugging in case of subsequent errors
                            print("\nRunning fixed code...")
                            try:
                                subprocess.run([sys.executable, fixed_code_file], check=True)
                            except Exception as run_error:
                                print(f"Error running fixed code: {run_error}")

                    return False

                # If there were no errors
                if stdout:
                    print("Code execution result:")
                    print(stdout)

                print("Code executed successfully!")
                return True

            except subprocess.TimeoutExpired:
                process.kill()
                print("Code execution interrupted - time limit exceeded (30 seconds).")
                return False

        except Exception as e:
            print(f"Error running code: {e}")
            return False

    def debug_and_regenerate_code(self, original_prompt: str, error_message: str, code: str) -> str:
        """Debug errors in the generated code and request a fix."""
        print(f"\nDetected an error in the generated code. Attempting to fix...")

        # Use a template for code debugging
        # Send a debugging query using a special template
        debug_response = self.query_ollama(
            original_prompt,  # Original task
            template_type="debug",  # Use debugging template
            code=code,  # Pass the original code
            error_message=error_message  # Pass the error message
        )

        if not debug_response:
            print("No response received for the debugging query.")
            return ""

        # Extract the fixed code
        debugged_code = self.extract_python_code(debug_response)

        if not debugged_code:
            print("Failed to extract the fixed code.")
            # If code extraction failed, try to use the entire response
            if debug_response and "import" in debug_response:
                # If the response contains an import, it might be code without markers
                return debug_response
            return ""

        return debugged_code
