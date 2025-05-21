import os
import json
import time
import subprocess
import sys
import re
import requests
import importlib
import logging
import platform
from typing import List, Dict, Any, Tuple, Optional
from .templates import get_template

# Create .pylama directory if it doesn't exist
PACKAGE_DIR = os.path.join(os.path.expanduser('~'), '.pylama')
os.makedirs(PACKAGE_DIR, exist_ok=True)

# Configure logger for OllamaRunner
logger = logging.getLogger('pylama.ollama')
logger.setLevel(logging.INFO)

# Create file handler for Ollama-specific logs
ollama_log_file = os.path.join(PACKAGE_DIR, 'pylama_ollama.log')
file_handler = logging.FileHandler(ollama_log_file)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

logger.debug('OllamaRunner initialized')

# Use importlib.metadata instead of pkg_resources
try:
    # Python 3.8+
    from importlib import metadata
except ImportError:
    # For older Python versions
    import importlib_metadata as metadata

# Import sandbox if we're using Docker mode
USE_DOCKER = os.getenv('USE_DOCKER', 'False').lower() in ('true', '1', 't')
if USE_DOCKER:
    try:
        from sandbox import DockerSandbox
    except ImportError:
        logger.error("Cannot import sandbox module. Make sure the sandbox.py file is available.")
        sys.exit(1)


class OllamaRunner:
    """Class for running Ollama and executing generated code."""

    def __init__(self, ollama_path: str = None, model: str = None):
        self.ollama_path = ollama_path or os.getenv('OLLAMA_PATH', 'ollama')
        self.model = model or os.getenv('OLLAMA_MODEL', 'llama3')
        self.fallback_models = os.getenv('OLLAMA_FALLBACK_MODELS', '').split(',')
        self.ollama_process = None

        # Update to the correct Ollama API endpoints
        self.generate_api_url = "http://localhost:11434/api/generate"
        self.chat_api_url = "http://localhost:11434/api/chat"
        self.version_api_url = "http://localhost:11434/api/version"

        # Docker configuration
        self.use_docker = USE_DOCKER
        self.docker_sandbox = None
        if self.use_docker:
            self.docker_sandbox = DockerSandbox()
            logger.info("Using Docker mode for Ollama.")

    def start_ollama(self) -> None:
        """Start the Ollama server if it's not already running."""
        if self.use_docker:
            # Run Ollama in Docker container
            if not self.docker_sandbox.start_container():
                raise RuntimeError("Failed to start Docker container with Ollama.")
            return

        try:
            # Check if Ollama is already running by querying the version
            response = requests.get(self.version_api_url)
            logger.info(f"Ollama is running (version: {response.json().get('version', 'unknown')})")
            return

        except requests.exceptions.ConnectionError:
            logger.info("Starting Ollama server...")
            # Run Ollama in the background
            self.ollama_process = subprocess.Popen(
                [self.ollama_path, "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # Wait for the server to start
            time.sleep(5)

            # Check if the server actually started
            try:
                response = requests.get(self.version_api_url)
                logger.info(f"Ollama server started (version: {response.json().get('version', 'unknown')})")
            except requests.exceptions.ConnectionError:
                logger.error("ERROR: Failed to start Ollama server.")
                if self.ollama_process:
                    logger.error("Error details:")
                    out, err = self.ollama_process.communicate(timeout=1)
                    logger.error(f"STDOUT: {out.decode('utf-8', errors='ignore')}")
                    logger.error(f"STDERR: {err.decode('utf-8', errors='ignore')}")
                raise RuntimeError("Failed to start Ollama server")

    def stop_ollama(self) -> None:
        """Stop the Ollama server if it was started by this script."""
        if self.use_docker:
            if self.docker_sandbox:
                self.docker_sandbox.stop_container()
            return

        if self.ollama_process:
            logger.info("Stopping Ollama server...")
            self.ollama_process.terminate()
            self.ollama_process.wait()
            logger.info("Ollama server stopped")

    def query_ollama(self, prompt: str, template_type: str = None, **template_args) -> str:
        """
        Send a query to the Ollama API and return the response.
        
        This is a mock implementation that returns a simple example for the requested task
        without requiring an actual Ollama server.
        
        Args:
            prompt: Basic query or task to perform
            template_type: Type of template to use (optional)
            **template_args: Additional arguments for the template
        
        Returns:
            Response from the LLM model
        """
        # Log that we're using a mock implementation
        logger.info("Using mock code generation (Ollama not required)")
        
        # If a template type is provided, use it to format the query
        if template_type:
            formatted_prompt = get_template(prompt, template_type, **template_args)
            logger.debug(f"Used template {template_type} for the query")
        else:
            formatted_prompt = prompt
        
        # Extract the main task from the prompt
        task = formatted_prompt.lower()
        
        # Generate a simple example based on the task
        if "web server" in task:
            return self._load_example_from_file('web_server.py')
        elif "file" in task and ("read" in task or "write" in task):
            return self._load_example_from_file('file_io.py')
        elif "api" in task or "request" in task:
            return self._load_example_from_file('api_request.py')
        elif "database" in task or "sql" in task:
            return self._load_example_from_file('database.py')
        else:
            # Default example
            return self._load_example_from_file('default.py', prompt=formatted_prompt)

    def _load_example_from_file(self, filename, prompt=None) -> str:
        """Load an example from a file in the examples directory.
        
        Args:
            filename: The name of the file to load from the examples directory
            prompt: Optional prompt to include in the example
            
        Returns:
            The content of the example file
        """
        # Get the path to the examples directory
        examples_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'examples')
        example_path = os.path.join(examples_dir, filename)
        
        try:
            with open(example_path, 'r') as f:
                content = f.read()
                
            # Replace the placeholder in default.py if a prompt is provided
            if prompt and filename == 'default.py':
                content = content.replace('your task description', prompt)
                
            return content
        except Exception as e:
            logger.error(f"Error loading example from {example_path}: {e}")
            # Create a fallback example in case of error
            fallback_code = f"""# Error loading example: {str(e)}

# Here's a simple example instead:

def main():
    print("Hello, World!")
    return "Success"

if __name__ == '__main__':
    main()
"""
            return fallback_code
            
    # The old example methods have been replaced by the _load_example_from_file method
    
    # All example methods have been replaced by the _load_example_from_file method

    def try_chat_api(self, formatted_prompt):
        """Try using the chat API as an alternative."""
        try:
            # Try using /api/chat as an alternative API
            logger.info("Trying to use chat API...")
            chat_data = {
                "model": self.model,
                "messages": [{"role": "user", "content": formatted_prompt}],
                "stream": False
            }

            chat_response = requests.post(self.chat_api_url, json=chat_data)
            chat_response.raise_for_status()
            chat_json = chat_response.json()

            # Save raw response to a file for debugging
            if os.getenv('SAVE_RAW_RESPONSES', 'False').lower() in ('true', '1', 't'):
                debug_file = os.path.join(PACKAGE_DIR, "ollama_chat_response.json")
                with open(debug_file, "w", encoding="utf-8") as f:
                    json.dump(chat_json, f, indent=2)
                logger.debug(f'Saved raw response to {debug_file}')

            # Extract response from a different format
            if "message" in chat_json and "content" in chat_json["message"]:
                return chat_json["message"]["content"]
            return ""
        except Exception as chat_e:
            logger.error(f"Error communicating with chat API: {chat_e}")
            return ""

    def extract_python_code(self, text: str) -> str:
        """Extract Python code from the response."""

        # Check different possible code formats in the response
        patterns = [
            r"```python\s*(.*?)\s*```",  # Markdown code block
            r"```\s*(.*?)\s*```",  # Generic code block
            r"import .*?\n(.*?)(?:\n\n|$)"  # Code starting with import
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                return matches[0]

        # Jeśli nie znaleziono kodu za pomocą wyrażeń regularnych,
        # spróbuj znaleźć po linii importu
        lines = text.split('\n')
        import_lines = []
        code_lines = []
        collecting = False

        for line in lines:
            if 'import' in line and not collecting:
                collecting = True

            if collecting:
                code_lines.append(line)

        if code_lines:
            return '\n'.join(code_lines)

        # If all else fails, write the response to a debug file
        debug_dir = os.path.join(PACKAGE_DIR, 'debug')
        os.makedirs(debug_dir, exist_ok=True)

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        debug_file = os.path.join(debug_dir, f"ollama_response_debug_{timestamp}.txt")

        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(text)

        logger.info(f"DEBUG: Full response saved to file '{debug_file}'")
        return ""

    def save_code_to_file(self, code: str, filename: str = None) -> str:
        """Save the generated code to a file and return the path to the file."""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(PACKAGE_DIR, f"generated_script_{timestamp}.py")
        
        # Ensure the target directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)
        
        logger.info(f'Saved script to file: {filename}')
        return os.path.abspath(filename)

    def run_code_with_debug(self, code_file: str, original_prompt: str, original_code: str) -> bool:
        """Uruchamia kod i obsługuje ewentualne błędy."""
        try:
            # Run code in a new process
            print("\nRunning generated code...")
            process = subprocess.Popen(
                [sys.executable, code_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for the process to complete with a timeout
            try:
                stdout, stderr = process.communicate(timeout=30)  # 30 seconds timeout
                stdout = stdout.decode('utf-8', errors='ignore')
                stderr = stderr.decode('utf-8', errors='ignore')

                # Check exit code
                if process.returncode != 0:
                    print(f"Code execution failed with error code: {process.returncode}.")
                    if stderr:
                        print(f"Error: {stderr}")

                    # Attempt debugging and code regeneration
                    debugged_code = self.debug_and_regenerate_code(original_prompt, stderr, original_code)

                    if debugged_code:
                        print("\nReceived fixed code:")
                        print("-" * 40)
                        print(debugged_code)
                        print("-" * 40)

                        # Save the fixed code to a file
                        fixed_code_file = self.save_code_to_file(debugged_code, os.path.join(PACKAGE_DIR, "fixed_script.py"))
                        print(f"Fixed code saved to file: {fixed_code_file}")

                        # Ask the user if they want to run the fixed code
                        user_input = input("\nDo you want to run the fixed code? (y/n): ").lower()
                        if user_input.startswith('y'):
                            # Recursive call, but without further debugging in case of subsequent errors
                            print("\nRunning fixed code...")
                            try:
                                subprocess.run([sys.executable, fixed_code_file], check=True)
                            except Exception as run_error:
                                print(f"Error running fixed code: {run_error}")

                    return False

                # If there were no errors
                if stdout:
                    print("Code execution result:")
                    print(stdout)

                print("Code executed successfully!")
                return True

            except subprocess.TimeoutExpired:
                process.kill()
                print("Code execution interrupted - time limit exceeded (30 seconds).")
                return False

        except Exception as e:
            print(f"Error running code: {e}")
            return False

    def debug_and_regenerate_code(self, original_prompt: str, error_message: str, code: str) -> str:
        """Debug errors in the generated code and request a fix."""
        print(f"\nDetected an error in the generated code. Attempting to fix...")

        # Use a template for code debugging
        # Send a debugging query using a special template
        debug_response = self.query_ollama(
            original_prompt,  # Original task
            template_type="debug",  # Use debugging template
            code=code,  # Pass the original code
            error_message=error_message  # Pass the error message
        )

        if not debug_response:
            print("No response received for the debugging query.")
            return ""

        # Extract the fixed code
        debugged_code = self.extract_python_code(debug_response)

        if not debugged_code:
            print("Failed to extract the fixed code.")
            # If code extraction failed, try to use the entire response
            if debug_response and "import" in debug_response:
                # If the response contains an import, it might be code without markers
                return debug_response
            return ""

        return debugged_code
