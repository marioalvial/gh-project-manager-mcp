# GitHub Project Manager MCP Server

A Model Context Protocol (MCP) server that wraps the GitHub CLI (`gh`) to provide advanced GitHub project management capabilities for AI assistants.

## Overview

GitHub Project Manager MCP Server enables AI assistants to interact with GitHub repositories, issues, pull requests, and other GitHub features through a standardized Model Context Protocol interface. By wrapping the GitHub CLI, it provides a seamless integration layer between AI agents and GitHub's features.

## Installation

### Prerequisites

- Python 3.11 or higher
- Poetry (for dependency management)
- GitHub CLI (`gh`) installed

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/gh-project-manager-mcp.git
cd gh-project-manager-mcp

# Install dependencies with Poetry
poetry install

# Verify installation
poetry run python -m gh_project_manager_mcp --version
```

### Docker Installation

```bash
# Build the Docker image
docker build -t gh-project-manager-mcp .

# Run the container with your GitHub token
docker run -p 8000:8000 -e GH_TOKEN=your_github_token gh-project-manager-mcp
```

## Authentication

This MCP server handles GitHub authentication for you using a personal access token. You don't need to authenticate with the GitHub CLI separately.

### Setting Up Your GitHub Token

1. Create a Personal Access Token (PAT) at https://github.com/settings/tokens
2. Ensure the token has appropriate scopes for your intended operations:
   - `repo` for full repository access
   - `workflow` for GitHub Actions control
   - `read:org` for organization access (if needed)

### Providing Your Token

The token can be provided through:

```bash
# Environmental variable
export GH_TOKEN=your_github_token

# Or when starting the server
GH_TOKEN=your_github_token poetry run python -m gh_project_manager_mcp.server
```

## Usage

### Starting the Server

```bash
# Start the server on default port (8000)
poetry run python -m gh_project_manager_mcp.server

# Start with custom port
poetry run python -m gh_project_manager_mcp.server --port 8080
```

### Configuration

Configuration is managed through environment variables or a `.env` file:

```
GH_TOKEN=your_github_token           # GitHub Personal Access Token (required)
GH_DEFAULT_OWNER=default_repo_owner  # Default repository owner (optional)
GH_DEFAULT_REPO=default_repo_name    # Default repository name (optional)
```

## Available Tools

The server exposes the following GitHub operations as MCP tools:

### Issues

* **create_issue** - Create a new issue in a GitHub repository
  * `owner`: Repository owner (string, required)
  * `repo`: Repository name (string, required)
  * `title`: Issue title (string, required)
  * `body`: Issue body content (string, optional)
  * `labels`: Labels to apply to this issue (array of strings, optional)
  * `assignees`: Usernames to assign to this issue (array of strings, optional)
  * `milestone`: Milestone number (number, optional)

* **get_issue** - Get details of a specific issue
  * `owner`: Repository owner (string, required)
  * `repo`: Repository name (string, required)
  * `issue_number`: The number of the issue (number, required)

* **list_issues** - List issues in a GitHub repository
  * `owner`: Repository owner (string, required)
  * `repo`: Repository name (string, required)
  * `state`: Filter by state ('open', 'closed', 'all') (string, optional)
  * `labels`: Filter by labels (array of strings, optional)
  * `sort`: Sort by ('created', 'updated', 'comments') (string, optional)
  * `direction`: Sort direction ('asc', 'desc') (string, optional)
  * `since`: Filter by date (ISO 8601 timestamp) (string, optional)
  * `page`: Page number for pagination (number, optional)
  * `perPage`: Results per page for pagination (number, optional)

* **update_issue** - Update an existing issue
  * `owner`: Repository owner (string, required)
  * `repo`: Repository name (string, required)
  * `issue_number`: Issue number to update (number, required)
  * `title`: New title (string, optional)
  * `body`: New description (string, optional)
  * `state`: New state ('open' or 'closed') (string, optional)
  * `labels`: New labels (array of strings, optional)
  * `assignees`: New assignees (array of strings, optional)
  * `milestone`: New milestone number (number, optional)

* **add_issue_comment** - Add a comment to an issue
  * `owner`: Repository owner (string, required)
  * `repo`: Repository name (string, required)
  * `issue_number`: Issue number to comment on (number, required)
  * `body`: Comment text (string, required)

* **get_issue_comments** - Get comments for an issue
  * `owner`: Repository owner (string, required)
  * `repo`: Repository name (string, required)
  * `issue_number`: Issue number (number, required)
  * `page`: Page number (number, optional)
  * `per_page`: Number of records per page (number, optional)

### Pull Requests

* **create_pull_request** - Create a new pull request
  * `owner`: Repository owner (string, required)
  * `repo`: Repository name (string, required)
  * `title`: PR title (string, required)
  * `head`: Branch containing changes (string, required)
  * `base`: Branch to merge into (string, required)
  * `body`: PR description (string, optional)
  * `draft`: Create as draft PR (boolean, optional)
  * `maintainer_can_modify`: Allow maintainer edits (boolean, optional)

* **get_pull_request** - Get details of a specific pull request
  * `owner`: Repository owner (string, required)
  * `repo`: Repository name (string, required)
  * `pullNumber`: Pull request number (number, required)

* **list_pull_requests** - List pull requests in a repository
  * `owner`: Repository owner (string, required)
  * `repo`: Repository name (string, required)
  * `state`: Filter by state ('open', 'closed', 'all') (string, optional)
  * `head`: Filter by head user/org and branch (string, optional)
  * `base`: Filter by base branch (string, optional)
  * `sort`: Sort by ('created', 'updated', 'popularity', 'long-running') (string, optional)
  * `direction`: Sort direction ('asc', 'desc') (string, optional)
  * `page`: Page number for pagination (number, optional)
  * `perPage`: Results per page for pagination (number, optional)

* **merge_pull_request** - Merge a pull request
  * `owner`: Repository owner (string, required)
  * `repo`: Repository name (string, required)
  * `pullNumber`: Pull request number (number, required)
  * `merge_method`: Merge method ('merge', 'squash', 'rebase') (string, optional)
  * `commit_title`: Title for merge commit (string, optional)
  * `commit_message`: Extra detail for merge commit (string, optional)

### Repositories

* **create_repository** - Create a new GitHub repository
  * `name`: Repository name (string, required)
  * `description`: Repository description (string, optional)
  * `private`: Whether the repository is private (boolean, optional)
  * `autoInit`: Initialize with README (boolean, optional)

* **get_file_contents** - Get contents of a file or directory
  * `owner`: Repository owner (string, required)
  * `repo`: Repository name (string, required)
  * `path`: File path (string, required)
  * `branch`: Branch to get contents from (string, optional)

* **create_or_update_file** - Create or update a single file
  * `owner`: Repository owner (string, required)
  * `repo`: Repository name (string, required)
  * `path`: Path where to create/update the file (string, required)
  * `content`: Content of the file (string, required)
  * `message`: Commit message (string, required)
  * `branch`: Branch to create/update the file in (string, required)
  * `sha`: SHA of file being replaced (for updates) (string, optional)

* **create_branch** - Create a new branch
  * `owner`: Repository owner (string, required)
  * `repo`: Repository name (string, required) 
  * `branch`: Name for new branch (string, required)
  * `from_branch`: Source branch (defaults to repo default) (string, optional)

## Integrating With AI Assistants

This MCP server can be integrated with AI assistants that support the Model Context Protocol:

```python
from mcp_client import MCPClient

# Initialize the client
client = MCPClient("http://localhost:8000")

# Example: Create an issue
result = client.call_tool(
    "mcp_github_create_issue",
    {
        "owner": "yourusername",
        "repo": "your-repo",
        "title": "Bug: Application crashes on startup",
        "body": "When launching the app, it crashes immediately with error code 0xC0000374."
    }
)
```

## Development

### Project Structure

```
src/gh_project_manager_mcp/
├── config.py            # Configuration with TOOL_PARAM_CONFIG
├── server.py            # MCP server entry point 
├── tools/               # GitHub operations implementation
│   ├── __init__.py
│   ├── issues.py
│   ├── pull_requests.py
│   └── ...
└── utils/              # Shared utilities
    ├── __init__.py
    └── gh_utils.py     # GitHub CLI wrapper utilities
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test suite
poetry run pytest tests/tools/test_issues.py
```

## Troubleshooting

### Common Issues

#### Token Permissions

If operations fail with 403 errors:
1. Verify your token has the necessary permissions for the operation
2. For organization operations, ensure your token has appropriate organization access

#### Rate Limiting

If you encounter rate limiting issues:
1. GitHub API has rate limits based on your token/account type
2. Consider using a token with higher limits (e.g., from a GitHub Apps installation)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
