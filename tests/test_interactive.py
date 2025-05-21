import sys
import pytest
from unittest.mock import patch
from io import StringIO
from pylama.cli import interactive_mode

def run_interactive_mode_with_inputs(inputs):
    """
    Helper to run interactive_mode with a list of user inputs.
    Returns the captured stdout output.
    """
    input_iter = iter(inputs)
    def mock_input(prompt):
        try:
            return next(input_iter)
        except StopIteration:
            raise KeyboardInterrupt  # Simulate Ctrl+C

    with patch('builtins.input', side_effect=mock_input):
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            try:
                interactive_mode()
            except KeyboardInterrupt:
                pass
            return mock_stdout.getvalue()

def test_interactive_models_list():
    # Simulate entering 'models' then Ctrl+C
    output = run_interactive_mode_with_inputs(['models'])
    assert 'Available models' in output
    assert 'SpeakLeash/bielik-7b-instruct-v0.1-gguf' in output
    assert 'llama2' in output

def test_interactive_set_model():
    # Simulate setting a model that exists
    output = run_interactive_mode_with_inputs(['set model SpeakLeash/bielik-7b-instruct-v0.1-gguf', 'models'])
    assert 'Model changed to' in output or 'Current model' in output
    assert 'SpeakLeash/bielik-7b-instruct-v0.1-gguf' in output

def test_interactive_exit():
    # Simulate exit
    output = run_interactive_mode_with_inputs(['exit'])
    assert 'Exiting PyLama' in output
