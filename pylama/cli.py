#!/usr/bin/env python3

import argparse
import logging
import sys
from pathlib import Path

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
    generate_code,
    execute_code,
    save_code_to_file,
)
from .templates import get_template
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


def interactive_mode():
    """
    Run PyLama in interactive mode, allowing the user to input prompts
    and see the generated code and execution results.
    """
    print("\n=== PyLama Interactive Mode ===\n")
    print("Type 'exit', 'quit', or Ctrl+C to exit.")
    print("Type 'models' to see available models.")
    print("Type 'set model <name>' to change the current model.")
    print("Type 'help' for more commands.\n")
    
    model = get_default_model()
    template = "platform_aware"
    
    while True:
        try:
            user_input = input("\nud83eudd99 PyLama> ")
            
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting PyLama. Goodbye!")
                break
                
            elif user_input.lower() == "help":
                print("\nAvailable commands:")
                print("  exit, quit - Exit PyLama")
                print("  models - List available models")
                print("  set model <name> - Change the current model")
                print("  set template <name> - Change the current template")
                print("  templates - List available templates")
                print("  Any other input will be treated as a code generation prompt\n")
                
            elif user_input.lower() == "models":
                models = get_models()
                print("\nAvailable models:")
                for m in models:
                    star = "*" if m == model else " "
                    print(f"  {star} {m}")
                print(f"\nCurrent model: {model}")
                
            elif user_input.lower().startswith("set model "):
                new_model = user_input[10:].strip()
                models = get_models()
                if new_model in models:
                    model = new_model
                    set_default_model(model)
                    print(f"Model changed to: {model}")
                else:
                    print(f"Model '{new_model}' not found. Use 'models' to see available models.")
                    
            elif user_input.lower() == "templates":
                print("\nAvailable templates:")
                templates = ["basic", "platform_aware", "dependency_aware", "testable", "secure", "performance", "pep8"]
                for t in templates:
                    star = "*" if t == template else " "
                    print(f"  {star} {t}")
                print(f"\nCurrent template: {template}")
                
            elif user_input.lower().startswith("set template "):
                new_template = user_input[13:].strip()
                templates = ["basic", "platform_aware", "dependency_aware", "testable", "secure", "performance", "pep8"]
                if new_template in templates:
                    template = new_template
                    print(f"Template changed to: {template}")
                else:
                    print(f"Template '{new_template}' not found. Use 'templates' to see available templates.")
                    
            elif user_input.strip():
                # Treat as a code generation prompt
                print(f"\nGenerating code using model: {model}, template: {template}...")
                code = generate_code(user_input, template_type=template, model=model)
                print("\nGenerated code:")
                print("----------------------------------------")
                print(code)
                print("----------------------------------------")
                
                save = input("\nSave code to file? (y/n): ").lower()
                if save == "y":
                    filepath = save_code_to_file(code)
                    print(f"\nCode saved to file: {filepath}")
                
                run = input("\nRun the generated code? (y/n): ").lower()
                if run == "y":
                    print("\nRunning generated code...")
                    result = execute_code(code)
                    print("\nCode execution result:")
                    print(result.get("output", "No output"))
                    
                    if result.get("error"):
                        print("\nError occurred:")
                        print(result["error"])
                    else:
                        print("\nCode executed successfully!")
                        
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
    
    args = parser.parse_args()
    
    logger.info("Application started")
    
    # Check if Ollama is running
    ollama_version = check_ollama()
    if not ollama_version:
        logger.error("Ollama is not running. Please start Ollama with 'ollama serve' and try again.")
        sys.exit(1)
    
    # Interactive mode
    if args.interactive:
        interactive_mode()
        return
    
    # Command-line mode
    if not args.prompt:
        parser.print_help()
        return
    
    prompt = " ".join(args.prompt)
    model = args.model or get_default_model()
    
    # Generate code
    code = generate_code(prompt, template_type=args.template, model=model)
    
    print("\nGenerated Python code:")
    print("----------------------------------------")
    print(code)
    print("----------------------------------------")
    
    # Save code to file if requested
    if args.save:
        filepath = save_code_to_file(code)
        print(f"\nCode saved to file: {filepath}")
    
    # Run code if requested
    if args.run:
        print("\nRunning generated code...")
        result = execute_code(code)
        print("\nCode execution result:")
        print(result.get("output", "No output"))
        
        if result.get("error"):
            print("\nError occurred:")
            print(result["error"])
            return 1
        else:
            print("\nCode executed successfully!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
