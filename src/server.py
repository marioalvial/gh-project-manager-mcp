"""Main entry point for the GitHub Project Manager MCP server."""

import os
import sys

import uvicorn
from mcp.server.fastmcp import FastMCP

# Assuming correct relative imports based on project structure
from .tools import issues as issues_tools
from .tools import projects as project_tools
from .tools import pull_requests as pr_tools
from .utils import gh_utils


def main():
    """Instantiate the server, register tools, and run the MCP server."""
    # Determine host and port inside main
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_SERVER_PORT", "8191"))  # Default to 8191

    print("Initializing server...")
    # Instantiate server inside main
    server = FastMCP(
        title="GitHub Project Manager MCP",
        description=(
            "An MCP server wrapping the GitHub CLI (`gh`) for project management "
            "tasks."
        ),
        version="0.1.0",
    )

    # Register tools inside main
    print("Registering tools...")
    issues_tools.init_tools(server)
    project_tools.init_tools(server)
    pr_tools.init_tools(server)
    print("Tool registration complete.")

    # Start server inside main
    print(f"Starting server on host {host}, port {port}...")
    uvicorn.run(server.app, host=host, port=port)


# --- Execution Guard --- #
if __name__ == "__main__":
    # Check for GH_TOKEN before starting
    if not gh_utils.get_github_token():
        print(
            "Error: GH_TOKEN environment variable not set. Server cannot start.",
            file=sys.stderr,
        )
        sys.exit(1)
    # Call main only when script is executed directly
    main()

# NO OTHER CODE should be at module level below this point.
