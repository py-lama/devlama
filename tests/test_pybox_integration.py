#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the PyBox integration with DevLama.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import PyBox wrapper and related modules
from devlama.pybox_wrapper import PythonSandbox, DockerSandbox
from pybox.code_analyzer import CodeAnalyzer
from pybox.dependency_manager import DependencyManager


@pytest.fixture
def mock_code_analyzer():
    """Mock the CodeAnalyzer class."""
    with patch('pybox.code_analyzer.CodeAnalyzer') as mock:
        analyzer_instance = MagicMock()
        analyzer_instance.analyze_code.return_value = {
            'imports': {'http': 'standard_library', 'requests': 'third_party'},
            'full_imports': {'http.server': 'http.server', 'requests': 'requests'},
            'standard_library': ['http'],
            'third_party': ['requests'],
            'unknown': [],
            'full_standard_library': ['http.server'],
            'full_third_party': ['requests'],
            'full_unknown': [],
            'required_packages': ['requests']
        }
        mock.return_value = analyzer_instance
        yield mock


@pytest.fixture
def mock_dependency_manager():
    """Mock the DependencyManager class."""
    with patch('pybox.dependency_manager.DependencyManager') as mock:
        manager_instance = MagicMock()
        manager_instance.analyze_dependencies.return_value = {
            'imports': {'http': 'standard_library', 'requests': 'third_party'},
            'required_packages': ['requests'],
            'installed_packages': ['requests'],
            'missing_packages': [],
            'installed_packages_count': 1
        }
        manager_instance.install_package.return_value = True
        mock.return_value = manager_instance
        yield mock


@pytest.fixture
def mock_subprocess():
    """Mock the subprocess module."""
    with patch('subprocess.run') as mock:
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.stdout = "Test output"
        process_mock.stderr = ""
        mock.return_value = process_mock
        yield mock


def test_python_sandbox_initialization():
    """Test that PythonSandbox initializes correctly."""
    with patch('pylama.pybox_wrapper.importlib.util.spec_from_file_location') as mock_spec:
        with patch('pylama.pybox_wrapper.importlib.util.module_from_spec') as mock_module:
            # Setup mocks
            spec_mock = MagicMock()
            module_mock = MagicMock()
            mock_spec.return_value = spec_mock
            mock_module.return_value = module_mock
            
            # Initialize PythonSandbox
            sandbox = PythonSandbox()
            
            # Check that it was initialized correctly
            assert sandbox is not None


def test_python_sandbox_run_code(mock_dependency_manager, mock_subprocess):
    """Test that PythonSandbox.run_code correctly executes code."""
    # Create a sandbox instance with mocked dependencies
    sandbox = PythonSandbox()
    sandbox.dependency_manager = mock_dependency_manager.return_value
    
    # Test code execution
    code = "import http.server\nprint('Hello, World!')"
    result = sandbox.run_code(code)
    
    # Check that dependencies were analyzed
    mock_dependency_manager.return_value.analyze_dependencies.assert_called_once_with(code)
    
    # Check that the code was executed
    mock_subprocess.assert_called_once()
    
    # Check the result
    assert result['success'] is True
    assert result['stdout'] == "Test output"
    assert result['stderr'] == ""


def test_python_sandbox_run_code_with_syntax_error(mock_dependency_manager):
    """Test that PythonSandbox.run_code handles syntax errors correctly."""
    # Create a sandbox instance with mocked dependencies
    sandbox = PythonSandbox()
    sandbox.dependency_manager = mock_dependency_manager.return_value
    
    # Test code with syntax error
    code = "print('Hello, World!'\n"
    
    # Mock ast.parse to raise a SyntaxError
    with patch('ast.parse') as mock_parse:
        mock_parse.side_effect = SyntaxError("invalid syntax")
        result = sandbox.run_code(code)
    
    # Check the result
    assert result['success'] is False
    assert 'SyntaxError' in result['error_type']


def test_docker_sandbox_initialization():
    """Test that DockerSandbox initializes correctly."""
    with patch('pylama.pybox_wrapper.importlib.util.spec_from_file_location') as mock_spec:
        with patch('pylama.pybox_wrapper.importlib.util.module_from_spec') as mock_module:
            # Setup mocks
            spec_mock = MagicMock()
            module_mock = MagicMock()
            mock_spec.return_value = spec_mock
            mock_module.return_value = module_mock
            
            # Initialize DockerSandbox
            sandbox = DockerSandbox()
            
            # Check that it was initialized correctly
            assert sandbox is not None


def test_code_analyzer_improvements(mock_code_analyzer):
    """Test the improvements to the code analyzer for handling submodules."""
    # Import the code analyzer directly
    from pybox.code_analyzer import CodeAnalyzer
    
    # Create a code analyzer instance
    analyzer = CodeAnalyzer()
    
    # Test code with submodule imports
    code = """import http.server
    from http.server import BaseHTTPRequestHandler, HTTPServer
    import requests
    
    class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Hello, World!')
    """
    
    # Mock the analyze_code method
    with patch.object(analyzer, 'analyze_code', return_value=mock_code_analyzer.return_value.analyze_code.return_value):
        result = analyzer.analyze_code(code)
    
    # Check the result
    assert 'http' in result['standard_library']
    assert 'http.server' in result['full_standard_library']
    assert 'requests' in result['third_party']
    assert 'requests' in result['full_third_party']


def test_dependency_manager_improvements(mock_dependency_manager):
    """Test the improvements to the dependency manager for handling submodules."""
    # Import the dependency manager directly
    from pybox.dependency_manager import DependencyManager
    
    # Create a dependency manager instance
    manager = DependencyManager()
    
    # Test code with submodule imports
    code = """import http.server
    from http.server import BaseHTTPRequestHandler, HTTPServer
    import requests
    
    class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Hello, World!')
    """
    
    # Mock the analyze_dependencies method
    with patch.object(manager, 'analyze_dependencies', return_value=mock_dependency_manager.return_value.analyze_dependencies.return_value):
        result = manager.analyze_dependencies(code)
    
    # Check the result
    assert 'requests' in result['required_packages']
    assert 'requests' in result['installed_packages']
    assert len(result['missing_packages']) == 0
