import pytest
from unittest.mock import patch, MagicMock
from devlama.cli import main


@pytest.fixture
def mock_check_ollama():
    """Mock the check_ollama function to return a version."""
    with patch('devlama.devlama.check_ollama') as mock:
        mock.return_value = "0.1.0"
        yield mock


@pytest.fixture
def mock_ollama_runner():
    """Mock the OllamaRunner class to return predictable results."""
    mock_runner = MagicMock()
    
    # Mock the query_ollama method
    def mock_query_ollama(prompt, template_type='platform_aware', **kwargs):
        if "hello world" in prompt.lower():
            return "print('Hello, World!')"
        return "# mock code"
    
    mock_runner.query_ollama.side_effect = mock_query_ollama
    mock_runner.check_model_availability.return_value = True
    
    with patch('devlama.cli.OllamaRunner', return_value=mock_runner) as mock_class:
        yield mock_runner


@pytest.fixture
def mock_execute_code():
    """Mock the execute_code function to return a successful result."""
    with patch('devlama.cli.execute_code') as mock:
        mock.return_value = {"output": "Hello, World!", "error": None}
        yield mock


@pytest.fixture
def mock_save_code_to_file():
    """Mock the save_code_to_file function to return a file path."""
    with patch('devlama.cli.save_code_to_file') as mock:
        mock.return_value = "/tmp/generated_script.py"
        yield mock


def test_main_help(capsys):
    """Test that the help message is displayed when help flag is provided."""
    with pytest.raises(SystemExit):
        with patch('sys.argv', ['devlama', '--help']):
            main()
    
    captured = capsys.readouterr()
    assert "usage:" in captured.out
    assert "PyLama - Python Code Generator" in captured.out


def test_main_generate_code(mock_check_ollama, mock_ollama_runner, mock_execute_code, mock_save_code_to_file):
    """Test that the main function generates code with the given prompt."""
    with patch('sys.argv', ['devlama', 'create', 'a', 'hello', 'world', 'program']):
        with patch('builtins.print') as mock_print:
            main()
    
    # Check that query_ollama was called with the correct arguments
    mock_ollama_runner.query_ollama.assert_called_once()
    args, kwargs = mock_ollama_runner.query_ollama.call_args
    assert kwargs.get('template_type') == 'platform_aware'  # Default template
    assert args[0] == 'create a hello world program'


def test_main_with_template(mock_check_ollama, mock_ollama_runner, mock_execute_code, mock_save_code_to_file):
    """Test that the main function uses the specified template."""
    with patch('sys.argv', ['devlama', '-t', 'secure', 'create', 'a', 'login', 'form']):
        with patch('builtins.print') as mock_print:
            main()
    
    # Check that query_ollama was called with the correct template
    mock_ollama_runner.query_ollama.assert_called_once()
    args, kwargs = mock_ollama_runner.query_ollama.call_args
    assert kwargs.get('template_type') == 'secure'
    assert args[0] == 'create a login form'


def test_main_with_model(mock_check_ollama, mock_ollama_runner, mock_execute_code, mock_save_code_to_file):
    """Test that the main function uses the specified model."""
    with patch('sys.argv', ['devlama', '--model', 'codellama:7b', 'create', 'a', 'hello', 'world', 'program']):
        with patch('builtins.print') as mock_print:
            main()
    
    # Check that OllamaRunner was initialized with the correct model
    from devlama.cli import OllamaRunner
    OllamaRunner.assert_called_once()
    args, kwargs = OllamaRunner.call_args
    assert kwargs.get('model') == 'codellama:7b'
    assert kwargs.get('mock_mode') is False


def test_main_with_save_option(mock_check_ollama, mock_ollama_runner, mock_save_code_to_file):
    """Test that the main function saves the code to a file when the -s option is used."""
    # Set up the mock to return a specific code
    mock_ollama_runner.query_ollama.return_value = "print('Hello, World!')"
    
    with patch('sys.argv', ['devlama', '-s', 'create', 'a', 'hello', 'world', 'program']):
        with patch('builtins.print') as mock_print:
            main()
    
    # Check that save_code_to_file was called
    mock_save_code_to_file.assert_called_once()


def test_main_with_run_option(mock_check_ollama, mock_ollama_runner, mock_execute_code):
    """Test that the main function runs the code when the -r option is used."""
    # Set up the mock to return a specific code
    mock_ollama_runner.query_ollama.return_value = "print('Hello, World!')"
    
    with patch('sys.argv', ['devlama', '-r', 'create', 'a', 'hello', 'world', 'program']):
        with patch('builtins.print') as mock_print:
            main()
    
    # Check that execute_code was called
    mock_execute_code.assert_called_once()
