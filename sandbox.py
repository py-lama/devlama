#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced version of the sandbox module with additional functions and improved error handling.

This module provides extended functionality compared to the original sandbox.py module,
while maintaining backward compatibility.
"""

import os
import sys
import logging
import tempfile
import traceback
import subprocess
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

# Import components from the sandbox package
from sandbox.code_analyzer import CodeAnalyzer
from sandbox.dependency_manager import DependencyManager
from sandbox.python_sandbox import PythonSandbox
from sandbox.docker_sandbox import DockerSandbox
from sandbox.sandbox_manager import SandboxManager
from sandbox.utils import get_system_info, format_execution_result, ensure_dependencies

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class EnhancedSandboxManager(SandboxManager):
    """
    Enhanced version of SandboxManager with additional functions and improved error handling.
    """

    def __init__(self, use_docker: bool = None):
        """
        Initialize EnhancedSandboxManager.

        Args:
            use_docker: Whether to use Docker for running code. If None, the value will be
                        retrieved from the USE_DOCKER environment variable.
        """
        super().__init__(use_docker)
        self.code_analyzer = CodeAnalyzer()
        self.dependency_manager = DependencyManager()

    def run_code_with_retry(self, code: str, timeout: int = 30, max_retries: int = 3) -> Dict[str, Any]:
        """
        Run Python code with automatic retry in case of dependency errors.

        Args:
            code: Python code to run.
            timeout: Execution time limit in seconds.
            max_retries: Maximum number of retries in case of dependency errors.

        Returns:
            Dict[str, Any]: Code execution results.
        """
        result = None
        retries = 0
        missing_deps = []

        while retries < max_retries:
            # Analyze code and install dependencies
            deps_analysis = self.dependency_manager.analyze_dependencies(code)
            missing_deps = deps_analysis.get('missing_packages', [])

            if missing_deps:
                logger.info(f"Installing missing dependencies: {', '.join(missing_deps)}")
                for pkg in missing_deps:
                    self.dependency_manager.install_package(pkg)

            # Run the code
            result = self.run_code(code, timeout)

            # Check if there were dependency-related errors
            if result['success'] or 'ModuleNotFoundError' not in result.get('error', ''):
                break

            # Extract the name of the missing module from the error
            error_msg = result.get('error', '')
            import_error_match = None

            if 'ModuleNotFoundError: No module named' in error_msg:
                # Example: ModuleNotFoundError: No module named 'numpy'
                import_name = error_msg.split("'")
                if len(import_name) >= 2:
                    import_error_match = import_name[1]

            if import_error_match and import_error_match not in missing_deps:
                logger.info(f"Detected missing module: {import_error_match}")
                self.dependency_manager.install_package(import_error_match)
                missing_deps.append(import_error_match)

            retries += 1
            logger.info(f"Retrying code execution ({retries}/{max_retries})")

        # Add information about installed dependencies to the result
        if result:
            result['installed_dependencies'] = missing_deps

        return result

    def run_code_with_callback(self, code: str, callback: Callable[[Dict[str, Any]], None],
                               timeout: int = 30) -> None:
        """
        Run Python code and call a callback function with the results.

        Args:
            code: Python code to run.
            callback: Function to be called with the code execution results.
            timeout: Execution time limit in seconds.
        """
        result = self.run_code_with_retry(code, timeout)
        callback(result)

    def run_code_in_file(self, file_path: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Run Python code from a file.

        Args:
            file_path: Path to the Python code file.
            timeout: Execution time limit in seconds.

        Returns:
            Dict[str, Any]: Code execution results.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            return self.run_code_with_retry(code, timeout)
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': traceback.format_exc(),
                'execution_time': 0
            }

    def run_interactive_session(self, initial_code: str = "") -> None:
        """
        Run an interactive Python session with code execution capability.

        Args:
            initial_code: Python code to execute at the beginning of the session.
        """
        print("=== Interactive Python Session ===")
        print("Type 'exit()' or 'quit()' to end the session.")
        print("Type 'help()' to get help.")

        # Execute initial code if it exists
        if initial_code:
            print("\nExecuting initial code:")
            result = self.run_code_with_retry(initial_code)
            if result['stdout']:
                print(result['stdout'])
            if result['stderr']:
                print(f"Errors:\n{result['stderr']}")

        # Main interactive loop
        context = {}
        while True:
            try:
                user_input = input(">>> ")

                if user_input.lower() in ('exit()', 'quit()'):
                    break
                elif user_input.lower() == 'help()':
                    print("\nInteractive Python Session Help:")
                    print("  exit(), quit() - End the session")
                    print("  help() - Display this help")
                    print("  clear() - Clear the screen")
                    print("  reset() - Reset the session context")
                    continue
                elif user_input.lower() == 'clear()':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue
                elif user_input.lower() == 'reset()':
                    context = {}
                    print("Session context has been reset.")
                    continue

                # Execute user code
                result = self.run_code_with_retry(user_input)
                if result['stdout']:
                    print(result['stdout'])
                if result['stderr']:
                    print(f"Errors:\n{result['stderr']}")

            except KeyboardInterrupt:
                print("\nInterrupted by user. Type 'exit()' to end the session.")
            except Exception as e:
                print(f"Error: {str(e)}")

        print("\nSession ended.")


# Create an instance of EnhancedSandboxManager for backward compatibility
_enhanced_sandbox_manager = EnhancedSandboxManager.from_env()


# Functions for backward compatibility and new functions

def run_code_with_retry(code: str, timeout: int = 30, max_retries: int = 3) -> Dict[str, Any]:
    """
    Run Python code with automatic retry in case of dependency errors.

    Args:
        code: Python code to run.
        timeout: Execution time limit in seconds.
        max_retries: Maximum number of retries in case of dependency errors.

    Returns:
        Dict[str, Any]: Code execution results.
    """
    return _enhanced_sandbox_manager.run_code_with_retry(code, timeout, max_retries)


def run_code_in_file(file_path: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Run Python code from a file.

    Args:
        file_path: Path to the Python code file.
        timeout: Execution time limit in seconds.

    Returns:
        Dict[str, Any]: Code execution results.
    """
    return _enhanced_sandbox_manager.run_code_in_file(file_path, timeout)


def run_interactive_session(initial_code: str = "") -> None:
    """
    Run an interactive Python session with code execution capability.

    Args:
        initial_code: Python code to execute at the beginning of the session.
    """
    _enhanced_sandbox_manager.run_interactive_session(initial_code)


# Main function for testing
def main():
    """
    Main function for testing the sandbox module.
    """
    print("=== Sandbox Module Test ===\n")

    # Example code for testing
    code = """
import os
import sys
import math
import platform

print('System Information:')
print(f'Operating System: {platform.system()} {platform.release()}')
print(f'Python Version: {sys.version}')
print(f'Current Directory: {os.getcwd()}')

# Example of mathematical calculations
print('\nMathematical Calculations:')
print(f'Pi: {math.pi}')
print(f'Square root of 16: {math.sqrt(16)}')
print(f'Factorial of 5: {math.factorial(5)}')
"""

    # Run code with automatic retry
    print("Running code with automatic retry:")
    result = run_code_with_retry(code)
    print(f"Success: {result['success']}")
    print(f"Standard output:\n{result['stdout']}")

    # Save code to a temporary file and run it
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name

    print("\nRunning code from file:")
    result = run_code_in_file(temp_path)
    print(f"Success: {result['success']}")
    print(f"Standard output:\n{result['stdout']}")

    # Remove temporary file
    os.unlink(temp_path)

    print("\nTest completed.")

    # Ask the user if they want to run an interactive session
    choice = input("\nDo you want to run an interactive session? (y/n): ")
    if choice.lower() in ('y', 'yes'):
        run_interactive_session()


if __name__ == "__main__":
    main()
