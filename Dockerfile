FROM python:3.11-slim

WORKDIR /app

# Define GH CLI version and architecture
ARG GH_VERSION=2.53.0
ARG TARGETARCH=arm64

# Install OS dependencies and GitHub CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN wget https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_${TARGETARCH}.deb -O gh_cli.deb \
    && apt-get update && apt-get install -y --no-install-recommends ./gh_cli.deb \
    && rm gh_cli.deb \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.8.3

# Add Poetry's install location to PATH
ENV PATH="/root/.local/bin:${PATH}"

# DO NOT configure global install - let Poetry create a venv

# Copy dependency definitions FIRST to leverage Docker cache
COPY pyproject.toml poetry.lock ./

# Install project dependencies using Poetry (into venv)
# Using --no-dev to install only production dependencies
# Using --no-interaction --no-ansi for non-interactive environments
RUN poetry install --no-interaction --no-ansi --no-dev

# Copy the rest of the application source code
COPY src/gh_project_manager_mcp ./gh_project_manager_mcp

# Expose the application port
EXPOSE 8191

# Define the command to run the application using python -m
# Ensures the package is run correctly
CMD ["python", "-m", "gh_project_manager_mcp.server"]