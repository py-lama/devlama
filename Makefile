# Makefile for PyLama

.PHONY: all setup clean test lint format run help venv

# Default values
PORT ?= 8002
HOST ?= 0.0.0.0

# Default target
all: help

# Create virtual environment if it doesn't exist
venv:
	@test -d venv || python3 -m venv venv

# Setup project
setup: venv
	@echo "Setting up PyLama..."
	@. venv/bin/activate && pip install -e .

# Clean project
clean:
	@echo "Cleaning PyLama..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name *.egg-info -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +

# Run tests
test: setup
	@echo "Testing PyLama..."
	@. venv/bin/activate && python -m unittest discover

# Lint code
lint: setup
	@echo "Linting PyLama..."
	@. venv/bin/activate && flake8 pylama

# Format code
format: setup
	@echo "Formatting PyLama..."
	@. venv/bin/activate && black pylama

# Run the API server
run: setup
	@echo "Running PyLama API server on port $(PORT)..."
	@. venv/bin/activate && uvicorn pylama.api:app --host $(HOST) --port $(PORT)

# Run with custom port (for backward compatibility)
run-port: setup
	@echo "Running PyLama API server on port $(PORT)..."
	@. venv/bin/activate && uvicorn pylama.api:app --host $(HOST) --port $(PORT)

# Help
help:
	@echo "PyLama Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  setup     - Set up the project"
	@echo "  clean     - Clean the project"
	@echo "  test      - Run tests"
	@echo "  lint      - Lint the code"
	@echo "  format    - Format the code with black"
	@echo "  run       - Run the API server"
	@echo "  run-port PORT=8002 - Run the API server on a custom port"
	@echo "  help      - Show this help message"
