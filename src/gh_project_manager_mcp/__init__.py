"""GitHub Project Manager MCP package."""

__version__ = "0.1.0"

import sys

# Redirect all print statements to stderr
# This ensures stdout is reserved exclusively for JSON-RPC messages
_original_print = print

# Remove the local implementation and import from utils.gh_utils
from gh_project_manager_mcp.utils.gh_utils import print_stderr

# Replace the global print function
print = print_stderr

# This will affect all imports from this package
__all__ = []
