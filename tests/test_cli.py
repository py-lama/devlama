import pytest
from unittest.mock import patch, MagicMock
from pylama.cli import main


@pytest.fixture
def mock_check_ollama():
    """Mock the check_ollama function to return a version."""
    with patch('pylama.pylama.check_ollama') as mock:
        mock.return_value = "0.1.0"
        yield mock


@pytest.fixture
def mock_generate_code():
    """Mock the generate_code function to return a real code snippet for known prompts."""
    def _mock(prompt, *args, **kwargs):
        if "hello world" in prompt.lower():
            return "print('Hello, World!')"
        return "# mock code"
    with patch('pylama.cli.generate_code', side_effect=_mock) as mock:
        yield mock


@pytest.fixture
def mock_execute_code():
    """Mock the execute_code function to return a successful result."""
    with patch('pylama.cli.execute_code') as mock:
        mock.return_value = {"output": "Hello, World!", "error": None}
        yield mock


@pytest.fixture
def mock_save_code_to_file():
    """Mock the save_code_to_file function to return a file path."""
    with patch('pylama.cli.save_code_to_file') as mock:
        mock.return_value = "/tmp/generated_script.py"
        yield mock


def test_main_help(capsys, mock_check_ollama):
    """Test that the help message is displayed when no arguments are provided."""
    with patch('sys.argv', ['pylama']):
        # The current implementation doesn't exit, it just prints the help message
        main()
    
    captured = capsys.readouterr()
    assert "usage:" in captured.out
    assert "PyLama - Python Code Generator" in captured.out


def test_main_generate_code(mock_check_ollama, mock_generate_code, mock_execute_code, mock_save_code_to_file):
    """Test that the main function generates code with the given prompt."""
    with patch('sys.argv', ['pylama', 'create', 'a', 'hello', 'world', 'program']):
        with patch('builtins.print') as mock_print:
            main()
    
    # Check that generate_code was called with the correct arguments
    mock_generate_code.assert_called_once()
    args, kwargs = mock_generate_code.call_args
    assert kwargs.get('template_type') == 'platform_aware'  # Default template
    assert args[0] == 'create a hello world program'


def test_main_with_template(mock_check_ollama, mock_generate_code, mock_execute_code, mock_save_code_to_file):
    """Test that the main function uses the specified template."""
    with patch('sys.argv', ['pylama', '-t', 'secure', 'create', 'a', 'login', 'form']):
        with patch('builtins.print') as mock_print:
            main()
    
    # Check that generate_code was called with the correct template
    mock_generate_code.assert_called_once()
    args, kwargs = mock_generate_code.call_args
    assert kwargs.get('template_type') == 'secure'
    assert args[0] == 'create a login form'


def test_main_with_model(mock_check_ollama, mock_generate_code, mock_execute_code, mock_save_code_to_file):
    """Test that the main function uses the specified model."""
    with patch('sys.argv', ['pylama', '-m', 'codellama:7b', 'create', 'a', 'hello', 'world', 'program']):
        with patch('builtins.print') as mock_print:
            main()
    
    # Check that generate_code was called with the correct model
    mock_generate_code.assert_called_once()
    args, kwargs = mock_generate_code.call_args
    assert kwargs.get('model') == 'codellama:7b'
    assert args[0] == 'create a hello world program'


def test_main_with_save_option(mock_check_ollama, mock_generate_code, mock_save_code_to_file):
    """Test that the main function saves the code to a file when the -s option is used."""
    with patch('sys.argv', ['pylama', '-s', 'create', 'a', 'hello', 'world', 'program']):
        with patch('builtins.print') as mock_print:
            main()
    
    # Check that save_code_to_file was called
    mock_save_code_to_file.assert_called_once_with("print('Hello, World!')")


def test_main_with_run_option(mock_check_ollama, mock_generate_code, mock_execute_code):
    """Test that the main function runs the code when the -r option is used."""
    with patch('sys.argv', ['pylama', '-r', 'create', 'a', 'hello', 'world', 'program']):
        with patch('builtins.print') as mock_print:
            main()
    
    # Check that execute_code was called
    mock_execute_code.assert_called_once_with("print('Hello, World!')")
