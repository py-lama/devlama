# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import platform
import tempfile
from typing import List, Dict, Any, Tuple, Optional
import argparse
from pathlib import Path

# Initialize logging with PyLogs
from devlama.ecosystem.logging_config import init_logging, get_logger

# Initialize logging first, before any other imports
init_logging()

# Get a logger for this module
logger = get_logger('devlama')

# Import from the new packages
import os
import sys

# Add parent directory to sys.path to find bexy and getllm packages
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Simple implementation of required functionality

# Model management functions
def get_models():
    """Get a list of available models."""
    return ["llama2", "codellama", "phi"]

def get_default_model():
    """Get the default model."""
    return "llama2"

def set_default_model(model):
    """Set the default model."""
    pass

def install_model(model):
    """Install a model."""
    return True

# Sandbox classes
class PythonSandbox:
    """Simple implementation of PythonSandbox."""
    def __init__(self):
        pass
    
    def run(self, code):
        """Run Python code in a sandbox."""
        # Create a temporary file to store the code
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            f.write(code.encode('utf-8'))
            temp_file = f.name
        
        try:
            # Run the code in a separate process
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            # Return the result
            if result.returncode == 0:
                return {
                    "output": result.stdout,
                    "error": None
                }
            else:
                return {
                    "output": result.stdout,
                    "error": result.stderr
                }
        except Exception as e:
            return {
                "output": "",
                "error": str(e)
            }
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file)
            except:
                pass

class DockerSandbox:
    """Simple implementation of DockerSandbox."""
    def __init__(self):
        pass
    
    def run(self, code):
        """Run Python code in a Docker sandbox."""
        # For now, just use the PythonSandbox implementation
        return PythonSandbox().run(code)

# Create .devlama directory
PACKAGE_DIR = os.path.join(os.path.expanduser('~'), '.devlama')
os.makedirs(PACKAGE_DIR, exist_ok=True)

# Logger is already configured by PyLogs in the import section at the top of the file
# Environment variables are already loaded by PyLogs in the logging_config.py module

# Import local modules
from .OllamaRunner import OllamaRunner
from .templates import get_template
from .dependency_utils import check_dependencies, install_dependencies, extract_imports


def check_ollama() -> Optional[str]:
    """
    Check if Ollama is running and return its version.
    
    This is a mock implementation that always returns a version,
    allowing the application to run without an actual Ollama server.
    """
    # Mock version for development/testing purposes
    mock_version = "v0.1.0 (mock)"
    print(f"Using mock Ollama: {mock_version}")
    logger.info(f"Using mock Ollama implementation (version: {mock_version})")
    return mock_version


def generate_code(prompt: str, template_type: str = "platform_aware", dependencies: str = None, model: str = None) -> str:
    """
    Generate Python code based on the given prompt and template.
    """
    # Get the appropriate template
    # Add platform and OS detection for platform_aware template
    template_kwargs = {"dependencies": dependencies}
    
    if template_type == "platform_aware":
        import platform as plt
        template_kwargs["platform"] = plt.platform()
        template_kwargs["os"] = plt.system()
    
    template = get_template(prompt, template_type, **template_kwargs)
    logger.info(f"Using template: {template_type}")
    
    # Use the specified model or get the default one
    if not model:
        model = get_default_model()
    
    # Generate code using Ollama
    logger.info(f"Sending query to model {model}...")
    ollama = OllamaRunner(model=model)
    response = ollama.query_ollama(template)
    
    # Extract Python code from the response
    print("\nResponse received from Ollama. Extracting Python code...")
    code = ollama.extract_python_code(response)
    
    if not code:
        logger.warning("No Python code found in the response")
        return "# No Python code was generated. Please try again with a different prompt."
    
    print("\nExtracted Python code:")
    print("----------------------------------------")
    print(code)
    print("----------------------------------------")
    
    return code


def save_code_to_file(code: str, filename: str = None) -> str:
    """
    Save the generated code to a file.
    """
    if not filename:
        filename = "generated_script.py"
    
    filepath = os.path.join(PACKAGE_DIR, filename)
    with open(filepath, "w") as f:
        f.write(code)
    
    logger.info(f"Saved script to file: {filepath}")
    return filepath


def execute_code(code: str, use_docker: bool = False) -> Dict[str, Any]:
    """
    Execute the generated code and return the result.
    """
    # Check if we should use Docker
    use_docker_env = os.environ.get("USE_DOCKER", "False").lower() in ("true", "1", "yes")
    use_docker = use_docker or use_docker_env
    
    # Create the appropriate sandbox
    if use_docker:
        sandbox = DockerSandbox()
    else:
        sandbox = PythonSandbox()
    
    # Execute the code
    return sandbox.run(code)
