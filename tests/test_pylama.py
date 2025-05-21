import pytest
from unittest.mock import patch, MagicMock
from pylama.pylama import check_ollama, generate_code, save_code_to_file, execute_code


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run to simulate Ollama version check."""
    with patch('subprocess.run') as mock:
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.stdout = "ollama 0.1.0"
        mock.return_value = process_mock
        yield mock


@pytest.fixture
def mock_ollama_runner():
    """Mock OllamaRunner to simulate code generation."""
    with patch('pylama.pylama.OllamaRunner') as mock:
        runner_instance = MagicMock()
        runner_instance.generate.return_value = "Generated response with code"
        runner_instance.extract_code.return_value = "print('Hello, World!')"
        mock.return_value = runner_instance
        yield mock


@pytest.fixture
def mock_python_sandbox():
    """Mock PythonSandbox to simulate code execution."""
    with patch('pylama.pylama.PythonSandbox') as mock:
        sandbox_instance = MagicMock()
        sandbox_instance.run.return_value = {"output": "Hello, World!", "error": None}
        mock.return_value = sandbox_instance
        yield mock


def test_check_ollama(mock_subprocess_run):
    """Test that check_ollama returns the Ollama version when it's running."""
    version = check_ollama()
    assert version == "ollama 0.1.0"
    mock_subprocess_run.assert_called_once_with(
        ["ollama", "version"],
        capture_output=True,
        text=True,
        check=False,
    )


def test_check_ollama_not_running():
    """Test that check_ollama returns None when Ollama is not running."""
    with patch('subprocess.run') as mock:
        process_mock = MagicMock()
        process_mock.returncode = 1
        mock.return_value = process_mock
        version = check_ollama()
        assert version is None


def test_generate_code(mock_ollama_runner):
    """Test that generate_code returns the generated code."""
    prompt = "Create a hello world program"
    code = generate_code(prompt, "basic")
    assert code == "print('Hello, World!')"
    
    # Check that OllamaRunner was instantiated and methods were called
    mock_ollama_runner.assert_called_once()
    runner_instance = mock_ollama_runner.return_value
    runner_instance.generate.assert_called_once()
    runner_instance.extract_code.assert_called_once_with("Generated response with code")


def test_save_code_to_file():
    """Test that save_code_to_file saves the code to a file."""
    with patch('builtins.open', create=True) as mock_open:
        with patch('os.path.join', return_value="/tmp/generated_script.py"):
            filepath = save_code_to_file("print('Hello, World!')")
            assert filepath == "/tmp/generated_script.py"
            mock_open.assert_called_once_with("/tmp/generated_script.py", "w")


def test_execute_code(mock_python_sandbox):
    """Test that execute_code executes the code using the sandbox."""
    result = execute_code("print('Hello, World!')")
    assert result == {"output": "Hello, World!", "error": None}
    
    # Check that PythonSandbox was instantiated and run was called
    mock_python_sandbox.assert_called_once()
    sandbox_instance = mock_python_sandbox.return_value
    sandbox_instance.run.assert_called_once_with("print('Hello, World!')")


def test_execute_code_with_docker():
    """Test that execute_code uses DockerSandbox when use_docker is True."""
    with patch('pylama.pylama.DockerSandbox') as mock_docker_sandbox:
        docker_instance = MagicMock()
        docker_instance.run.return_value = {"output": "Hello from Docker!", "error": None}
        mock_docker_sandbox.return_value = docker_instance
        
        result = execute_code("print('Hello from Docker!')", use_docker=True)
        assert result == {"output": "Hello from Docker!", "error": None}
        
        # Check that DockerSandbox was instantiated and run was called
        mock_docker_sandbox.assert_called_once()
        docker_instance.run.assert_called_once_with("print('Hello from Docker!')")
