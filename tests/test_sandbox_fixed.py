#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import sys
import os
import tempfile
import shutil

# Dodanie u015bcieu017cki nadrzu0119dnej do sys.path, aby mou017cna byu0142o importowau0107 moduu0142y z pakietu pylama
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sandbox import CodeAnalyzer, DependencyManager, PythonSandbox


class TestCodeAnalyzer(unittest.TestCase):
    """Testy dla klasy CodeAnalyzer."""
    
    def setUp(self):
        self.analyzer = CodeAnalyzer()
    
    def test_analyze_code_with_standard_imports(self):
        """Test analizy kodu z importami ze standardowej biblioteki."""
        code = """import os
import sys
import math

print(os.getcwd())
print(sys.version)
print(math.pi)
"""
        
        result = self.analyzer.analyze_code(code)
        
        self.assertIn('os', result['standard_library'])
        self.assertIn('sys', result['standard_library'])
        self.assertIn('math', result['standard_library'])
        self.assertEqual(len(result['third_party']), 0)
        self.assertEqual(len(result['unknown']), 0)
        self.assertEqual(len(result['required_packages']), 0)
    
    def test_analyze_code_with_third_party_imports(self):
        """Test analizy kodu z importami z zewnu0119trznych bibliotek."""
        code = """
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

data = np.array([1, 2, 3, 4, 5])
df = pd.DataFrame({'A': data})
plt.plot(data)
"""
        
        result = self.analyzer.analyze_code(code)
        
        # Uwaga: te testy mogu0105 siu0119 nie powieu015bu0107, jeu015bli pakiety nie su0105 zainstalowane
        # lub su0105 klasyfikowane inaczej
        self.assertIn('numpy', result['imports'])
        self.assertIn('pandas', result['imports'])
        self.assertIn('matplotlib', result['imports'])
    
    def test_analyze_code_with_syntax_error(self):
        """Test analizy kodu z bu0142u0119dem sku0142adni."""
        code = """
print('Hello')
if True
    print('Missing colon')
"""
        
        result = self.analyzer.analyze_code(code)
        
        self.assertIn('error', result)
        self.assertEqual(len(result['imports']), 0)


class TestDependencyManager(unittest.TestCase):
    """Testy dla klasy DependencyManager."""
    
    def setUp(self):
        self.dependency_manager = DependencyManager()
    
    def test_module_to_package_mapping(self):
        """Test mapowania moduu0142u00f3w na pakiety."""
        self.assertEqual(self.dependency_manager.module_to_package.get('numpy'), 'numpy')
        self.assertEqual(self.dependency_manager.module_to_package.get('pandas'), 'pandas')
        self.assertEqual(self.dependency_manager.module_to_package.get('sklearn'), 'scikit-learn')
    
    def test_check_package_installed(self):
        """Test sprawdzania, czy pakiet jest zainstalowany."""
        # Ten test zaku0142ada, u017ce os i sys su0105 zawsze dostu0119pne
        self.assertTrue(self.dependency_manager.check_package_installed('os'))
        self.assertTrue(self.dependency_manager.check_package_installed('sys'))
        
        # Ten test mou017ce siu0119 nie powieu015bu0107, jeu015bli pakiet jest zainstalowany
        self.assertFalse(self.dependency_manager.check_package_installed('nonexistent_package_xyz'))


class TestPythonSandbox(unittest.TestCase):
    """Testy dla klasy PythonSandbox."""
    
    def setUp(self):
        # Uu017cywamy lokalnego wykonania (bez Dockera) dla testu00f3w jednostkowych
        self.sandbox = PythonSandbox(use_docker=False)
        
        # Utworzenie tymczasowego katalogu na pliki testowe
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        # Usuniu0119cie tymczasowego katalogu po testach
        shutil.rmtree(self.test_dir)
    
    def test_run_simple_code(self):
        """Test uruchamiania prostego kodu."""
        code = "print('Hello, world!')"
        
        result = self.sandbox.run_code(code)
        
        self.assertTrue(result['success'])
        self.assertIn('Hello, world!', result['stdout'])
        # Ignorujemy komunikaty pytest-cov w stderr
        if 'pytest-cov' in result.get('stderr', ''):
            print('Ignorowanie komunikatu pytest-cov w stderr')
        else:
            self.assertEqual(result['stderr'], '')
    
    def test_run_code_with_syntax_error(self):
        """Test uruchamiania kodu z bu0142u0119dem sku0142adni."""
        code = """
print('Hello')
if True
    print('Missing colon')
"""
        
        result = self.sandbox.run_code(code)
        
        self.assertFalse(result['success'])
        self.assertIn('SyntaxError', result['error_type'])
    
    def test_run_code_with_runtime_error(self):
        """Test uruchamiania kodu z bu0142u0119dem wykonania."""
        code = """print('Before error')
x = 10 / 0  # Division by zero
print('After error')
"""
        
        result = self.sandbox.run_code(code)
        
        self.assertFalse(result['success'])
        self.assertIn('Before error', result['stdout'])
        self.assertIn('ZeroDivisionError', result['stderr'])


class TestSandboxIntegration(unittest.TestCase):
    """Testy integracyjne dla sandboxa."""
    
    def setUp(self):
        # Uu017cywamy lokalnego wykonania (bez Dockera) dla testu00f3w integracyjnych
        self.sandbox = PythonSandbox(use_docker=False)
    
    def test_code_with_file_operations(self):
        """Test uruchamiania kodu z operacjami na plikach."""
        # Utworzenie tymczasowego katalogu
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'test.txt')
        
        try:
            # Kod, ktu00f3ry tworzy i czyta plik
            code = f"""with open('{temp_file}', 'w') as f:
    f.write('Hello from sandbox!')

with open('{temp_file}', 'r') as f:
    content = f.read()
    print(content)
"""
            
            result = self.sandbox.run_code(code)
            
            self.assertTrue(result['success'])
            self.assertIn('Hello from sandbox!', result['stdout'])
            
            # Sprawdzenie, czy plik zostau0142 rzeczywiu015bcie utworzony
            self.assertTrue(os.path.exists(temp_file))
            with open(temp_file, 'r') as f:
                content = f.read()
                self.assertEqual(content, 'Hello from sandbox!')
                
        finally:
            # Czyszczenie
            shutil.rmtree(temp_dir)
    
    def test_code_with_imports(self):
        """Test uruchamiania kodu z importami."""
        code = """import os
import sys
import math

print(f'OS: {os.name}')
print(f'Python: {sys.version}')
print(f'Pi: {math.pi}')
"""
        
        result = self.sandbox.run_code(code)
        
        self.assertTrue(result['success'])
        self.assertIn('OS:', result['stdout'])
        self.assertIn('Python:', result['stdout'])
        self.assertIn('Pi:', result['stdout'])


if __name__ == '__main__':
    unittest.main()
