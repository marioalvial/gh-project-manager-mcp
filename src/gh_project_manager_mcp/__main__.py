#!/usr/bin/env python
"""Main entry point for the GitHub Project Manager MCP application."""

import sys
from typing import List, Optional

from gh_project_manager_mcp.utils.gh_utils import print_stderr

# Replace the global print function
print = print_stderr


def main(args: Optional[List[str]] = None) -> None:
    """Run the GitHub Project Manager MCP server.

    Args:
    ----
        args: Command line arguments. Defaults to sys.argv[1:].
            - If "stdio" is passed, runs in stdio mode.
            - Otherwise, runs in HTTP mode (default).

    """
    if args is None:
        args = sys.argv[1:]

    # Check if we should run in stdio mode
    if args and args[0] == "stdio":
        print("Starting in stdio mode")
        from gh_project_manager_mcp.server import main as run_stdio_server

        run_stdio_server()
    else:
        print("Starting in HTTP mode")
        from gh_project_manager_mcp.server import main

        # This follows the current pattern in server.py's __main__ block
        main()


if __name__ == "__main__":
    try:
        # Execute the main function from the server module
        main()
    except KeyboardInterrupt:
        print("\nExiting due to keyboard interrupt.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback

        print(f"\nTraceback:\n{traceback.format_exc()}")
        sys.exit(1)
