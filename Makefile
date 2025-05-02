# Makefile for gh-project-manager-mcp

# Variables
POETRY = poetry
PYTHON = $(POETRY) run python
PYTEST = $(POETRY) run pytest
BLACK = $(POETRY) run black
DOCKER_IMAGE_NAME = gh-pm-mcp-server
DOCKER_CONTAINER_NAME = gh-pm-server
APP_PORT = 8191 # Define port variable

# Resolve GH_TOKEN: prioritize Makefile param ($(GH_TOKEN)), fallback to env var ($$GH_TOKEN)
RESOLVED_GH_TOKEN = $(or $(GH_TOKEN),$(shell echo $$GH_TOKEN))

# Default target executed when 'make' is run without arguments
.DEFAULT_GOAL := help

.PHONY: help install format test test-cov test-tool test-utils build clean docker-build run-docker stop-docker run-local run start-docker start-local

help:
	@echo "Available commands:"
	@echo "  install         Install project dependencies using Poetry."
	@echo "  format          Format code using black."
	@echo "  test            Run all tests using pytest."
	@echo "  test-cov        Run all tests with coverage reporting."
	@echo "  test-tool       Run tests for a specific tool (e.g., make test-tool tool=issues)."
	@echo "  test-utils      Run tests for the utils module."
	@echo "  test args=\"...\" Run pytest with additional arguments (e.g., make test args=\"-k test_create -v\")."
	@echo "  build           Build the Python package using Poetry."
	@echo "  clean           Remove build artifacts and cache files."
	@echo "  docker-build    Build the Docker image."
	@echo "  run-docker [GH_TOKEN=...] Build Docker image AND run the server container on port $(APP_PORT)."
	@echo "  start-docker [GH_TOKEN=...] Run the server using the EXISTING Docker image on port $(APP_PORT)."
	@echo "  stop-docker     Stop and remove the running Docker container."
	@echo "  run-local [GH_TOKEN=...] Run the server locally using Poetry on port $(APP_PORT)."
	@echo "  start-local [GH_TOKEN=...] Alias for run-local (starts server locally using Poetry)."
	@echo "  run [GH_TOKEN=...] Alias for run-docker."


install:
	@echo "--> Installing dependencies..."
	$(POETRY) install --all-extras

format:
	@echo "--> Formatting code..."
	$(BLACK) .

test:
	@echo "--> Running all tests..."
	$(PYTEST) $(args)

test-cov:
	@echo "--> Running tests with coverage..."
	$(PYTEST) --cov=src --cov-report=term-missing $(args)

# Example: make test-tool tool=issues
test-tool: tool ?= issues # Default to 'issues' if not specified
test-tool:
	@echo "--> Running tests for tool: $(tool)..."
	$(PYTEST) tests/tools/test_$(tool).py $(args)

test-utils:
	@echo "--> Running tests for utils..."
	$(PYTEST) tests/utils/ $(args)

build:
	@echo "--> Building package..."
	$(POETRY) build

clean:
	@echo "--> Cleaning up..."
	rm -rf dist/ build/ .pytest_cache/ *.egg-info/ .coverage coverage.xml htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build:
	@echo "--> Building Docker image: $(DOCKER_IMAGE_NAME)..."
	docker build -t $(DOCKER_IMAGE_NAME) .

stop-docker:
	@echo "--> Stopping and removing Docker container: $(DOCKER_CONTAINER_NAME)..."
	-docker stop $(DOCKER_CONTAINER_NAME) >/dev/null 2>&1 || true
	-docker rm $(DOCKER_CONTAINER_NAME) >/dev/null 2>&1 || true

# Usage: make run-docker [GH_TOKEN=your_token]
run-docker: docker-build stop-docker
	@echo "--> Checking GH_TOKEN..."
ifeq ($(strip $(RESOLVED_GH_TOKEN)),)
	$(error ERROR: GH_TOKEN is not set via Makefile parameter or environment variable. Please set it.)
else
	@echo "Using resolved GH_TOKEN."
endif
	@echo "--> Starting server in Docker container (foreground): $(DOCKER_CONTAINER_NAME) on port $(APP_PORT)..."
	docker run --name $(DOCKER_CONTAINER_NAME) -p 8191:8191 -e GH_TOKEN="$(RESOLVED_GH_TOKEN)" $(DOCKER_IMAGE_NAME):latest
	@echo "Container $(DOCKER_CONTAINER_NAME) started. Use 'make stop-docker' to stop."
	@echo "View logs with: docker logs $(DOCKER_CONTAINER_NAME)"

# Usage: make start-docker [GH_TOKEN=your_token]
# Assumes 'make docker-build' has been run previously.
start-docker: stop-docker
	@echo "--> Checking GH_TOKEN..."
ifeq ($(strip $(RESOLVED_GH_TOKEN)),)
	$(error ERROR: GH_TOKEN is not set via Makefile parameter or environment variable. Please set it.)
else
	@echo "Using resolved GH_TOKEN."
endif
	@echo "--> Starting server in Docker container (foreground): $(DOCKER_CONTAINER_NAME) on port $(APP_PORT)..."
	docker run --name $(DOCKER_CONTAINER_NAME) -p 8191:8191 -e GH_TOKEN="$(RESOLVED_GH_TOKEN)" $(DOCKER_IMAGE_NAME):latest
	@echo "Container $(DOCKER_CONTAINER_NAME) started. Use 'make stop-docker' to stop."
	@echo "View logs with: docker logs $(DOCKER_CONTAINER_NAME)"

# Usage: make run-local [GH_TOKEN=your_token]
run-local:
	@echo "--> Checking GH_TOKEN..."
ifeq ($(strip $(RESOLVED_GH_TOKEN)),)
	$(error ERROR: GH_TOKEN is not set via Makefile parameter or environment variable. Please set it.)
else
	@echo "Using resolved GH_TOKEN."
endif
	@echo "--> Running server locally..."
	GH_TOKEN="$(RESOLVED_GH_TOKEN)" $(POETRY) run gh-pm-mcp-server