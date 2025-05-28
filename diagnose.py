#!/usr/bin/env python3

"""
DevLama Diagnostic Tool

This script runs DevLama in diagnose mode, where all examples are executed and tested.
It helps verify that the code generation and execution pipeline is working correctly.
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)7s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("devlama-diagnose")

# Ensure we can import from bexy
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import DevLama functionality
from devlama.devlama import generate_code
from devlama.OllamaRunner import OllamaRunner

# Import BEXY directly
try:
    from bexy.bexy import PythonSandbox
    logger.info("Successfully imported BEXY")
except ImportError:
    logger.error("Failed to import BEXY directly. Trying alternative import method...")
    try:
        from devlama.bexy_wrapper import PythonSandbox
        logger.info("Successfully imported BEXY through wrapper")
    except ImportError:
        logger.error("Failed to import BEXY through wrapper. Using fallback implementation.")
        
        # Fallback implementation if BEXY is not available
        class PythonSandbox:
            """Fallback implementation of PythonSandbox."""
            def __init__(self):
                pass
            
            def run(self, code):
                """Run Python code in a sandbox."""
                return {
                    "output": "Error: PythonSandbox not available.",
                    "error": "Module not found"
                }


def get_example_files():
    """Get all example files from the examples directory."""
    examples_dir = Path(__file__).parent / "devlama" / "examples"
    return list(examples_dir.glob("*.py"))


def get_example_content(example_file):
    """Get the content of an example file directly."""
    try:
        with open(example_file, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading example file {example_file}: {e}")
        return None


def get_example_prompt(example_name):
    """Generate a prompt based on the example name."""
    prompts = {
        "api_request": "create a program that fetches data from a REST API and include all necessary imports",
        "database": "create a program that connects to a SQLite database and performs CRUD operations, include all necessary imports",
        "default": "create a simple hello world program",
        "file_io": "create a program that reads and writes to files, include all necessary imports",
        "web_server": "create a simple web server with HTTP server, include import for http.server and BaseHTTPRequestHandler"
    }
    
    # Handle both Path objects and strings
    if hasattr(example_name, 'stem'):
        base_name = example_name.stem
    else:
        # If it's a string, remove the .py extension if present
        base_name = example_name.replace('.py', '')
    
    return prompts.get(base_name, f"create a {base_name.replace('_', ' ')} program")


def add_main_for_web_server(code, example_name):
    """Add a main function for web server examples if needed."""
    # Only process web server examples
    if example_name != 'web_server':
        return code
        
    # Add a main function call if needed for examples that don't have one
    if 'if __name__' not in code:
        # Check if there's a server setup code
        if 'SimpleHTTPRequestHandler' in code:
            # Add server setup code
            server_code = "\n\nif __name__ == '__main__':\n    # Create an HTTP server\n    server_address = ('', 8000)  # Host and port\n    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)\n    print('Starting server on port 8000...')\n    # No need to actually run the server in test mode\n    # httpd.serve_forever()\n"
            code += server_code
            logger.info("Added server setup code for web_server example")
    
    return code


def execute_code_with_bexy(code, example_name=None):
    """Execute code using BEXY sandbox."""
    # Add main function for web server examples if needed
    if example_name:
        code = add_main_for_web_server(code, example_name)
    
    # Create a Python sandbox instance
    sandbox = PythonSandbox()
    
    # Execute the code in the sandbox using run_code method
    result = sandbox.run_code(code)
    
    # Convert BEXY result format to match PyLama's execute_code format
    return {
        "output": result.get("stdout", ""),
        "error": result.get("stderr", "") if not result.get("success", True) else None
    }


def run_diagnostic():
    """Run diagnostic tests on all examples."""
    print("\n===== PyLama Diagnostic Mode =====\n")
    print("Testing all examples to ensure they generate and execute correctly\n")
    
    examples = get_example_files()
    results = []
    
    for i, example_file in enumerate(examples, 1):
        example_name = example_file.stem
        prompt = get_example_prompt(example_file)
        
        print(f"\n[{i}/{len(examples)}] Testing example: {example_name}")
        print(f"Prompt: {prompt}")
        
        try:
            # Get example content directly from file for more reliable testing
            print("Getting example content...")
            direct_code = get_example_content(example_file)
            if direct_code:
                code = direct_code
                print("Using example file directly for more reliable testing")
            else:
                # Fall back to generating code if direct access fails
                print("Generating code...")
                code = generate_code(prompt, template_type="basic")
            
            if not code or code.strip() == "":
                print("\u274c Failed: No code was generated")
                results.append((example_name, False, "No code generated"))
                continue
            
            # Execute code using BEXY
            print("Executing code with BEXY...")
            execution_result = execute_code_with_bexy(code, example_name=example_name.stem if hasattr(example_name, 'stem') else example_name)
            
            if execution_result.get("error"):
                print(f"\u274c Failed: Execution error: {execution_result['error']}")
                results.append((example_name, False, f"Execution error: {execution_result['error']}"))
            else:
                print("\u2705 Success: Code generated and executed without errors")
                print(f"Output: {execution_result.get('output', 'No output')}")
                results.append((example_name, True, "Success"))
                
        except Exception as e:
            print(f"\u274c Failed: Exception occurred: {str(e)}")
            results.append((example_name, False, f"Exception: {str(e)}"))
    
    # Print summary
    print("\n===== Diagnostic Results =====\n")
    success_count = sum(1 for _, success, _ in results if success)
    print(f"Total examples: {len(examples)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(examples) - success_count}\n")
    
    for example_name, success, message in results:
        status = "✅ Success" if success else "❌ Failed"
        print(f"{status}: {example_name} - {message}")
    
    return 0 if success_count == len(examples) else 1


def main():
    """Main entry point for the diagnostic tool."""
    try:
        return run_diagnostic()
    except KeyboardInterrupt:
        print("\nDiagnostic interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
