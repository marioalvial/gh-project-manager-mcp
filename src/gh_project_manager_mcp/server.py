import os

# from gh_project_manager_mcp.tools.projects import init_tools as init_project_tools # Assuming this will exist
import uvicorn

# Revert to official SDK import path
# from mcp import FastMCP
from mcp.server.fastmcp import FastMCP

from gh_project_manager_mcp.tools import issues as issue_tools
from gh_project_manager_mcp.tools import pull_requests as pr_tools
# Commented out until implemented
# from gh_project_manager_mcp.tools import projects as project_tools
from gh_project_manager_mcp.utils import gh_utils


def main():
    """Initialize and start the MCP server.
    
    This function creates a FastMCP instance, registers tools from different modules,
    and starts the uvicorn server.
    
    Returns:
        FastMCP: The initialized server instance (useful for testing)
    """
    print("Registering tools...")
    
    # Check for GitHub token
    token = gh_utils.get_github_token()
    if not token:
        print("ERROR: GitHub token not found. Set the GITHUB_TOKEN environment variable.")
        import sys
        sys.exit(1)
    
    # Create the server instance
    server = FastMCP(
        title="GitHub Project Manager MCP",
        description="An MCP server wrapping the GitHub CLI (`gh`) for project management tasks.",
        version="0.1.0",
    )

    # Initialize tools from different modules
    issue_tools.init_tools(server)
    pr_tools.init_tools(server)
    # project_tools.init_tools(server) # Uncomment when ready

    print("Tool registration complete.")

    # Return the server for testing purposes
    return server


def start_server(server):
    """Start the uvicorn server with the given FastMCP instance.
    
    Args:
        server (FastMCP): The FastMCP server instance to run
        
    Returns:
        None
    """
    host = os.environ.get("MCP_SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_SERVER_PORT", 8191))

    print(f"Starting server on host {host}, port {port}...")
    # Run the server using uvicorn
    uvicorn.run(server, host=host, port=port)


if __name__ == "__main__":
    server = main()
    start_server(server)
