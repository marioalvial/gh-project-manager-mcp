#!/usr/bin/env python
"""GitHub Project Manager MCP server with stdio transport."""

import os
import sys

import anyio
from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server

# Import tool modules
from gh_project_manager_mcp.tools import issues as issues_tools
from gh_project_manager_mcp.tools import projects as project_tools
from gh_project_manager_mcp.tools import pull_requests as pr_tools
from gh_project_manager_mcp.utils.gh_utils import print_stderr

# Replace the global print function to ensure stdout is reserved for JSON-RPC messages
print = print_stderr


def create_server():
    """Initialize the FastMCP server and register tools.

    Returns
    -------
        FastMCP: The initialized server instance

    """
    print("Initializing server...")
    # Instantiate server
    server = FastMCP(
        title="GitHub Project Manager MCP",
        description=(
            "An MCP server wrapping the GitHub CLI (`gh`) for project management "
            "tasks."
        ),
        version="0.1.0",
    )

    # Register tools
    print("Registering tools...")
    issues_tools.init_tools(server)
    project_tools.init_tools(server)
    pr_tools.init_tools(server)
    print("Tool registration complete.")

    return server


async def run_async() -> None:
    """Run the server asynchronously with stdio transport."""
    print("Starting GitHub Project Manager MCP (stdio transport)...")

    # Check for GitHub token and exit if not found
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("Error: GitHub token not found in environment.")
        print("       Please set GITHUB_TOKEN or GH_TOKEN environment variable.")
        sys.exit(1)
    else:
        print("Found GitHub token, proceeding with startup.")

    # Initialize the server and all tools
    server = create_server()

    print("Server initialized, switching to stdio mode...")

    # Create initialization options
    initialization_options = server._mcp_server.create_initialization_options()

    try:
        # Use the stdio_server context manager to handle stdin/stdout streams
        async with stdio_server() as (read_stream, write_stream):
            print("Server connected to stdio, ready for MCP client communication")
            await server._mcp_server.run(
                read_stream,
                write_stream,
                initialization_options,
            )
            print("Server run completed successfully.")
    except Exception as e:
        import traceback

        print(f"Error running server: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


def main() -> None:
    """Run the MCP server using stdio transport.

    This function initializes the server and runs it using the stdio
    transport mechanism, which allows it to communicate via standard
    input/output streams, making it compatible with MCP clients.
    """
    try:
        # Run the async function with anyio
        anyio.run(run_async)
    except KeyboardInterrupt:
        print("Server stopped by user.")
    except Exception as e:
        import traceback

        print(f"Error running server: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


# --- Execution Guard --- #
if __name__ == "__main__":
    # Check for GH_TOKEN before starting
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print(
            "Error: GitHub token not found in environment. Server cannot start.",
            file=sys.stderr,
        )
        sys.exit(1)
    # Call main only when script is executed directly
    main()

# NO OTHER CODE should be at module level below this point.
