![obraz](pylama-logo.png)

# PyLama - Python Code Generation with Ollama

PyLama is a Python tool that leverages Ollama's language models to generate and execute Python code. It simplifies the process of writing and running Python scripts by handling dependency management and code execution automatically. With the new template system, it generates higher quality, platform-aware code that's ready to run.

## Features

- **AI-Powered Code Generation** - Generate Python code using Ollama's language models
- **Template System** - Use specialized templates for different coding needs (security, performance, testing)
- **Platform-Aware Code** - Generate code optimized for your specific operating system
- **Automatic Dependency Management** - Automatically detects and installs required Python packages
- **Code Execution** - Run generated code in a controlled environment
- **Error Handling** - Automatic error detection and debugging suggestions with specialized templates
- **Modular Architecture** - Separated components for better maintainability

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.com/) installed and running locally
- At least one Ollama model (e.g., llama3, llama2, mistral)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/py-lama/pylama.git
   cd pylama
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure Ollama is running:
   ```bash
   ollama serve
   ```

## Usage

### Basic Usage

```bash
python pylama.py
```

### Command Line Options

- `prompt`: The task description for code generation (can be provided as positional arguments)
- `-t, --template`: Choose a template type for code generation (default: platform_aware)
  - Available templates: basic, platform_aware, dependency_aware, testable, secure, performance, pep8
- `-d, --dependencies`: Specify allowed dependencies (for dependency_aware template)
- `-m, --model`: Specify which Ollama model to use (default: llama3)

### Examples

```bash
# Basic usage with a prompt
python pylama.py "create a function to calculate factorial"

# Use a specific template
python pylama.py -t secure "create a web server"

# Specify allowed dependencies
python pylama.py -t dependency_aware -d "numpy,pandas,matplotlib" "create a data visualization"

# Use a specific model
python pylama.py -m phi3 "create a simple game"
```

## Model Management (models.py)

- **Automatic Environment & Dependency Setup:**
  - Running `models.py` will auto-create a `.venv` and install required dependencies (`requests`, `bs4`, `python-dotenv`) if missing.
  - No manual pip/venv setup required—just run the script.
- **Model List Updating:**
  - Models are fetched directly from the [Ollama library](https://ollama.com/library) (HTML scraping), not from a static JSON.
  - Only coding-related models up to 7B parameters are shown.
  - Use the interactive CLI to update the list (`u`), install by number, or quit (`q`).
- **Immediate Feedback:**
  - Installed models are listed at startup for quick reference.

## Python Sandbox (sandbox package)

- **Modular Architecture:**
  - Refactored into specialized components for better maintainability and organization:
    - `code_analyzer.py`: Analyzes Python code and detects dependencies
    - `dependency_manager.py`: Manages package dependencies and installations
    - `python_sandbox.py`: Executes Python code safely in a local environment
    - `docker_sandbox.py`: Executes Python code in a Docker container
    - `sandbox_manager.py`: Manages different sandbox types
    - `utils.py`: Provides utility functions for the sandbox package
- **Automatic Dependency Management:**
  - The sandbox analyzes Python code, detects imports, and installs missing packages automatically (locally or in Docker).
- **Safe & Flexible Execution:**
  - Run code locally or in a Docker container for isolation (choose with `use_docker=True/False`).
  - Handles syntax errors and runtime exceptions with clear error messages.
  - Execution timeout can be set to avoid hanging code.
- **Backward Compatibility:**
  - Original `sandbox.py` serves as a compatibility layer for existing code.
- **Usage Example:**
  ```python
  # Using the new modular structure
  from sandbox.python_sandbox import PythonSandbox
  sandbox = PythonSandbox(use_docker=False)
  result = sandbox.run_code('import numpy as np\nprint(np.arange(5))')
  print(result['stdout'])
  
  # Using the compatibility layer (for existing code)
  from sandbox import run_code
  result = run_code('import numpy as np\nprint(np.arange(5))')
  print(result['stdout'])
  ```

## Project Structure

- `pylama.py`: Main script with command-line interface
- `OllamaRunner.py`: Handles communication with Ollama API
- `templates.py`: Contains specialized templates for different code generation needs
- `DependencyManager.py`: Manages Python package dependencies
- `sandbox.py`: Compatibility layer for the sandbox package
- `sandbox/`: Modular package for code execution and dependency management
  - `code_analyzer.py`: Analyzes Python code and detects dependencies
  - `dependency_manager.py`: Manages package dependencies and installations
  - `python_sandbox.py`: Executes Python code safely in a local environment
  - `docker_sandbox.py`: Executes Python code in a Docker container
  - `sandbox_manager.py`: Manages different sandbox types
  - `utils.py`: Provides utility functions for the sandbox package
  - `examples.py`: Contains example usage of the sandbox components
- `models.sh`: Script to manage Ollama models

## How It Works

1. The tool analyzes your prompt and selects the appropriate template based on your requirements
2. It enhances your prompt with template-specific instructions for the Ollama model
3. The template-enhanced prompt is sent to the specified Ollama model to generate Python code
4. It extracts import statements to identify required dependencies
5. It checks for and installs any missing dependencies
6. The generated code is executed in a controlled environment
7. Any errors are caught and a specialized debug template is used to regenerate improved code

## Configuration

Create a `.env` file in the project root to customize behavior:

```env
OLLAMA_MODEL=llama3
OLLAMA_FALLBACK_MODELS=phi3,llama2
LOG_LEVEL=INFO
USE_DOCKER=False
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Template System

PyLama includes a powerful template system that helps generate better quality code for different scenarios:

### Available Templates

- **basic** - Simple code generation with standard best practices
- **platform_aware** - Generates code optimized for your specific operating system
- **dependency_aware** - Creates code using only specified dependencies
- **testable** - Includes unit tests with the generated code
- **secure** - Focuses on security best practices and input validation
- **performance** - Optimizes code for better performance
- **pep8** - Ensures code follows Python PEP 8 style guidelines

### Debug Template

When errors occur in generated code, PyLama uses a specialized debug template to analyze and fix the issues automatically.

## Wymagania

- Python 3.8+ (skrypt wykryje i zainstaluje zależności)
- [Ollama](https://ollama.com/download)
- Co najmniej jeden model Ollama (np. tinyllama, llama3, qwen, phi)

## Szybki start

1. **Pobierz i utwórz skrypt:**

   ```bash
   # Zapisz skrypt jako setup.sh
   chmod +x setup.sh
   ```

2. **Uruchom z pełną konfiguracją:**

   ```bash
   ./setup.sh
   ```

   Skrypt automatycznie:
   - Sprawdzi i zainstaluje wymagane pakiety Python
   - Sprawdzi instalację Ollama
   - Pomoże w konfiguracji modeli
   - Uruchomi serwer API

3. **Lub tylko uruchom serwer (jeśli już skonfigurowany):**

   ```bash
   ./setup.sh --run
   ```

## Dostępne opcje

Skrypt oferuje kilka przydatnych opcji:

```bash
# Wyświetlenie pomocy
./setup.sh --help

# Tylko konfiguracja środowiska (bez uruchamiania)
./setup.sh --setup

# Tylko uruchomienie serwera
./setup.sh --run

# Uruchomienie na niestandardowym porcie
./setup.sh --run --port 8080

# Zarządzanie modelami Ollama
./setup.sh --models

# Sprawdzenie wymagań systemowych
./setup.sh --check
```

## Interfejs webowy

Po uruchomieniu serwera, interfejs webowy jest dostępny pod adresem:

```
http://localhost:5001
```

Interfejs pozwala na:
- Zadawanie pytań do modelu
- Zmianę parametrów generowania
- Przeglądanie dostępnych modeli

## API REST

Serwer udostępnia następujące endpointy:

### `POST /ask`

Wysyła zapytanie do modelu Ollama.

**Żądanie**:
```json
{
  "prompt": "Co to jest Python?",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Odpowiedź**:
```json
{
  "response": "Python to wysokopoziomowy, interpretowany język programowania..."
}
```

### `GET /models`

Pobiera listę dostępnych modeli Ollama.

**Odpowiedź**:
```json
{
  "models": [
    {
      "name": "tinyllama:latest",
      "size": 1640,
      "current": true
    },
    {
      "name": "llama3:latest",
      "size": 3827,
      "current": false
    }
  ]
}
```

### `POST /echo`

Proste narzędzie do testowania działania serwera.
![img.png](img.png)
**Żądanie**:
```json
{
  "message": "Test"
}
```

**Odpowiedź**:
```json
{
  "response": "Otrzymano: Test"
}
```

## Używanie z cURL

```bash
# Zapytanie do modelu
curl -X POST -H "Content-Type: application/json" \
     -d '{"prompt":"Co to jest Python?"}' \
     http://localhost:5001/ask

# Pobranie listy modeli
curl http://localhost:5001/models

# Test echo
curl -X POST -H "Content-Type: application/json" \
     -d '{"message":"Test"}' \
     http://localhost:5001/echo
```

## Plik konfiguracyjny .env

Skrypt tworzy plik `.env` z ustawieniami, które możesz edytować:

```
# Konfiguracja modelu Ollama
MODEL_NAME="tinyllama:latest"

# Konfiguracja serwera
OLLAMA_URL="http://localhost:11434"
SERVER_PORT=5001

# Parametry generowania
TEMPERATURE=0.7
MAX_TOKENS=1000
```

## Obsługiwane modele

Skrypt działa z wszystkimi modelami dostępnymi w Ollama. Oto szczegółowa lista najpopularniejszych modeli:

| Model | Rozmiar | Przeznaczenie |
|-------|---------|---------------|
| **llama3** | 8B | Ogólnego przeznaczenia, dobry do większości zadań |
| **phi3** | 3.8B | Szybki, dobry do prostszych zadań, zoptymalizowany pod kątem kodu |
| **mistral** | 7B | Ogólnego przeznaczenia, efektywny energetycznie |
| **gemma** | 7B | Dobry do zadań języka naturalnego i kreatywnego pisania |
| **tinyllama** | 1.1B | Bardzo szybki, idealny dla słabszych urządzeń |
| **qwen** | 7-14B | Dobry w analizie tekstu, wsparcie dla języków azjatyckich |
| **llava** | 7-13B | Multimodalny z obsługą obrazów - pozwala na analizę obrazów i tekstu |
| **codellama** | 7-34B | Wyspecjalizowany model do kodowania - świetny do generowania i analizy kodu |
| **vicuna** | 7-13B | Wytrenowany na konwersacjach, dobry do dialogów |
| **falcon** | 7-40B | Szybki i efektywny, dobry stosunek wydajności do rozmiaru |
| **orca-mini** | 3B | Dobry do podstawowych zadań NLP |
| **wizardcoder** | 13B | Stworzony do zadań związanych z kodem |
| **llama2** | 7-70B | Poprzednia generacja modelu Meta, sprawdzony w różnych zastosowaniach |
| **stablelm** | 3-7B | Dobry do generowania tekstu i dialogów |
| **dolphin** | 7B | Koncentruje się na naturalności dialogów |
| **neural-chat** | 7-13B | Zoptymalizowany pod kątem urządzeń Intel |
| **starling** | 7B | Mniejszy ale skuteczny, zoptymalizowany pod kątem jakości odpowiedzi |
| **openhermes** | 7B | Dobra dokładność, postępowanie zgodnie z instrukcjami |
| **yi** | 6-34B | Zaawansowany model wielojęzyczny |

### Wybór rozmiaru modelu

Przy wyborze własnego modelu, warto rozważyć różne rozmiary:

- **Mini (1-3B)**: Bardzo małe modele - szybkie, ale ograniczone możliwości
- **Small (3-7B)**: Małe modele - dobry kompromis szybkość/jakość
- **Medium (8-13B)**: Średnie modele - lepsze odpowiedzi, wymaga więcej RAM
- **Large (30-70B)**: Duże modele - najlepsza jakość, wysokie wymagania sprzętowe

### Wymagania sprzętowe

Poniżej orientacyjne wymagania sprzętowe dla różnych rozmiarów modeli:

| Rozmiar modelu | Minimalna ilość RAM | Zalecana ilość RAM | GPU |
|----------------|---------------------|-------------------|-----|
| Mini (1-3B) | 4GB | 8GB | Opcjonalnie |
| Small (3-7B) | 8GB | 16GB | Zalecany |
| Medium (8-13B) | 16GB | 24GB | Zalecany ≥4GB VRAM |
| Large (30-70B) | 32GB | 64GB | Wymagany ≥8GB VRAM |

## FAQ

- **Q: Do I need to install anything before running `models.py`?**
  - A: No, the script will auto-create a venv and install dependencies if needed.
- **Q: How do I update the model list?**
  - A: Run `models.py` and press `u` in the menu.
- **Q: How do I run code with sandbox.py?**
  - A: See the usage example above. Dependencies are managed automatically.
