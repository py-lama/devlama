#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
import questionary
import difflib

# Initialize logging with PyLogs
from devlama.ecosystem.logging_config import init_logging, get_logger

# Initialize logging first, before any other imports
init_logging()

# Get a logger for this module
logger = get_logger('cli')

# Import main functionality
from .devlama import (
    check_ollama,
    save_code_to_file,
    execute_code,
)
from .templates import get_template
from .OllamaRunner import OllamaRunner
# Ensure we can import from bexy and getllm
import os
import sys

# Add parent directory to sys.path to find bexy and getllm packages
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
    parser = argparse.ArgumentParser(description="PyLama - Python Code Generator and Ecosystem Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Code generation command (default)
    code_parser = subparsers.add_parser("code", help="Generate Python code using LLM models")
    code_parser.add_argument(
        "prompt", nargs="+", help="Task to be performed by Python code"
    )
    code_parser.add_argument(
        "-t", "--template",
        choices=["basic", "platform_aware", "dependency_aware", "testable", "secure", "performance", "pep8"],
        default="platform_aware",
        help="Type of template to use",
    )
    code_parser.add_argument(
        "-d", "--dependencies",
        help="List of allowed dependencies (only for template=dependency_aware)",
    )
    code_parser.add_argument(
        "-m", "--model",
        help="Name of the Ollama model to use",
    )
    code_parser.add_argument(
        "-s", "--save",
        action="store_true",
        help="Save the generated code to a file",
    )
    code_parser.add_argument(
        "-r", "--run",
        action="store_true",
        help="Run the generated code after creation",
    )
    code_parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock code generation and execution (for testing)",
    )
    
    # Interactive mode command
    interactive_parser = subparsers.add_parser("interactive", help="Run in interactive mode")
    interactive_parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock code generation and execution (for testing)",
    )
    
    # Ecosystem management commands
    from .ecosystem.cli import main as ecosystem_main
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start the PyLama ecosystem")
    start_parser.add_argument("--docker", action="store_true", help="Use Docker to start the ecosystem")
    start_parser.add_argument("--bexy", action="store_true", help="Start BEXY")
    start_parser.add_argument("--getllm", action="store_true", help="Start PyLLM")
    start_parser.add_argument("--shellama", action="store_true", help="Start SheLLama")
    start_parser.add_argument("--apilama", action="store_true", help="Start APILama")
    start_parser.add_argument("--devlama", action="store_true", help="Start PyLama")
    start_parser.add_argument("--weblama", action="store_true", help="Start WebLama")
    start_parser.add_argument("--open", action="store_true", help="Open WebLama in browser after starting")
    start_parser.add_argument("--browser", action="store_true", help="Alias for --open, opens WebLama in browser")
    start_parser.add_argument("--auto-adjust-ports", action="store_true", help="Automatically adjust ports if they are in use", default=True)
    start_parser.add_argument("--no-auto-adjust-ports", action="store_false", dest="auto_adjust_ports", help="Do not automatically adjust ports if they are in use")
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop the PyLama ecosystem")
    stop_parser.add_argument("--docker", action="store_true", help="Use Docker to stop the ecosystem")
    stop_parser.add_argument("--bexy", action="store_true", help="Stop BEXY")
    stop_parser.add_argument("--getllm", action="store_true", help="Stop PyLLM")
    stop_parser.add_argument("--shellama", action="store_true", help="Stop SheLLama")
    stop_parser.add_argument("--apilama", action="store_true", help="Stop APILama")
    stop_parser.add_argument("--devlama", action="store_true", help="Stop PyLama")
    stop_parser.add_argument("--weblama", action="store_true", help="Stop WebLama")
    
    # Restart command
    restart_parser = subparsers.add_parser("restart", help="Restart the PyLama ecosystem")
    restart_parser.add_argument("--docker", action="store_true", help="Use Docker to restart the ecosystem")
    restart_parser.add_argument("--bexy", action="store_true", help="Restart BEXY")
    restart_parser.add_argument("--getllm", action="store_true", help="Restart PyLLM")
    restart_parser.add_argument("--shellama", action="store_true", help="Restart SheLLama")
    restart_parser.add_argument("--apilama", action="store_true", help="Restart APILama")
    restart_parser.add_argument("--devlama", action="store_true", help="Restart PyLama")
    restart_parser.add_argument("--weblama", action="store_true", help="Restart WebLama")
    
    # Status command
    subparsers.add_parser("status", help="Show the status of the PyLama ecosystem")
    
    # Logs command
    logs_parser = subparsers.add_parser("logs", help="View logs for a service")
    logs_parser.add_argument("service", choices=["bexy", "getllm", "shellama", "apilama", "devlama", "weblama", "all"],
                           help="Service to view logs for (use 'all' to view logs from all services)")
    logs_parser.add_argument("--level", choices=["debug", "info", "warning", "error", "critical"],
                           help="Filter logs by level")
    logs_parser.add_argument("--limit", type=int, default=50,
                           help="Maximum number of logs to display")
    logs_parser.add_argument("--json", action="store_true",
                           help="Output logs in JSON format")
    
    # Open command
    open_parser = subparsers.add_parser("open", help="Open WebLama in a web browser")
    open_parser.add_argument("--port", type=int, help="Custom port to use (default: 9081)")
    open_parser.add_argument("--host", type=str, help="Custom host to use (default: 127.0.0.1)")
    
    # Collect logs command
    collect_parser = subparsers.add_parser("collect-logs", help="Collect logs from services and import them into LogLama")
    collect_parser.add_argument("--services", nargs="+",
                              choices=["bexy", "getllm", "shellama", "apilama", "devlama", "weblama"],
                              help="Services to collect logs from (default: all)")
    collect_parser.add_argument("--verbose", "-v", action="store_true",
                              help="Show verbose output")
    
    # Log collector daemon commands
    collector_parser = subparsers.add_parser("log-collector", help="Manage the log collector daemon")
    collector_subparsers = collector_parser.add_subparsers(dest="collector_command", help="Log collector command")
    
    # Start log collector command
    start_collector_parser = collector_subparsers.add_parser("start", help="Start the log collector daemon")
    start_collector_parser.add_argument("--services", nargs="+",
                                      choices=["bexy", "getllm", "shellama", "apilama", "devlama", "weblama"],
                                      help="Services to collect logs from (default: all)")
    start_collector_parser.add_argument("--interval", "-i", type=int, default=300,
                                      help="Collection interval in seconds (default: 300)")
    start_collector_parser.add_argument("--verbose", "-v", action="store_true",
                                      help="Show verbose output")
    start_collector_parser.add_argument("--foreground", "-f", action="store_true",
                                      help="Run in the foreground instead of as a daemon")
    
    # Stop log collector command
    collector_subparsers.add_parser("stop", help="Stop the log collector daemon")
    
    # Status log collector command
    collector_subparsers.add_parser("status", help="Check the status of the log collector daemon")
    
    # For backwards compatibility, add -i/--interactive flag to the main parser
    parser.add_argument("-i", "--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--mock", action="store_true", help="Use mock code generation and execution (for testing)")
    
    args = parser.parse_args()
    
    logger.info("Application started")
    
    # Handle ecosystem management commands
    if args.command in ["start", "stop", "restart", "status", "logs", "open", "collect-logs", "log-collector"]:
        from .ecosystem import main as ecosystem_main
        # Re-parse the arguments for the ecosystem management command
        sys.argv[0] = "devlama-ecosystem"  # Change the program name for help messages
        return ecosystem_main()
    
    # Handle interactive mode (both with -i flag and with 'interactive' command)
    if args.interactive or args.command == "interactive":
        mock_mode = args.mock
        interactive_mode(mock_mode=mock_mode)
        return 0
    
    # For code generation (default behavior)
    # Check if Ollama is running
    ollama_version = check_ollama()
    if not ollama_version:
        logger.error("Ollama is not running. Please start Ollama with 'ollama serve' and try again.")
        sys.exit(1)
    
    # If no command specified but prompt is provided, assume 'code' command
    if args.command is None:
        if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
            # There's a positional argument that doesn't start with '-', treat it as a prompt
            prompt = " ".join(sys.argv[1:])
            template = "platform_aware"  # Default template
            model = get_default_model()
            save = False
            run = False
            mock_mode = args.mock
        else:
            # No command and no prompt, show help
            parser.print_help()
            return 1
    elif args.command == "code":
        # Code generation command
        prompt = " ".join(args.prompt)
        template = args.template
        model = args.model or get_default_model()
        save = args.save
        run = args.run
        mock_mode = args.mock
    else:
        # Unknown command, show help
        parser.print_help()
        return 1
    
    # Prepare OllamaRunner with mock_mode
    runner = OllamaRunner(model=model, mock_mode=mock_mode)
    
    # Use runner to generate code
    code = runner.query_ollama(prompt, template_type=template)
    print("\nGenerated Python code:")
    print("----------------------------------------")
    print(code)
    print("----------------------------------------")
    
    if save:
        filepath = save_code_to_file(code)
        print(f"\nCode saved to file: {filepath}")
    
    if run:
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
