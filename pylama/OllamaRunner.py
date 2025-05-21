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
import threading

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


class ProgressSpinner:
    """A simple progress spinner for console output."""
    def __init__(self, message="Processing", delay=0.1):
        self.message = message
        self.delay = delay
        self.running = False
        self.spinner_thread = None
        self.spinner_chars = ['-', '\\', '|', '/']
        self.counter = 0
        self.start_time = 0
        
    def spin(self):
        while self.running:
            elapsed = time.time() - self.start_time
            sys.stderr.write(f"\r{self.message} {self.spinner_chars[self.counter % len(self.spinner_chars)]} ({elapsed:.1f}s) ")
            sys.stderr.flush()
            time.sleep(self.delay)
            self.counter += 1
        # Clear the line when done
        sys.stderr.write("\r" + " " * (len(self.message) + 20) + "\r")
        sys.stderr.flush()
            
    def start(self):
        self.running = True
        self.start_time = time.time()
        self.spinner_thread = threading.Thread(target=self.spin)
        self.spinner_thread.daemon = True
        self.spinner_thread.start()
        
    def stop(self):
        self.running = False
        if self.spinner_thread:
            self.spinner_thread.join(timeout=1.0)


class OllamaRunner:
    """Class for running Ollama and executing generated code."""

    def __init__(self, ollama_path: str = None, model: str = None, mock_mode: bool = False):
        self.ollama_path = ollama_path or os.getenv('OLLAMA_PATH', 'ollama')
        # Set default model with fallbacks to ensure we use an available model
        self.model = model or os.getenv('OLLAMA_MODEL', 'codellama:7b')
        self.fallback_models = os.getenv('OLLAMA_FALLBACK_MODELS', 'codellama:7b,phi3:latest,tinyllama:latest').split(',')
        self.ollama_process = None
        self.mock_mode = mock_mode
        # Update to the correct Ollama API endpoints for v0.7.0
        self.base_api_url = "http://localhost:11434/api"
        self.generate_api_url = f"{self.base_api_url}/generate"
        self.chat_api_url = f"{self.base_api_url}/chat"
        self.version_api_url = f"{self.base_api_url}/version"
        self.list_api_url = f"{self.base_api_url}/tags"
        # Track the last error that occurred
        self.last_error = None
        # Docker configuration
        self.use_docker = USE_DOCKER
        self.docker_sandbox = None
        if self.use_docker:
            self.docker_sandbox = DockerSandbox()
            logger.info("Using Docker mode for Ollama.")
        self.original_model_specified = model is not None

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

    def check_model_availability(self) -> bool:
        """
        Check if the selected model is available in Ollama.
        Returns True if the model is available, False otherwise.
        If the model is not available but auto-install is enabled, attempts to install it.
        """
        try:
            # Get list of available models from Ollama
            response = requests.get(self.list_api_url, timeout=10)
            response.raise_for_status()
            available_models = [tag['name'] for tag in response.json().get('models', [])]
            
            # If the model is available, return True
            if self.model in available_models:
                return True
                
            # Log available models for debugging
            logger.warning(f"Model {self.model} not found in Ollama. Available models: {available_models}")
            
            # If user explicitly specified a model and it's not available, try to install it
            if self.original_model_specified:
                # Check if we should try to automatically install the model
                auto_install = os.getenv('OLLAMA_AUTO_INSTALL_MODEL', 'True').lower() in ('true', '1', 't')
                if auto_install:
                    print(f"\nModel {self.model} not found. Attempting to install it...")
                    if self.install_model(self.model):
                        return True
                
                # Check if we should try to automatically use an available model
                if os.getenv('OLLAMA_AUTO_SELECT_MODEL', 'True').lower() in ('true', '1', 't'):
                    # Try to find a suitable model from the available ones
                    for model in available_models:
                        if 'code' in model.lower() or 'llama' in model.lower() or 'phi' in model.lower():
                            logger.info(f"Automatically selecting available model: {model} instead of {self.model}")
                            self.model = model
                            return True
                    # If no suitable model found, use the first available one
                    if available_models:
                        logger.info(f"Automatically selecting first available model: {available_models[0]} instead of {self.model}")
                        self.model = available_models[0]
                        return True
                else:
                    # Don't use fallbacks if user explicitly specified a model
                    return False
            
            # Try fallback models
            for fallback in self.fallback_models:
                if fallback in available_models:
                    self.model = fallback
                    logger.info(f"Using fallback model: {fallback}")
                    return True
                    
            # If no fallbacks are available, return False
            return False
        except Exception as e:
            logger.warning(f"Could not check model availability: {e}")
            return False  # Assume model is not available if we can't check

    def install_model(self, model_name: str) -> bool:
        """
        Install a model using Ollama's pull command.
        For SpeakLeash models, performs a special installation process.
        
        Args:
            model_name: The name of the model to install
            
        Returns:
            True if installation was successful, False otherwise
        """
        # Check if it's a SpeakLeash model that needs special handling
        if model_name.lower().startswith('speakleash/bielik'):
            print(f"\nDetected SpeakLeash Bielik model: {model_name}")
            print("Starting special installation process...")
            return self._install_speakleash_model(model_name)
        
        # For regular models, use ollama pull
        print(f"\nInstalling model: {model_name}")
        spinner = ProgressSpinner(message=f"Pulling model {model_name}")
        spinner.start()
        
        try:
            # Run ollama pull command
            result = subprocess.run(
                [self.ollama_path, "pull", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            spinner.stop()
            
            if result.returncode == 0:
                print(f"Successfully installed model: {model_name}")
                # Update the current model
                self.model = model_name
                return True
            else:
                print(f"Failed to install model: {model_name}")
                print(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            spinner.stop()
            print(f"Error installing model: {e}")
            return False
    
    def _install_speakleash_model(self, model_name: str) -> bool:
        """
        Special installation process for SpeakLeash Bielik models.
        
        Args:
            model_name: The name of the SpeakLeash model to install
            
        Returns:
            True if installation was successful, False otherwise
        """
        # Extract the model version from the name
        model_parts = model_name.split('/')
        if len(model_parts) != 2:
            print(f"Invalid model name format: {model_name}")
            return False
            
        model_version = model_parts[1].lower()
        
        # Set up custom model name for Ollama
        custom_model_name = f"bielik-custom-{int(time.time())}"  # Add timestamp to avoid conflicts
        
        # Determine the correct Hugging Face model path and file
        if "1.5b-v3.0" in model_version:
            hf_repo = "speakleash/Bielik-1.5B-v3.0-Instruct-GGUF"
            model_file = "Bielik-1.5B-v3.0-Instruct.Q8_0.gguf"
        elif "4.5b-v3.0" in model_version:
            hf_repo = "speakleash/Bielik-4.5B-v3.0-Instruct-GGUF"
            model_file = "Bielik-4.5B-v3.0-Instruct.Q8_0.gguf"
        elif "11b-v2.3" in model_version:
            hf_repo = "speakleash/Bielik-11B-v2.3-Instruct-GGUF"
            model_file = "Bielik-11B-v2.3-Instruct.Q8_0.gguf"
        else:
            print(f"Unsupported Bielik model version: {model_version}")
            print("Supported versions: 1.5b-v3.0, 4.5b-v3.0, 11b-v2.3")
            return False
        
        # Create a temporary directory for the model
        temp_dir = os.path.join(PACKAGE_DIR, "models", custom_model_name)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Download the model using Hugging Face CLI if available, otherwise use wget
        print(f"\nDownloading {model_name} from Hugging Face...")
        print(f"This may take a while depending on your internet connection.")
        
        model_path = os.path.join(temp_dir, model_file)
        download_url = f"https://huggingface.co/{hf_repo}/resolve/main/{model_file}"
        
        try:
            # First try using huggingface_hub if installed
            try:
                from huggingface_hub import hf_hub_download
                print("Using Hugging Face Hub for download (shows progress)")
                
                hf_hub_download(
                    repo_id=hf_repo,
                    filename=model_file,
                    local_dir=temp_dir,
                    local_dir_use_symlinks=False
                )
                
                if not os.path.exists(model_path):
                    raise FileNotFoundError(f"Downloaded file not found at {model_path}")
                    
            except ImportError:
                # Fall back to wget if huggingface_hub is not installed
                print("Hugging Face Hub not available, using wget for download")
                spinner = ProgressSpinner(message=f"Downloading {model_file}")
                spinner.start()
                
                result = subprocess.run(
                    ["wget", "-O", model_path, download_url],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
                
                spinner.stop()
                
                if result.returncode != 0 or not os.path.exists(model_path):
                    print(f"Download failed: {result.stderr}")
                    return False
            
            # Create a Modelfile
            modelfile_path = os.path.join(temp_dir, "Modelfile")
            with open(modelfile_path, "w") as f:
                f.write(f"FROM {model_file}\n")
                f.write("PARAMETER num_ctx 4096\n")
                f.write('SYSTEM """\nPoland-optimized NLU model with constitutional AI constraints\n"""\n')
            
            # Create the model in Ollama
            print(f"\nCreating Ollama model: {custom_model_name}")
            spinner = ProgressSpinner(message=f"Creating model in Ollama")
            spinner.start()
            
            result = subprocess.run(
                [self.ollama_path, "create", custom_model_name, "-f", modelfile_path],
                cwd=temp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            spinner.stop()
            
            if result.returncode == 0:
                print(f"\nSuccessfully created model: {custom_model_name}")
                print(f"Original model name: {model_name}")
                print(f"\nYou can now use this model with: --model {custom_model_name}")
                
                # Update environment variables for future use
                os.environ["OLLAMA_MODEL"] = custom_model_name
                
                # Update fallback models to include this model
                fallback_models = os.environ.get("OLLAMA_FALLBACK_MODELS", "")
                if fallback_models:
                    os.environ["OLLAMA_FALLBACK_MODELS"] = f"{custom_model_name},{fallback_models}"
                else:
                    os.environ["OLLAMA_FALLBACK_MODELS"] = custom_model_name
                
                # Enable auto-select model
                os.environ["OLLAMA_AUTO_SELECT_MODEL"] = "true"
                
                # Update the current model
                self.model = custom_model_name
                
                # Save these settings to .env file if it exists
                self._update_env_file(custom_model_name)
                
                return True
            else:
                print(f"Failed to create model: {custom_model_name}")
                print(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error during model installation: {e}")
            return False
    
    def _update_env_file(self, model_name: str) -> None:
        """
        Update the .env file with the new model settings.
        
        Args:
            model_name: The name of the model to set as default
        """
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        
        # Check if .env file exists
        if not os.path.exists(env_file):
            try:
                # Create a new .env file
                with open(env_file, "w") as f:
                    f.write(f"OLLAMA_MODEL={model_name}\n")
                    f.write(f"OLLAMA_FALLBACK_MODELS={model_name},codellama:7b,phi:latest\n")
                    f.write("OLLAMA_AUTO_SELECT_MODEL=true\n")
                    f.write("OLLAMA_TIMEOUT=60\n")
                print(f"Created .env file with model settings: {env_file}")
            except Exception as e:
                print(f"Error creating .env file: {e}")
            return
        
        try:
            # Read existing .env file
            with open(env_file, "r") as f:
                lines = f.readlines()
            
            # Update or add model settings
            model_line_found = False
            fallback_line_found = False
            auto_select_line_found = False
            timeout_line_found = False
            
            for i, line in enumerate(lines):
                if line.startswith("OLLAMA_MODEL="):
                    lines[i] = f"OLLAMA_MODEL={model_name}\n"
                    model_line_found = True
                elif line.startswith("OLLAMA_FALLBACK_MODELS="):
                    # Add the new model to fallback models if not already there
                    fallback_models = line.split("=")[1].strip()
                    if model_name not in fallback_models:
                        lines[i] = f"OLLAMA_FALLBACK_MODELS={model_name},{fallback_models}\n"
                    fallback_line_found = True
                elif line.startswith("OLLAMA_AUTO_SELECT_MODEL="):
                    lines[i] = "OLLAMA_AUTO_SELECT_MODEL=true\n"
                    auto_select_line_found = True
                elif line.startswith("OLLAMA_TIMEOUT="):
                    # Only update timeout if it's less than 60
                    timeout_value = line.split("=")[1].strip()
                    try:
                        if int(timeout_value) < 60:
                            lines[i] = "OLLAMA_TIMEOUT=60\n"
                    except ValueError:
                        lines[i] = "OLLAMA_TIMEOUT=60\n"
                    timeout_line_found = True
            
            # Add missing settings
            if not model_line_found:
                lines.append(f"OLLAMA_MODEL={model_name}\n")
            if not fallback_line_found:
                lines.append(f"OLLAMA_FALLBACK_MODELS={model_name},codellama:7b,phi:latest\n")
            if not auto_select_line_found:
                lines.append("OLLAMA_AUTO_SELECT_MODEL=true\n")
            if not timeout_line_found:
                lines.append("OLLAMA_TIMEOUT=60\n")
            
            # Write updated .env file
            with open(env_file, "w") as f:
                f.writelines(lines)
                
            print(f"Updated .env file with model settings: {env_file}")
            
        except Exception as e:
            print(f"Error updating .env file: {e}")

    def query_ollama(self, prompt: str, template_type: str = None, **template_args) -> str:
        """
        Send a query to the Ollama API and return the response.
        Uses mock implementation if self.mock_mode is True.
        """
        # Add default template parameters if not provided
        default_params = {
            'platform': platform.system(),
            'os': platform.system(),
            'dependencies': 'any standard Python library',
            'python_version': platform.python_version()
        }
        
        # Update template_args with defaults for any missing keys
        for key, value in default_params.items():
            if key not in template_args:
                template_args[key] = value
                
        if self.mock_mode:
            logger.info("Using mock code generation (Ollama not required)")
            # If a template type is provided, use it to format the query
            if template_type:
                formatted_prompt = get_template(prompt, template_type, **template_args)
                logger.debug(f"Used template {template_type} for the query")
            else:
                formatted_prompt = prompt
            task = formatted_prompt.lower()
            if "web server" in task:
                return self._load_example_from_file('web_server.py')
            elif "file" in task and ("read" in task or "write" in task):
                return self._load_example_from_file('file_io.py')
            elif "api" in task or "request" in task:
                return self._load_example_from_file('api_request.py')
            elif "database" in task or "sql" in task:
                return self._load_example_from_file('database.py')
            else:
                return self._load_example_from_file('default.py', prompt=formatted_prompt)
        
        # Check if the model is available
        if not self.check_model_availability():
            return f"# Error: Model '{self.model}' not found in Ollama.\n\n# Please ensure:\n# 1. Ollama is running (ollama serve)\n# 2. The model is available (ollama pull {self.model})\n# 3. Or use one of the available models"
        
        # Format the prompt if needed
        if template_type:
            formatted_prompt = get_template(prompt, template_type, **template_args)
            logger.debug(f"Used template {template_type} for the query")
        else:
            formatted_prompt = prompt
            
        # Start a progress spinner
        spinner = ProgressSpinner(message=f"Generating code with {self.model}")
        spinner.start()
        
        try:
            # First try the chat API
            response_text = self.try_chat_api(formatted_prompt)
            if response_text:
                spinner.stop()
                return self.extract_python_code(response_text)
            
            # If chat API fails, try the generate API
            logger.warning(f"Chat API failed: {self.last_error}, trying generate API...")
            
            # Prepare the API request payload
            payload = {
                "model": self.model,
                "prompt": formatted_prompt,
                "stream": False
            }
            
            # Send the API request
            response = requests.post(self.generate_api_url, json=payload, timeout=30)
            response.raise_for_status()
            response_json = response.json()
            
            # Extract the response text
            response_text = response_json.get("response", "")
            spinner.stop()
            return self.extract_python_code(response_text)
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Both API endpoints failed. Error: {e}")
            spinner.stop()
            return f"# Error querying Ollama API: {e}\n\n# Please ensure:\n# 1. Ollama is running (ollama serve)\n# 2. The model '{self.model}' is available (ollama pull {self.model})\n# 3. The Ollama API is accessible at {self.base_api_url}"
        
    def try_chat_api(self, formatted_prompt):
        """Try using the chat API as an alternative."""
        try:
            chat_data = {
                "model": self.model,
                "messages": [{"role": "user", "content": formatted_prompt}],
                "stream": False
            }
            logger.debug(f"Sending chat request to {self.chat_api_url} with model {self.model}")
            chat_response = requests.post(self.chat_api_url, json=chat_data, timeout=30)  # Reduced timeout
            chat_response.raise_for_status()
            chat_json = chat_response.json()
            
            # Extract response from chat API
            if "message" in chat_json and "content" in chat_json["message"]:
                return chat_json["message"]["content"]
            elif "response" in chat_json:
                return chat_json["response"]
            else:
                logger.warning(f"Unexpected chat API response format: {chat_json}")
                return None
        except Exception as e:
            self.last_error = str(e)
            return None

    def extract_python_code(self, text: str) -> str:
        """Extract Python code from the response."""
        # If the response already looks like code (no markdown), return it
        if text.strip().startswith("import ") or text.strip().startswith("#") or text.strip().startswith("def ") or text.strip().startswith("class "):
            return text
            
        # Look for Python code blocks in markdown
        import re
        code_block_pattern = r"```(?:python)?\s*([\s\S]*?)```"
        matches = re.findall(code_block_pattern, text)
        
        if matches:
            # Return the first code block found
            return matches[0].strip()
        
        # If no code blocks found, return the original text
        return text

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
