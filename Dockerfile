FROM python:3.11-slim AS builder

WORKDIR /app

# Define GH CLI version
ARG GH_VERSION=2.53.0
# Let Docker automatically determine the target architecture
ARG TARGETARCH

# Install dependencies in a single layer to reduce image size
# Install Poetry and configure it not to create virtualenvs
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install poetry==1.8.3 \
    && poetry config virtualenvs.create false

# Copy dependency definitions to leverage Docker cache
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry lock && poetry install --no-interaction --no-ansi --only main \
    && pip install "result>=0.17.0,<0.18.0" python-dotenv

# Copy the application source code
COPY src/gh_project_manager_mcp ./gh_project_manager_mcp

# Final image
FROM python:3.11-slim

# Add metadata through labels
LABEL org.opencontainers.image.title="GitHub Project Manager MCP"
LABEL org.opencontainers.image.description="An MCP server for GitHub project management"
LABEL org.opencontainers.image.authors="Mário Alvial <mse.alvial@gmail.com>"
LABEL org.opencontainers.image.source="https://github.com/yourusername/gh-project-manager-mcp"
LABEL org.opencontainers.image.version="0.1.0"

WORKDIR /app

# Define GH CLI version
ARG GH_VERSION=2.53.0
# Let Docker automatically determine the target architecture
ARG TARGETARCH

# Install GitHub CLI and runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    ca-certificates \
    && wget https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_${TARGETARCH}.deb -O gh_cli.deb \
    && apt-get install -y --no-install-recommends ./gh_cli.deb \
    && rm gh_cli.deb \
    && rm -rf /var/lib/apt/lists/* \
    && pip install "result>=0.17.0,<0.18.0" python-dotenv

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder /app/gh_project_manager_mcp /app/gh_project_manager_mcp

# Expose the application port
EXPOSE 8191

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Define the command to run the application
CMD ["python", "-m", "gh_project_manager_mcp", "stdio"]