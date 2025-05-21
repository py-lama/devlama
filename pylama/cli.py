#!/usr/bin/env python3

import argparse
import logging
import sys
from pathlib import Path
import questionary
import difflib

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)7s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Import main functionality
from .pylama import (
    check_ollama,
    save_code_to_file,
    execute_code,
)
from .templates import get_template
from .OllamaRunner import OllamaRunner
# Ensure we can import from pybox and pyllm
import os
import sys

# Add parent directory to sys.path to find pybox and pyllm packages
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Simple implementation of required functionality

# Model management functions
def get_models():
    """Get a list of available models, including Bielik from SpeakLeash."""
    return [
        "llama2",
        "codellama",
        "codellama:13b",
        "codellama:34b",
        "codellama:70b",
        "deepseek-coder:6.7b",
        "deepseek-coder:33b",
        "starcoder2:15b",
        "phi",
        "phi-2",
        "wizardcoder:15b",
        "codegemma:2b",
        "codegemma:7b",
        "codegemma:7b-it",
        # Bielik models from SpeakLeash:
        "SpeakLeash/bielik-7b-instruct-v0.1-gguf",
        "SpeakLeash/bielik-11b-v2.0-instruct-gguf",
        "SpeakLeash/bielik-11b-v2.1-instruct-gguf",
        "SpeakLeash/bielik-11b-v2.2-instruct-gguf",
        "SpeakLeash/bielik-11b-v2.3-instruct-gguf",
        "SpeakLeash/bielik-1.5b-v3.0-instruct-gguf",
        "SpeakLeash/bielik-4.5b-v3.0-instruct-gguf",
    ]

def get_default_model():
    """Get the default model."""
    return "llama2"

def set_default_model(model):
    """Set the default model."""
    pass


def interactive_mode(mock_mode=False):
    """
    Run PyLama in interactive mode, allowing the user to input prompts
    and see the generated code and execution results.
    """
    print("\n=== PyLama Interactive Mode ===\n")
    print("Type 'exit', 'quit', or Ctrl+C to exit.")
    print("Type 'models' to see available models.")
    print("Type 'set model' to change the current model interactively.")
    print("Type 'set model <name>' to change the current model by name.")
    print("Type 'help' for more commands.\n")
    
    model = get_default_model()
    template = "platform_aware"
    
    import builtins
    real_generate_code = generate_code
    real_execute_code = execute_code
    def mock_generate_code(prompt, *args, **kwargs):
        if "hello world" in prompt.lower():
            return "print('Hello, World!')"
        return "# mock code"
    def mock_execute_code(code, *args, **kwargs):
        if "print('Hello, World!')" in code:
            return {"output": "Hello, World!\n", "error": None}
        return {"output": "", "error": None}
    if mock_mode:
        globals()['generate_code'] = mock_generate_code
        globals()['execute_code'] = mock_execute_code
    else:
        globals()['generate_code'] = real_generate_code
        globals()['execute_code'] = real_execute_code
    
    while True:
        try:
            user_input = input("\nud83eudd99 PyLama> ").strip()

            # Known commands for help and fuzzy matching
            known_commands = [
                "exit", "quit", "help", "models", "list", "set model", "set template", "templates"
            ]

            if user_input.lower() in ["exit", "quit"]:
                print("Exiting PyLama. Goodbye!")
                break

            elif user_input.lower() == "help":
                print("\nAvailable commands:")
                print("  exit, quit - Exit PyLama")
                print("  models, list - List available models and select one interactively")
                print("  set model - Select a model interactively")
                print("  set model <name> - Change the current model by name")
                print("  set template <name> - Change the current template")
                print("  templates - List available templates")
                print("  Any other input will be treated as a code generation prompt\n")

            elif user_input.lower() in ["models", "list"]:
                models = get_models()
                print("\nAvailable models:")
                for m in models:
                    star = "*" if m == model else " "
                    print(f"  {star} {m}")
                print(f"\nCurrent model: {model}")
                # Interactive selection
                select = questionary.select("Select a model to use:", choices=models, default=model).ask()
                if select:
                    model = select
                    set_default_model(model)
                    print(f"Model changed to: {model}")

            elif user_input.lower() == "set model":
                models = get_models()
                select = questionary.select("Select a model to use:", choices=models, default=model).ask()
                if select:
                    model = select
                    set_default_model(model)
                    print(f"Model changed to: {model}")

            elif user_input.lower().startswith("set model "):
                new_model = user_input[10:].strip()
                models = get_models()
                if new_model in models:
                    model = new_model
                    set_default_model(model)
                    print(f"Model changed to: {model}")
                else:
                    print(f"Model '{new_model}' not found. Use 'models' to see available models.")

            elif user_input.lower().startswith("set template "):
                new_template = user_input[13:].strip()
                templates = ["basic", "platform_aware", "dependency_aware", "testable", "secure", "performance", "pep8"]
                if new_template in templates:
                    template = new_template
                    print(f"Template changed to: {template}")
                else:
                    print(f"Template '{new_template}' not found. Use 'templates' to see available templates.")

            elif user_input.lower() == "templates":
                print("\nAvailable templates:")
                templates = ["basic", "platform_aware", "dependency_aware", "testable", "secure", "performance", "pep8"]
                for t in templates:
                    star = "*" if t == template else " "
                    print(f"  {star} {t}")
                print(f"\nCurrent template: {template}")

            elif user_input:
                # Check for mistyped command (fuzzy match)
                command_word = user_input.split()[0].lower()
                close_matches = difflib.get_close_matches(command_word, known_commands, n=1, cutoff=0.75)
                if close_matches:
                    print(f"Unrecognized command '{user_input}'. Did you mean '{close_matches[0]}'?")
                else:
                    print(f"Unrecognized command '{user_input}'. Type 'help' to see available commands.")

        except KeyboardInterrupt:
            print("\nExiting PyLama. Goodbye!")
            break
            
        except Exception as e:
            print(f"\nError: {str(e)}")


def main():
    """
    Main entry point for the PyLama CLI.
    """
    parser = argparse.ArgumentParser(description="PyLama - Python Code Generator using LLM models")
    parser.add_argument(
        "prompt", nargs="*", help="Task to be performed by Python code"
    )
    parser.add_argument(
        "-t", "--template",
        choices=["basic", "platform_aware", "dependency_aware", "testable", "secure", "performance", "pep8"],
        default="platform_aware",
        help="Type of template to use",
    )
    parser.add_argument(
        "-d", "--dependencies",
        help="List of allowed dependencies (only for template=dependency_aware)",
    )
    parser.add_argument(
        "-m", "--model",
        help="Name of the Ollama model to use",
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )
    parser.add_argument(
        "-s", "--save",
        action="store_true",
        help="Save the generated code to a file",
    )
    parser.add_argument(
        "-r", "--run",
        action="store_true",
        help="Run the generated code after creation",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock code generation and execution (for testing)",
    )
    
    args = parser.parse_args()
    
    logger.info("Application started")
    
    # Check if Ollama is running
    ollama_version = check_ollama()
    if not ollama_version:
        logger.error("Ollama is not running. Please start Ollama with 'ollama serve' and try again.")
        sys.exit(1)
    
    # Prepare OllamaRunner with mock_mode
    runner = OllamaRunner(model=args.model or get_default_model(), mock_mode=args.mock)
    
    # For interactive mode
    if args.interactive:
        interactive_mode(mock_mode=args.mock)
        return
    
    # Command-line mode
    prompt = " ".join(args.prompt)
    template = args.template
    
    # Use runner to generate code
    code = runner.query_ollama(prompt, template_type=template)
    print("\nGenerated Python code:")
    print("----------------------------------------")
    print(code)
    print("----------------------------------------")
    
    if args.save:
        filepath = save_code_to_file(code)
        print(f"\nCode saved to file: {filepath}")
    
    if args.run:
        result = execute_code(code)
        print("\nCode execution result:")
        print(result.get("output", "No output"))
        if result.get("error"):
            print("\nError occurred:")
            print(result["error"])
        else:
            print("\nCode executed successfully!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
