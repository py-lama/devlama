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
from DependencyManager import DependencyManager
from OllamaRunner import OllamaRunner
from templates import get_template

# Import from the new packages
from pyllm import get_models, get_default_model, set_default_model, install_model
from pybox import PythonSandbox, DockerSandbox

# Create .pylama directory
PACKAGE_DIR = os.path.join(os.path.expanduser('~'), '.pylama')
os.makedirs(PACKAGE_DIR, exist_ok=True)

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels"""
    grey = "\x1b[38;21m"
    blue = "\x1b[34;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    COLORS = {
        logging.DEBUG: blue,
        logging.INFO: grey,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: bold_red
    }
    
    def format(self, record):
        log_fmt = f"%(asctime)s - %(levelname)8s - %(message)s"
        if record.levelno in self.COLORS:
            log_fmt = f"{self.COLORS[record.levelno]}{log_fmt}{self.reset}"
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

# Configure root logger
log_file = os.path.join(PACKAGE_DIR, 'pylama.log')
logger = logging.getLogger('pylama')
logger.setLevel(logging.INFO)

# Create console handler with colored output
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter())

# Create file handler
file_handler = logging.FileHandler(log_file)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)

# Add handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)

logger.info('Application started')
logger.debug(f'Logs directory: {PACKAGE_DIR}')

# Load environment variables
load_dotenv()

# Function to install basic dependencies
def ensure_basic_dependencies():
    """Checks and installs basic dependencies needed for the script to work."""
    basic_dependencies = ['setuptools', 'requests', 'importlib-metadata', 'python-dotenv']

    for dep in basic_dependencies:
        try:
            # Try to import to check if it's installed
            if dep == 'setuptools':
                import setuptools
            elif dep == 'requests':
                import requests
            elif dep == 'importlib-metadata':
                try:
                    # Python 3.8+ has this built-in
                    from importlib import metadata
                except ImportError:
                    # For older Python versions
                    import importlib_metadata
            elif dep == 'python-dotenv':
                from dotenv import load_dotenv
        except ImportError:
            logger.info(f"Installing basic dependency: {dep}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                logger.info(f"Installed {dep}")
            except subprocess.CalledProcessError:
                logger.error(f"Failed to install {dep}. Aborting.")
                sys.exit(1)


# Install basic dependencies before importing other modules
ensure_basic_dependencies()



def parse_arguments():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description='PyLama - Python Code Generator using LLM models')
    parser.add_argument('prompt', nargs='*', help='Task to be performed by Python code')
    parser.add_argument('-t', '--template', choices=['basic', 'platform_aware', 'dependency_aware', 'testable', 'secure', 'performance', 'pep8'], 
                        default='platform_aware', help='Type of template to use')
    parser.add_argument('-d', '--dependencies', help='List of allowed dependencies (only for template=dependency_aware)')
    parser.add_argument('-m', '--model', help='Name of the Ollama model to use')
    return parser.parse_args()

def main():
    """Main program function."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Check if Ollama is installed
        try:
            result = subprocess.run([os.environ.get("OLLAMA_PATH", "ollama"), "--version"],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            if result.returncode != 0:
                print("Ollama is not properly installed.")
                print("Please install Ollama: https://ollama.ai/download")
                return
            print(f"Found Ollama: {result.stdout.decode('utf-8').strip()}")
        except FileNotFoundError:
            print("Ollama is not installed or not available in the system path.")
            print("Please install Ollama: https://ollama.ai/download")
            return

        # Create class instances
        ollama = OllamaRunner(model=args.model) if args.model else OllamaRunner()
        dependency_manager = DependencyManager()

        # Start Ollama
        ollama.start_ollama()

        # Get query from the user
        if args.prompt:
            # If arguments were provided, join them into a single prompt
            prompt = ' '.join(args.prompt)
        else:
            # Otherwise use the default prompt from environment variables or ask the user
            prompt = os.environ.get("TEST_PROMPT_1")
            if not prompt:
                prompt = input("Enter the task to be performed by Python code: ")

        # Prepare arguments for the template
        template_args = {}
        
        # Add specific arguments for the selected template
        if args.template == 'platform_aware':
            template_args['platform'] = platform.system()
            template_args['os'] = f"{platform.system()} {platform.release()}"
        elif args.template == 'dependency_aware' and args.dependencies:
            template_args['dependencies'] = args.dependencies
        
        # Send query to Ollama using the selected template
        logger.info(f"Using template: {args.template}")
        response = ollama.query_ollama(
            prompt,  # Basic task
            template_type=args.template,  # Use selected template
            **template_args  # Pass additional arguments for the template
        )

        if not response:
            print("No response received from Ollama.")
            return

        print("\nResponse received from Ollama. Extracting Python code...")

        # Extract Python code from the response
        code = ollama.extract_python_code(response)

        if not code:
            print("Failed to extract Python code from the response.")
            print("Check the 'ollama_response_debug.txt' or 'ollama_raw_response.json' file for the full response.")
            return

        print("\nExtracted Python code:")
        print("-" * 40)
        print(code)
        print("-" * 40)

        # Save code to a file in the .pylama directory
        code_file = ollama.save_code_to_file(code, os.path.join(PACKAGE_DIR, 'generated_script.py'))
        print(f"\nCode saved to file: {code_file}")

        # Find and install dependencies
        modules = dependency_manager.extract_imports(code)
        installed, missing = dependency_manager.check_dependencies(modules)

        print(f"\nFound modules: {', '.join(modules) if modules else 'none'}")
        print(f"Installed modules: {', '.join(installed) if installed else 'none'}")

        if missing:
            print(f"Missing dependencies: {', '.join(missing)}")
            if not dependency_manager.install_dependencies(missing):
                print("Script execution aborted due to dependency installation error.")
                return
        else:
            print("All dependencies are already installed")

        # Automatically run code with debugging
        ollama.run_code_with_debug(code_file, prompt, code)

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Stop Ollama if it was started by this script
        if 'ollama' in locals():
            ollama.stop_ollama()


if __name__ == "__main__":
    # Check if the script is run directly (not imported)
    # First install basic dependencies
    ensure_basic_dependencies()
    main()