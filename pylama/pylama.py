# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import platform
from typing import List, Dict, Any, Tuple, Optional
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Import from the new packages
import os
import sys

# Add parent directory to sys.path to find pybox and pyllm packages
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import directly using importlib to avoid package structure issues
import importlib.util

# Get the absolute paths to the modules we need
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import models.py from pyllm
models_path = os.path.join(parent_dir, 'pyllm', 'pyllm', 'models.py')
spec = importlib.util.spec_from_file_location('models', models_path)
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)

# Get the functions we need from models.py
get_models = models.get_models
get_default_model = models.get_default_model
set_default_model = models.set_default_model
install_model = models.install_model

# Import python_sandbox.py from pybox
python_sandbox_path = os.path.join(parent_dir, 'pybox', 'pybox', 'python_sandbox.py')
spec = importlib.util.spec_from_file_location('python_sandbox', python_sandbox_path)
python_sandbox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(python_sandbox)
PythonSandbox = python_sandbox.PythonSandbox

# Import docker_sandbox.py from pybox
docker_sandbox_path = os.path.join(parent_dir, 'pybox', 'pybox', 'docker_sandbox.py')
spec = importlib.util.spec_from_file_location('docker_sandbox', docker_sandbox_path)
docker_sandbox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(docker_sandbox)
DockerSandbox = docker_sandbox.DockerSandbox

# Create .pylama directory
PACKAGE_DIR = os.path.join(os.path.expanduser('~'), '.pylama')
os.makedirs(PACKAGE_DIR, exist_ok=True)

# Configure root logger
log_file = os.path.join(PACKAGE_DIR, 'pylama.log')
logger = logging.getLogger('pylama')
logger.setLevel(logging.INFO)

# Add file handler
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Add console handler with colors
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

# Load environment variables
load_dotenv()

# Import local modules
from .OllamaRunner import OllamaRunner
from .templates import get_template
from .dependency_utils import check_dependencies, install_dependencies, extract_imports


def check_ollama() -> Optional[str]:
    """
    Check if Ollama is running and return its version.
    """
    try:
        result = subprocess.run(
            ["ollama", "version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"Found Ollama: {version}")
            logger.info(f"Ollama is running (version: {version})")
            return version
        else:
            logger.error("Ollama is not running or not installed")
            return None
    except Exception as e:
        logger.error(f"Error checking Ollama: {str(e)}")
        return None


def generate_code(prompt: str, template_type: str = "platform_aware", dependencies: str = None, model: str = None) -> str:
    """
    Generate Python code based on the given prompt and template.
    """
    # Get the appropriate template
    template = get_template(prompt, template_type, dependencies=dependencies)
    logger.info(f"Using template: {template_type}")
    
    # Use the specified model or get the default one
    if not model:
        model = get_default_model()
    
    # Generate code using Ollama
    logger.info(f"Sending query to model {model}...")
    ollama = OllamaRunner(model)
    response = ollama.generate(template)
    
    # Extract Python code from the response
    print("\nResponse received from Ollama. Extracting Python code...")
    code = ollama.extract_code(response)
    
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
