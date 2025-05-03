#!/usr/bin/env python
"""Command-line entry point for GitHub Project Manager MCP server."""

import sys
from typing import List, Optional


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
        print("Starting in stdio mode", file=sys.stderr)
        from gh_project_manager_mcp.stdio_server import run_stdio_server

        run_stdio_server()
    else:
        print("Starting in HTTP mode", file=sys.stderr)
        from gh_project_manager_mcp.server import main

        # This follows the current pattern in server.py's __main__ block
        main()


if __name__ == "__main__":
    main()
