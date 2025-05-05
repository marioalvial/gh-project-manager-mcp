"""Utility modules for the GitHub Project Manager MCP."""

import sys

# Redirect all print statements to stderr
# This ensures stdout is reserved exclusively for JSON-RPC messages
_original_print = print

# Import the print_stderr function from gh_utils
from gh_project_manager_mcp.utils.gh_utils import print_stderr

# Replace the global print function
print = print_stderr

# Export modules
__all__ = ["gh_utils"]
