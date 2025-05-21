#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import sys
import os

# Dodanie ścieżki nadrzędnej do sys.path, aby można było importować moduły z pakietu pylama
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_all_tests():
    """Uruchamia wszystkie testy w katalogu tests."""
    # Odkrycie i załadowanie wszystkich testów
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(os.path.dirname(__file__), pattern='test_*.py')
    
    # Uruchomienie testów z wyświetlaniem wyników
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Zwrócenie kodu wyjścia na podstawie wyników testów
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
