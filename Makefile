# Makefile for gh-project-manager-mcp

# Variables
POETRY = poetry
PYTHON = $(POETRY) run python
PYTEST = $(POETRY) run pytest
RUFF_FORMAT = $(POETRY) run ruff format
RUFF_CHECK = $(POETRY) run ruff check
DOCKER_IMAGE_NAME = gh-pm-mcp-server
DOCKER_CONTAINER_NAME = gh-pm-server
APP_PORT = 8191 # Define port variable

# Resolve GH_TOKEN: prioritize Makefile param ($(GH_TOKEN)), fallback to env var ($$GH_TOKEN)
RESOLVED_GH_TOKEN = $(or $(GH_TOKEN),$(shell echo $$GH_TOKEN))

# Default target executed when 'make' is run without arguments
.DEFAULT_GOAL := help

.PHONY: help install format lint test test-cov test-tool test-utils build clean docker-build run-docker stop-docker run-local run start-docker start-local diff-stats integration-test unit-test

help:
	@echo "Available commands:"
	@echo "  install         Install project dependencies using Poetry."
	@echo "  format          Format code using Ruff."
	@echo "  lint            Check code for linting errors using Ruff."
	@echo "  test            Run all tests (unit + integration)."
	@echo "  unit-test       Run only unit tests."
	@echo "  integration-test Run only integration tests (starts MCP server if needed)."
	@echo "  test-cov        Run all tests with coverage reporting."
	@echo "  test-tool       Run tests for a specific tool (e.g., make test-tool tool=issues)."
	@echo "  test-utils      Run tests for the utils module."
	@echo "  test args=\"...\" Run pytest with additional arguments (e.g., make test args=\"-k test_create -v\")."
	@echo "  build           Build the Python package using Poetry."
	@echo "  clean           Remove build artifacts and cache files."
	@echo "  docker-build    Build the Docker image."
	@echo "  run-docker [GH_TOKEN=...] Build Docker image AND run the server container with .env variables on port $(APP_PORT)."
	@echo "  start-docker [GH_TOKEN=...] Run the server using the EXISTING Docker image with .env variables on port $(APP_PORT)."
	@echo "  stop-docker     Stop and remove the running Docker container."
	@echo "  run-local [GH_TOKEN=...] Run the server locally using Poetry on port $(APP_PORT)."
	@echo "  start-local [GH_TOKEN=...] Alias for run-local (starts server locally using Poetry)."
	@echo "  run [GH_TOKEN=...] Alias for run-docker."
	@echo "  diff-stats [ref=...] Show stats for lines added/modified in the current git diff."
	@echo ""
	@echo "Environment Variables:"
	@echo "  - You can create a .env file in the project root to set environment variables."
	@echo "  - The Docker commands (run-docker, start-docker) will automatically load variables from .env if it exists."
	@echo "  - Example .env file content:"
	@echo "    GH_TOKEN=your_github_token"
	@echo "    MCP_SERVER_PORT=8191"
	@echo "    DEFAULT_ISSUE_ASSIGNEE=@me"


install:
	@echo "Installing dependencies..."
	$(POETRY) install --all-extras

format:
	@echo "Formatting code..."
	$(RUFF_FORMAT) .

lint:
	@echo "Checking code style with Ruff..."
	$(RUFF_CHECK) .

test:
	@echo "========================================================="
	@echo "Running all tests (unit tests + integration tests)"
	@echo "========================================================="
	@$(MAKE) unit-test
	@echo "========================================================="
	@echo "Running integration tests"
	@echo "========================================================="
	@$(MAKE) -k integration-test || true
	@echo "========================================================="
	@echo "Test suite complete"
	@echo "========================================================="

test-cov:
	@echo "Running tests with coverage..."
	$(PYTEST) --cov=src --cov-report=term-missing $(args)

# Example: make test-tool tool=issues
test-tool: tool ?= issues # Default to 'issues' if not specified
test-tool:
	@echo "Running tests for tool: $(tool)..."
	$(PYTEST) tests/tools/test_$(tool).py $(args)

test-utils:
	@echo "Running tests for utils..."
	$(PYTEST) tests/utils/ $(args)

build:
	@echo "Building package..."
	$(POETRY) build

clean:
	@echo "Cleaning up..."
	rm -rf dist/ build/ .pytest_cache/ *.egg-info/ .coverage coverage.xml htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build:
	docker build -t $(DOCKER_IMAGE_NAME) .

stop-docker:
	@echo "Stopping and removing Docker container: $(DOCKER_CONTAINER_NAME)..."
	-docker stop $(DOCKER_CONTAINER_NAME) >/dev/null 2>&1 || true
	-docker rm $(DOCKER_CONTAINER_NAME) >/dev/null 2>&1 || true

# Usage: make run-docker [GH_TOKEN=your_token]
run-docker: docker-build stop-docker
ifeq ($(strip $(RESOLVED_GH_TOKEN)),)
	@if [ -f .env ]; then \
		echo "Loading environment variables from .env file..."; \
		docker run -d --name $(DOCKER_CONTAINER_NAME) -p 8191:8191 --env-file .env $(DOCKER_IMAGE_NAME):latest; \
	else \
		echo "No .env file found and no GH_TOKEN provided."; \
		docker run -d --name $(DOCKER_CONTAINER_NAME) -p 8191:8191 $(DOCKER_IMAGE_NAME):latest; \
	fi
else
	@echo "Using provided GH_TOKEN..."
	@if [ -f .env ]; then \
		echo "Loading environment variables from .env file and adding GH_TOKEN..."; \
		docker run -d --name $(DOCKER_CONTAINER_NAME) -p 8191:8191 --env-file .env -e GH_TOKEN="$(RESOLVED_GH_TOKEN)" $(DOCKER_IMAGE_NAME):latest; \
	else \
		docker run -d --name $(DOCKER_CONTAINER_NAME) -p 8191:8191 -e GH_TOKEN="$(RESOLVED_GH_TOKEN)" $(DOCKER_IMAGE_NAME):latest; \
	fi
endif
	@echo "Container $(DOCKER_CONTAINER_NAME) started on port 8191. Use 'make stop-docker' to stop."
	@echo "View container logs with: docker logs $(DOCKER_CONTAINER_NAME) -f"

# Usage: make start-docker [GH_TOKEN=your_token]
# Assumes 'make docker-build' has been run previously.
start-docker: stop-docker
ifeq ($(strip $(RESOLVED_GH_TOKEN)),)
	@if [ -f .env ]; then \
		echo "Loading environment variables from .env file..."; \
		docker run -d --name $(DOCKER_CONTAINER_NAME) -p 8191:8191 --env-file .env $(DOCKER_IMAGE_NAME):latest; \
	else \
		echo "No .env file found and no GH_TOKEN provided."; \
		docker run -d --name $(DOCKER_CONTAINER_NAME) -p 8191:8191 $(DOCKER_IMAGE_NAME):latest; \
	fi
else
	@echo "Using provided GH_TOKEN..."
	@if [ -f .env ]; then \
		echo "Loading environment variables from .env file and adding GH_TOKEN..."; \
		docker run -d --name $(DOCKER_CONTAINER_NAME) -p 8191:8191 --env-file .env -e GH_TOKEN="$(RESOLVED_GH_TOKEN)" $(DOCKER_IMAGE_NAME):latest; \
	else \
		docker run -d --name $(DOCKER_CONTAINER_NAME) -p 8191:8191 -e GH_TOKEN="$(RESOLVED_GH_TOKEN)" $(DOCKER_IMAGE_NAME):latest; \
	fi
endif
	@echo "Container $(DOCKER_CONTAINER_NAME) started on port 8191. Use 'make stop-docker' to stop."
	@echo "View container logs with: docker logs $(DOCKER_CONTAINER_NAME) -f"

# Usage: make run-local [GH_TOKEN=your_token]
run-local:
ifeq ($(strip $(RESOLVED_GH_TOKEN)),)
	$(PYTHON) -m gh_project_manager_mcp.server
else
	@echo "Using provided GH_TOKEN..."
	GH_TOKEN="$(RESOLVED_GH_TOKEN)" $(PYTHON) -m gh_project_manager_mcp.server
endif

# Alias for run-local
start-local: run-local

# Alias for run-docker
run: run-docker

# Run only unit tests
unit-test:
	@echo "Running unit tests..."
	$(PYTEST) tests/unit/ $(args)

# Integration tests - checks server health using Docker container
integration-test:
	@$(MAKE) stop-docker
	@$(MAKE) docker-build
	@if [ -f .env ]; then \
		echo "Loading environment variables from .env file for integration tests..."; \
		docker run -d --name $(DOCKER_CONTAINER_NAME) -p 8191:8191 --env-file .env -e GH_TOKEN="dummy-token-for-tests" $(DOCKER_IMAGE_NAME):latest; \
	else \
		docker run -d --name $(DOCKER_CONTAINER_NAME) -p 8191:8191 -e GH_TOKEN="dummy-token-for-tests" $(DOCKER_IMAGE_NAME):latest; \
	fi
	@echo "Waiting for server to start..."
	@echo "View container logs with: docker logs $(DOCKER_CONTAINER_NAME) -f"
	@for i in $$(seq 1 10); do \
		if curl -s http://localhost:8191/health > /dev/null; then \
			echo "Server started successfully."; \
			break; \
		fi; \
		if [ $$i -eq 10 ]; then \
			echo "Failed to start server after 10 attempts"; \
			$(MAKE) stop-docker; \
			exit 1; \
		fi; \
		sleep 2; \
		echo "Waiting... ($$i/10)"; \
	done
	@$(PYTEST) tests/integration/ $(args) || { echo "Tests failed!"; $(MAKE) stop-docker; exit 1; }
	@$(MAKE) stop-docker
	@echo "Integration tests completed successfully."

# Usage: make diff-stats [ref=branch_or_commit]
# Shows statistics for lines added/modified in the current git diff
# If ref is specified, compares against that reference (branch or commit)
diff-stats:
ifdef ref
	@echo "Comparing against: $(ref)"
	@echo "Summary of changes:"
	@git --no-pager diff $(ref) --stat | grep -v "Bin "
	@echo "\nDetailed line changes:"
	@echo "  File                                                          Additions  Deletions"
	@echo "  ---------------------------------------------                 ---------  ---------"
	@git diff $(ref) --numstat | grep -v "^-" | awk '{sum_add += $$1; sum_del += $$2; printf "  %-60s  %-9s  %-9s\n", $$3, $$1, $$2} END {printf "\n  %-60s  %-9s  %-9s\n", "TOTAL", sum_add, sum_del}'
else
	@echo "Comparing against staged/unstaged changes"
	@echo "Summary of changes:"
	@git --no-pager diff --stat | grep -v "Bin "
	@echo "\nDetailed line changes:"
	@echo "  File                                                          Additions  Deletions"
	@echo "  ---------------------------------------------                 ---------  ---------"
	@git diff --numstat | grep -v "^-" | awk '{sum_add += $$1; sum_del += $$2; printf "  %-60s  %-9s  %-9s\n", $$3, $$1, $$2} END {printf "\n  %-60s  %-9s  %-9s\n", "TOTAL", sum_add, sum_del}'
endif