#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Przyku0142ady uu017cycia pakietu sandbox.

Ten moduu0142 zawiera przyku0142ady uu017cycia ru00f3u017cnych komponentu00f3w pakietu sandbox.
"""

import os
import sys
import logging

# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Przyku0142adowe kody Python do testu00f3w
EXAMPLE_CODE_SIMPLE = """
import os
import sys
import math

print('Informacje o systemie:')
print(f'System operacyjny: {os.name}')
print(f'Wersja Pythona: {sys.version}')
print(f'Katalog bieu017cu0105cy: {os.getcwd()}')

# Przyku0142ad obliczeu0144 matematycznych
print('\nObliczenia matematyczne:')
print(f'Pi: {math.pi}')
print(f'Pierwiastek z 16: {math.sqrt(16)}')
print(f'Silnia z 5: {math.factorial(5)}')
"""

EXAMPLE_CODE_NUMPY = """
import numpy as np
import matplotlib.pyplot as plt

# Przyku0142ad uu017cycia NumPy
arr = np.array([1, 2, 3, 4, 5])
print(f'Tablica NumPy: {arr}')
print(f'u015arednia: {np.mean(arr)}')
print(f'Suma: {np.sum(arr)}')
print(f'Odchylenie standardowe: {np.std(arr)}')

# Przyku0142ad generowania wykresu
x = np.linspace(0, 10, 100)
y = np.sin(x)
plt.figure(figsize=(8, 4))
plt.plot(x, y)
plt.title('Funkcja sinus')
plt.xlabel('x')
plt.ylabel('sin(x)')
plt.grid(True)
plt.savefig('sinus.png')
print('Wykres zapisany do pliku sinus.png')
"""

EXAMPLE_CODE_ERROR = """
print('Ten kod zawiera bu0142u0105d sku0142adni')
if True
    print('Brakuje dwukropka po if')
"""

EXAMPLE_CODE_RUNTIME_ERROR = """
print('Ten kod zawiera bu0142u0105d wykonania')
x = 10 / 0  # Dzielenie przez zero
print('Ta linia nie zostanie wykonana')
"""

EXAMPLE_CODE_FILE_OPERATIONS = """
import os
import tempfile

# Utworzenie tymczasowego pliku
temp_file = tempfile.NamedTemporaryFile(delete=False)
temp_path = temp_file.name
temp_file.close()

# Zapisanie danych do pliku
with open(temp_path, 'w') as f:
    f.write('Hello, world!\n')
    f.write('To jest przyku0142ad operacji na plikach.')

# Odczytanie danych z pliku
print(f'Odczytywanie pliku: {temp_path}')
with open(temp_path, 'r') as f:
    content = f.read()
    print(content)

# Usuniu0119cie pliku
os.unlink(temp_path)
print(f'Plik {temp_path} zostau0142 usuniu0119ty.')
"""


def example_code_analyzer():
    """Przyku0142ad uu017cycia CodeAnalyzer."""
    from sandbox.code_analyzer import CodeAnalyzer
    
    analyzer = CodeAnalyzer()
    
    print("\n=== Przyku0142ad uu017cycia CodeAnalyzer ===\n")
    
    # Analiza kodu z importami standardowymi
    print("Analiza kodu z importami standardowymi:")
    result = analyzer.analyze_code(EXAMPLE_CODE_SIMPLE)
    print(f"Standardowe biblioteki: {result['standard_library']}")
    print(f"Zewnu0119trzne biblioteki: {result['third_party']}")
    print(f"Nieznane biblioteki: {result['unknown']}")
    print(f"Wymagane pakiety: {result['required_packages']}")
    
    # Analiza kodu z importami zewnu0119trznymi
    print("\nAnaliza kodu z importami zewnu0119trznymi:")
    result = analyzer.analyze_code(EXAMPLE_CODE_NUMPY)
    print(f"Standardowe biblioteki: {result['standard_library']}")
    print(f"Zewnu0119trzne biblioteki: {result['third_party']}")
    print(f"Nieznane biblioteki: {result['unknown']}")
    print(f"Wymagane pakiety: {result['required_packages']}")
    
    # Analiza kodu z bu0142u0119dem sku0142adni
    print("\nAnaliza kodu z bu0142u0119dem sku0142adni:")
    result = analyzer.analyze_code(EXAMPLE_CODE_ERROR)
    print(f"Wynik: {result}")


def example_dependency_manager():
    """Przyku0142ad uu017cycia DependencyManager."""
    from sandbox.dependency_manager import DependencyManager
    
    dependency_manager = DependencyManager()
    
    print("\n=== Przyku0142ad uu017cycia DependencyManager ===\n")
    
    # Sprawdzenie zainstalowanych pakietu00f3w
    print("Sprawdzenie zainstalowanych pakietu00f3w:")
    packages = ['os', 'sys', 'math', 'numpy', 'pandas', 'nonexistent_package']
    for package in packages:
        installed = dependency_manager.check_package_installed(package)
        print(f"Pakiet {package}: {'zainstalowany' if installed else 'niezainstalowany'}")
    
    # Analiza zaleu017cnou015bci
    print("\nAnaliza zaleu017cnou015bci:")
    result = dependency_manager.analyze_dependencies(EXAMPLE_CODE_NUMPY)
    print(f"Wymagane pakiety: {result['required_packages']}")
    print(f"Zainstalowane pakiety: {result['installed_packages']}")
    print(f"Brakuju0105ce pakiety: {result['missing_packages']}")


def example_python_sandbox():
    """Przyku0142ad uu017cycia PythonSandbox."""
    from sandbox.python_sandbox import PythonSandbox
    
    sandbox = PythonSandbox()
    
    print("\n=== Przyku0142ad uu017cycia PythonSandbox ===\n")
    
    # Uruchomienie prostego kodu
    print("Uruchomienie prostego kodu:")
    result = sandbox.run_code(EXAMPLE_CODE_SIMPLE)
    print(f"Sukces: {result['success']}")
    print(f"Standardowe wyju015bcie:\n{result['stdout']}")
    
    # Uruchomienie kodu z bu0142u0119dem sku0142adni
    print("\nUruchomienie kodu z bu0142u0119dem sku0142adni:")
    result = sandbox.run_code(EXAMPLE_CODE_ERROR)
    print(f"Sukces: {result['success']}")
    print(f"Standardowe wyju015bcie bu0142u0119du00f3w:\n{result['stderr']}")
    
    # Uruchomienie kodu z bu0142u0119dem wykonania
    print("\nUruchomienie kodu z bu0142u0119dem wykonania:")
    result = sandbox.run_code(EXAMPLE_CODE_RUNTIME_ERROR)
    print(f"Sukces: {result['success']}")
    print(f"Standardowe wyju015bcie:\n{result['stdout']}")
    print(f"Standardowe wyju015bcie bu0142u0119du00f3w:\n{result['stderr']}")


def example_docker_sandbox():
    """Przyku0142ad uu017cycia DockerSandbox."""
    from sandbox.docker_sandbox import DockerSandbox
    
    # Sprawdu017a, czy Docker jest zainstalowany
    import subprocess
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        docker_installed = result.returncode == 0
    except Exception:
        docker_installed = False
    
    if not docker_installed:
        print("\n=== Przyku0142ad uu017cycia DockerSandbox ===\n")
        print("Docker nie jest zainstalowany. Pomijanie przyku0142adu.")
        return
    
    sandbox = DockerSandbox()
    
    print("\n=== Przyku0142ad uu017cycia DockerSandbox ===\n")
    
    # Uruchomienie prostego kodu w Dockerze
    print("Uruchomienie prostego kodu w Dockerze:")
    result = sandbox.run_code(EXAMPLE_CODE_SIMPLE)
    print(f"Sukces: {result['success']}")
    print(f"Standardowe wyju015bcie:\n{result['stdout']}")


def example_sandbox_manager():
    """Przyku0142ad uu017cycia SandboxManager."""
    from sandbox.sandbox_manager import SandboxManager
    
    # Utworzenie SandboxManager
    manager = SandboxManager(use_docker=False)
    
    print("\n=== Przyku0142ad uu017cycia SandboxManager ===\n")
    
    # Uruchomienie kodu lokalnie
    print("Uruchomienie kodu lokalnie:")
    result = manager.run_code(EXAMPLE_CODE_SIMPLE)
    print(manager.format_result(result))
    
    # Sprawdu017a, czy Docker jest zainstalowany
    import subprocess
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        docker_installed = result.returncode == 0
    except Exception:
        docker_installed = False
    
    if docker_installed:
        # Utworzenie SandboxManager z Dockerem
        docker_manager = SandboxManager(use_docker=True)
        
        # Uruchomienie kodu w Dockerze
        print("\nUruchomienie kodu w Dockerze:")
        result = docker_manager.run_code(EXAMPLE_CODE_SIMPLE)
        print(docker_manager.format_result(result))


def example_utils():
    """Przyku0142ad uu017cycia funkcji pomocniczych."""
    from sandbox.utils import get_system_info, format_execution_result, create_temp_file
    
    print("\n=== Przyku0142ad uu017cycia funkcji pomocniczych ===\n")
    
    # Informacje o systemie
    print("Informacje o systemie:")
    system_info = get_system_info()
    for key, value in system_info.items():
        print(f"{key}: {value}")
    
    # Utworzenie tymczasowego pliku
    print("\nUtworzenie tymczasowego pliku:")
    file_path, file_name = create_temp_file("print('Hello, world!')")
    print(f"Utworzono plik: {file_path}")
    
    # Formatowanie wyniku wykonania kodu
    print("\nFormatowanie wyniku wykonania kodu:")
    result = {
        'success': True,
        'stdout': 'Hello, world!',
        'stderr': '',
        'required_packages': ['numpy', 'pandas'],
        'installed_packages': ['numpy'],
        'missing_packages': ['pandas']
    }
    formatted = format_execution_result(result)
    print(formatted)
    
    # Usuniu0119cie tymczasowego pliku
    try:
        os.unlink(file_path)
        print(f"Usuniu0119to plik: {file_path}")
    except Exception as e:
        print(f"Bu0142u0105d podczas usuwania pliku: {e}")


def main():
    """Gu0142u00f3wna funkcja uruchamiaju0105ca przyku0142ady."""
    print("=== Przyku0142ady uu017cycia pakietu sandbox ===")
    
    # Uruchomienie przyku0142adu00f3w
    example_code_analyzer()
    example_dependency_manager()
    example_python_sandbox()
    example_docker_sandbox()
    example_sandbox_manager()
    example_utils()


if __name__ == "__main__":
    main()
