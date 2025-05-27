# Makefile for DevLama

.PHONY: all setup clean test lint format run help venv docker-test docker-build docker-clean docker-integration docker-full-stack docker-ansible test-package update-version publish publish-test

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
	@echo "Setting up DevLama..."
	@. venv/bin/activate && pip install -e .

# Clean project
clean:
	@echo "Cleaning DevLama..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name *.egg-info -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +

# Run tests
test: setup
	@echo "Testing DevLama..."
	@. venv/bin/activate && python -m unittest discover

# Lint code
lint: setup
	@echo "Linting DevLama..."
	@. venv/bin/activate && flake8 devlama

# Format code
format: setup
	@echo "Formatting DevLama..."
	@. venv/bin/activate && black devlama

# Run the API server
run: setup
	@echo "Running DevLama API server on port $(PORT)..."
	@. venv/bin/activate && uvicorn devlama.api:app --host $(HOST) --port $(PORT)

# Run with custom port (for backward compatibility)
run-port: setup
	@echo "Running DevLama API server on port $(PORT)..."
	@. venv/bin/activate && uvicorn devlama.api:app --host $(HOST) --port $(PORT)

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
	@echo "Starting full DevLama ecosystem in Docker..."
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


# Build package
build: setup
	@echo "Building package..."
	@. venv/bin/activate && pip install -e . && pip install wheel twine build
	@. venv/bin/activate && rm -rf dist/* && python setup.py sdist bdist_wheel

# Update version
update-version:
	@echo "Updating package version..."
	@python ../scripts/update_version.py

# Publish package to PyPI
publish: build update-version
	@echo "Publishing package to PyPI..."
	@. venv/bin/activate && twine check dist/* && twine upload dist/*

# Publish package to TestPyPI
publish-test: build update-version
	@echo "Publishing package to TestPyPI..."
	@. venv/bin/activate && twine check dist/* && twine upload --repository testpypi dist/*
