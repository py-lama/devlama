#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the PyLama diagnostic functionality.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to import diagnose
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from diagnose import (
    get_example_files,
    get_example_content,
    get_example_prompt,
    add_main_for_web_server,
    execute_code_with_pybox,
    run_diagnostic
)


@pytest.fixture
def mock_examples_dir():
    """Mock the examples directory with test examples."""
    with patch('diagnose.get_example_files') as mock:
        # Create mock example files
        example1 = MagicMock()
        example1.stem = 'web_server'
        example1.name = 'web_server.py'
        
        example2 = MagicMock()
        example2.stem = 'file_io'
        example2.name = 'file_io.py'
        
        mock.return_value = [example1, example2]
        yield mock


@pytest.fixture
def mock_example_content():
    """Mock the example content retrieval."""
    with patch('diagnose.get_example_content') as mock:
        mock.return_value = "print('Test example')\n"
        yield mock


@pytest.fixture
def mock_pybox():
    """Mock the PyBox sandbox."""
    with patch('diagnose.PythonSandbox') as mock:
        sandbox_instance = MagicMock()
        sandbox_instance.run_code.return_value = {
            'success': True,
            'stdout': 'Test output',
            'stderr': ''
        }
        mock.return_value = sandbox_instance
        yield mock


def test_get_example_prompt():
    """Test that get_example_prompt returns the correct prompt for each example."""
    # Test web_server example
    assert 'web server' in get_example_prompt('web_server')
    
    # Test file_io example
    assert 'files' in get_example_prompt('file_io')
    
    # Test api_request example
    assert 'API' in get_example_prompt('api_request')
    
    # Test database example
    assert 'database' in get_example_prompt('database')
    
    # Test default example
    assert 'hello world' in get_example_prompt('default')
    
    # Test unknown example - should return a generic prompt with the example name
    assert 'create a unknown example program' == get_example_prompt('unknown_example')


def test_add_main_for_web_server():
    """Test that add_main_for_web_server adds a main function to web server examples."""
    # Test with web_server example
    code = "class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):\n    pass\n"
    result = add_main_for_web_server(code, 'web_server')
    assert "if __name__ == '__main__'" in result
    assert "SimpleHTTPRequestHandler" in result
    
    # Test with non-web_server example
    code = "print('Hello')\n"
    result = add_main_for_web_server(code, 'file_io')
    assert result == code  # Should not modify non-web_server examples


def test_execute_code_with_pybox(mock_pybox):
    """Test that execute_code_with_pybox correctly executes code using PyBox."""
    code = "print('Test')\n"
    result = execute_code_with_pybox(code)
    
    # Check that PyBox was called correctly
    mock_pybox.assert_called_once()
    mock_pybox.return_value.run_code.assert_called_once_with(code)
    
    # Check the result format
    assert 'output' in result
    assert 'error' in result
    assert result['output'] == 'Test output'
    assert result['error'] is None


def test_execute_code_with_pybox_for_web_server(mock_pybox):
    """Test that execute_code_with_pybox handles web server examples correctly."""
    code = "class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):\n    pass\n"
    result = execute_code_with_pybox(code, example_name='web_server')
    
    # Check that PyBox was called with modified code
    mock_pybox.assert_called_once()
    called_code = mock_pybox.return_value.run_code.call_args[0][0]
    assert "if __name__ == '__main__'" in called_code


@patch('diagnose.execute_code_with_pybox')
@patch('diagnose.generate_code')
@patch('diagnose.print')
def test_run_diagnostic(mock_print, mock_generate, mock_execute, mock_examples_dir, mock_example_content):
    """Test that run_diagnostic correctly processes all examples."""
    # Mock the generate_code function
    mock_generate.return_value = "print('Generated code')\n"
    
    # Mock the execute_code_with_pybox function
    mock_execute.return_value = {'output': 'Test output', 'error': None}
    
    # Run the diagnostic
    result = run_diagnostic()
    
    # Check that all examples were processed
    assert mock_examples_dir.call_count == 1
    assert mock_example_content.call_count == 2  # One for each example
    assert mock_execute.call_count == 2  # One for each example
    
    # Check the result
    assert result == 0  # Should return 0 for success
