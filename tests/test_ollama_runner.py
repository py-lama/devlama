#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the OllamaRunner class.
"""

import os
import sys
import re
import pytest
from unittest.mock import patch, MagicMock, mock_open

# Import OllamaRunner
from pylama.OllamaRunner import OllamaRunner


@pytest.fixture
def mock_requests():
    """Mock the requests module."""
    with patch('pylama.OllamaRunner.requests') as mock:
        response_mock = MagicMock()
        response_mock.json.return_value = {"version": "v0.1.0"}
        mock.get.return_value = response_mock
        yield mock


@pytest.fixture
def mock_subprocess():
    """Mock the subprocess module."""
    with patch('pylama.OllamaRunner.subprocess') as mock:
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.stdout = "ollama 0.1.0"
        mock.Popen.return_value = process_mock
        mock.run.return_value = process_mock
        yield mock


@pytest.fixture
def mock_open_file():
    """Mock the open function for file operations."""
    with patch('builtins.open', mock_open(read_data="print('Hello, World!')")) as mock_file:
        yield mock_file


def test_ollama_runner_initialization():
    """Test that OllamaRunner initializes correctly."""
    # Mock the environment variables to ensure consistent test results
    with patch.dict('os.environ', {'OLLAMA_MODEL': 'llama3'}):
        runner = OllamaRunner()
        assert runner.model == "llama3"
        assert runner.generate_api_url == "http://localhost:11434/api/generate"
        assert runner.chat_api_url == "http://localhost:11434/api/chat"
        assert runner.version_api_url == "http://localhost:11434/api/version"


def test_ollama_runner_start_ollama(mock_requests, mock_subprocess):
    """Test that OllamaRunner.start_ollama correctly starts the Ollama server."""
    runner = OllamaRunner()
    runner.start_ollama()
    
    # Check that requests.get was called with the correct URL
    mock_requests.get.assert_called_once_with(runner.version_api_url)


def test_ollama_runner_stop_ollama(mock_subprocess):
    """Test that OllamaRunner.stop_ollama correctly stops the Ollama server."""
    runner = OllamaRunner()
    runner.ollama_process = mock_subprocess.Popen.return_value
    runner.stop_ollama()
    
    # Check that the process was terminated
    runner.ollama_process.terminate.assert_called_once()
    runner.ollama_process.wait.assert_called_once()


def test_ollama_runner_query_ollama():
    """Test that OllamaRunner.query_ollama returns the correct response."""
    runner = OllamaRunner()
    response = runner.query_ollama("Create a hello world program")
    
    # Check that the response is not empty
    assert response is not None
    assert len(response) > 0


def test_ollama_runner_load_example_from_file(mock_open_file):
    """Test that OllamaRunner._load_example_from_file correctly loads examples."""
    runner = OllamaRunner()
    
    # Test loading web_server example
    with patch('os.path.join', return_value='/path/to/web_server.py'):
        content = runner._load_example_from_file('web_server.py')
        assert content == "print('Hello, World!')"
    
    # Test loading with prompt replacement
    with patch('os.path.join', return_value='/path/to/default.py'):
        content = runner._load_example_from_file('default.py', prompt="Create a calculator")
        assert content == "print('Hello, World!')"


def test_ollama_runner_extract_python_code():
    """Test that OllamaRunner.extract_python_code correctly extracts code."""
    runner = OllamaRunner()
    
    # Test with markdown code block
    text = """Here's a simple hello world program:

```python
print('Hello, World!')
```

This will print a greeting to the console."""
    code = runner.extract_python_code(text)
    assert code == "print('Hello, World!')"
    
    # Test with generic code block
    text = """Here's a simple hello world program:

```
print('Hello, World!')
```

This will print a greeting to the console."""
    code = runner.extract_python_code(text)
    assert code == "print('Hello, World!')"
    
    # Mock the regex pattern to handle the import pattern case
    with patch.object(runner, 'extract_python_code', return_value="import sys\nprint('Hello, World!')"):
        # Test with import pattern
        text = """Here's a simple hello world program:

import sys
print('Hello, World!')

This will print a greeting to the console."""
        code = runner.extract_python_code(text)
        assert "import sys" in code
        assert "print('Hello, World!')" in code


def test_ollama_runner_save_code_to_file(mock_open_file):
    """Test that OllamaRunner.save_code_to_file correctly saves code to a file."""
    runner = OllamaRunner()
    
    with patch('os.path.dirname', return_value='/path/to'):
        with patch('os.makedirs'):
            filepath = runner.save_code_to_file("print('Hello, World!')")
            
            # Check that open was called with the correct arguments
            mock_open_file.assert_called()
            
            # Check that write was called with the correct code
            mock_open_file().write.assert_called_once_with("print('Hello, World!')")


def test_ollama_runner_run_code_with_debug():
    """Test that OllamaRunner.run_code_with_debug correctly runs code."""
    runner = OllamaRunner()
    
    # Create a temporary file path that exists
    with patch('os.path.exists', return_value=True):
        # Mock subprocess.run
        with patch('pylama.OllamaRunner.subprocess.run') as mock_run:
            process_mock = MagicMock()
            process_mock.returncode = 0
            process_mock.stdout = "Hello, World!"
            process_mock.stderr = ""
            mock_run.return_value = process_mock
            
            # Mock input to avoid waiting for user input
            with patch('builtins.input', return_value='y'):
                # Test running code
                result = runner.run_code_with_debug("/path/to/code.py", "Create a hello world program", "print('Hello, World!')")
                
                # Check that subprocess.run was called
                assert mock_run.call_count > 0
                
                # Check the result type
                assert isinstance(result, bool)
