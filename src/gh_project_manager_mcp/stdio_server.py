#!/usr/bin/env python
"""MCP server with stdio transport for GitHub Project Manager."""

import sys

import anyio
from mcp.server.stdio import stdio_server

from gh_project_manager_mcp.server import main as init_server
from gh_project_manager_mcp.utils import gh_utils


async def run_async() -> None:
    """Run the server asynchronously with stdio transport."""
    print("Starting GitHub Project Manager MCP (stdio transport)...", file=sys.stderr)

    # Check for GitHub token and exit if not found
    token = gh_utils.get_github_token()
    if not token:
        print("Error: GitHub token not found in environment.", file=sys.stderr)
        print(
            "       Please set GITHUB_TOKEN or GH_TOKEN environment variable.",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        print("Found GitHub token, proceeding with startup.", file=sys.stderr)

    # Initialize the server and all tools
    server = init_server()

    print("Server initialized, switching to stdio mode...", file=sys.stderr)

    # Create initialization options
    initialization_options = server._mcp_server.create_initialization_options()

    try:
        # Use the stdio_server context manager to handle stdin/stdout streams
        async with stdio_server() as (read_stream, write_stream):
            print(
                "Server connected to stdio, ready for MCP client communication",
                file=sys.stderr,
            )
            await server._mcp_server.run(
                read_stream,
                write_stream,
                initialization_options,
            )
            print("Server run completed successfully.", file=sys.stderr)
    except Exception as e:
        import traceback

        print(f"Error running server: {str(e)}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)


def run_stdio_server() -> None:
    """Run the MCP server using stdio transport.

    This function initializes the server and runs it using the stdio
    transport mechanism, which allows it to communicate via standard
    input/output streams, making it compatible with MCP clients.
    """
    try:
        # Run the async function with anyio
        anyio.run(run_async)
    except KeyboardInterrupt:
        print("Server stopped by user.", file=sys.stderr)
    except Exception as e:
        import traceback

        print(f"Error running server: {str(e)}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_stdio_server()
