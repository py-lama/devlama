# Makefile for PyLama

.PHONY: all setup clean test lint format run help venv docker-test docker-build docker-clean docker-integration docker-full-stack docker-ansible

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

# Docker testing targets
docker-build:
	@echo "Building Docker test images..."
	@./run_docker_tests.sh --build

docker-test: docker-build
	@echo "Running tests in Docker..."
	@./run_docker_tests.sh --run-tests

docker-integration: docker-build
	@echo "Running integration tests in Docker..."
	@./run_docker_tests.sh --integration

docker-full-stack: docker-build
	@echo "Starting full PyLama ecosystem in Docker..."
	@./run_docker_tests.sh --full-stack

docker-ansible: docker-build
	@echo "Running Ansible tests in Docker..."
	@./run_docker_tests.sh --ansible-tests

docker-interactive: docker-build
	@echo "Starting interactive Docker test environment..."
	@./run_docker_tests.sh --interactive

docker-clean:
	@echo "Cleaning Docker test environment..."
	@./run_docker_tests.sh --clean

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
	@echo "  docker-build      - Build Docker test images"
	@echo "  docker-test       - Run tests in Docker"
	@echo "  docker-integration - Run integration tests in Docker"
	@echo "  docker-full-stack  - Start full PyLama ecosystem in Docker"
	@echo "  docker-ansible     - Run Ansible tests in Docker"
	@echo "  docker-interactive - Start interactive Docker test environment"
	@echo "  docker-clean      - Clean Docker test environment"
	@echo "  help      - Show this help message"
