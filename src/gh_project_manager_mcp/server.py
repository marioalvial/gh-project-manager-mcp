"""Main entry point for the GitHub Project Manager MCP server."""

import os

import uvicorn

# from mcp import FastMCP
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from gh_project_manager_mcp.tools import issues as issue_tools
from gh_project_manager_mcp.tools import pull_requests as pr_tools

# Commented out until implemented
# from gh_project_manager_mcp.tools import projects as project_tools
from gh_project_manager_mcp.utils import gh_utils


# Simple health check endpoint - KEEP
async def health(request):
    """Run simple health check."""
    return PlainTextResponse("OK")


def main():
    """Initialize and start the MCP server.

    This function creates a FastMCP instance, registers tools from different modules,
    and returns the configured server instance.

    Returns
    -------
        FastMCP: The initialized server instance

    """
    print("Registering tools...")

    # Check for GitHub token and exit if not found
    token = gh_utils.get_github_token()
    if not token:
        print("Error: GitHub token not found in environment.")
        print("       Please set GITHUB_TOKEN or GH_TOKEN environment variable.")
        import sys

        sys.exit(1)
    else:
        print("Found GitHub token, proceeding with startup.")

    # Create the server instance
    server = FastMCP(
        title="GitHub Project Manager MCP",
        description="An MCP server wrapping the GitHub CLI (`gh`) "
        "for project management tasks.",
        version="0.1.0",
    )

    # Initialize tools from different modules
    issue_tools.init_tools(server)
    pr_tools.init_tools(server)
    # project_tools.init_tools(server) # Uncomment when ready

    print("Tool registration complete.")

    # Return the server for testing purposes
    return server


if __name__ == "__main__":
    # Get host and port from env vars for informational purposes
    host = os.environ.get("MCP_SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_SERVER_PORT", 8191))
    print(f"Starting server on host {host}, port {port}...")

    # Using the official MCP SDK approach with SSE transport
    server = main()

    from starlette.applications import Starlette

    # Remove unused imports if info/home are removed
    # from starlette.responses import HTMLResponse, JSONResponse # Removed these
    from starlette.routing import Mount, Route

    # REMOVED info async function

    # REMOVED home async function

    # Create and configure the SSE transport with correct endpoints - KEEP
    sse = SseServerTransport("/messages/")

    # SSE connection handler - KEEP
    async def handle_sse(request: Request) -> None:
        """Handle incoming SSE connections."""
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,  # noqa: SLF001
        ) as (read_stream, write_stream):
            # Run the MCP server with the streams
            # Use server's initialization options
            await server._mcp_server.run(
                read_stream,
                write_stream,
                server._mcp_server.create_initialization_options(),
            )

    # Create a starlette app - REMOVE '/' and '/info' routes
    app = Starlette(
        routes=[
            # Route("/", home), # REMOVED
            Route("/health", health),  # KEEP
            # Route("/info", info), # REMOVED
            # Direct SSE connection endpoint - KEEP
            Route("/sse", endpoint=handle_sse),
            # Mount the messages endpoint for SSE communication - KEEP
            Mount("/messages", app=sse.handle_post_message),
        ]
    )

    # Run uvicorn with the app and configured host/port - KEEP
    uvicorn.run(app, host=host, port=port)
