# Installation Guide for GitHub Project Manager MCP

This guide will help you set up and run the GitHub Project Manager MCP server, which acts as a wrapper around the GitHub CLI (`gh`) to provide tools for managing GitHub resources through the Model Context Protocol (MCP).

## Requirements

- Python 3.11 or higher
- [GitHub CLI](https://cli.github.com/) (gh) installed and authenticated
- Poetry (recommended) or pip for package management
- Git (for development installation)

## Installation Methods

### Option 1: Install from PyPI (Recommended for Users)

```bash
pip install gh-project-manager-mcp
```

### Option 2: Install from Git (For Development)

```bash
git clone https://github.com/marioalvial/gh-project-manager-mcp.git
cd gh-project-manager-mcp
poetry install
```

### Option 3: Install Using Docker

The project includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t gh-project-manager-mcp .

# Run the container
docker run -p 8080:8080 -e GH_TOKEN=your_github_token gh-project-manager-mcp
```

## Authentication

The server requires GitHub authentication to function. There are two ways to authenticate:

### Method 1: GitHub CLI Authentication

If you're running the server locally or in an environment where GitHub CLI is installed:

```bash
gh auth login
```

Follow the prompts to authenticate with GitHub. The MCP server will use these credentials.

### Method 2: GitHub Token

Set the `GH_TOKEN` environment variable with a GitHub Personal Access Token:

```bash
export GH_TOKEN=your_github_token
```

For Docker, pass the token when running the container:

```bash
docker run -p 8080:8080 -e GH_TOKEN=your_github_token gh-project-manager-mcp
```

## Configuration

The server can be configured with various environment variables as detailed in the [README.md](README.md#configuration).

## Running the Server

After installation, you can run the server using:

```bash
# If installed via pip or Poetry
gh-pm-mcp-server

# Or if in development mode
poetry run python -m gh_project_manager_mcp.server
```

The server will start and listen for incoming MCP connections on port 8080 by default.

## Testing Your Installation

You can verify your installation is working correctly by:

1. Ensuring the server starts without errors
2. Checking that the MCP endpoints are accessible
3. Confirming GitHub CLI commands can be executed through the MCP interface

## Troubleshooting

Common issues and their solutions:

### Authentication Problems

- Verify your GitHub CLI is authenticated with `gh auth status`
- Check your GH_TOKEN environment variable is correctly set
- Ensure your token has the required scopes (repo, project, etc.)

### Connection Issues

- Confirm the server is running on the expected port
- Check for firewall rules that might be blocking access
- Verify your MCP client is configured to connect to the correct endpoint

### Command Execution Failures

- Ensure GitHub CLI is installed and in your PATH
- Verify the GitHub CLI version is compatible (use `gh --version`)
- Check logs for specific error messages related to command execution

## Next Steps

After successful installation:

- Review the [README.md](README.md) for detailed usage instructions
- Explore the available tools and capabilities
- Configure environment variables for default parameter values
- Set up your MCP client to connect to the server

## Development Setup

If you're planning to contribute to the project:

```bash
# Clone the repository
git clone https://github.com/marioalvial/gh-project-manager-mcp.git
cd gh-project-manager-mcp

# Install dependencies including dev dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Run linters
poetry run ruff check .
``` 