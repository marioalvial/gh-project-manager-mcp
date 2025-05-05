# src/gh_project_manager_mcp/utils/gh_utils.py
"""Utilities for interacting with the GitHub CLI (`gh`)."""

import subprocess
import sys
import traceback
from typing import List

from result import Err, Ok, Result

from gh_project_manager_mcp.utils.error import ApplicationError, Error, ErrorCode

# Constants
DEFAULT_ERROR_MESSAGE = "An unknown error occurred during GitHub CLI operation"

# Export the public functions
__all__ = [
    "execute_gh_command",
    "print_stderr",
]

_original_print = print


def print_stderr(*args, **kwargs):
    """Wrap print function to always write to stderr.

    Ensures all print statements are redirected to stderr,
    keeping stdout clean for the JSON-RPC protocol messages.

    Args:
    ----
        *args: Arguments to print.
        **kwargs: Keyword arguments to print.

    Returns:
    -------
        The result of the original print function.

    """
    if "file" not in kwargs:
        kwargs["file"] = sys.stderr
    return _original_print(*args, **kwargs)


def execute_gh_command(command: List[str]) -> Result[str, Error]:
    """Execute a GitHub CLI command and return a Result object.

    Args:
    ----
        command: The command to execute as a list of strings (e.g., ['issue', 'list']).

    Returns:
    -------
        Ok(str) containing the raw stdout output if successful.
        Err(Error) containing error details if the command fails.

    """
    try:
        full_command = ["gh"] + command

        process = subprocess.run(
            full_command, capture_output=True, text=True, check=False
        )

        stdout_output = process.stdout.strip()
        stderr_output = process.stderr.strip()

        if process.returncode != 0:
            error_msg = (
                stderr_output or f"Command failed with exit code {process.returncode}"
            )
            print_stderr(f"GitHub CLI Error ({process.returncode}): {error_msg}")

            # Create command failed error with the process as the exception
            error = Error(
                ErrorCode.GH_COMMAND_FAILED,
                exception=process,
                details={"stdout": stdout_output, "stderr": stderr_output},
                format_args={"reason": error_msg},
            )
            return Err(error)

        return Ok(stdout_output)

    except FileNotFoundError as e:
        print_stderr(
            "Error: 'gh' command not found. Is GitHub CLI installed and in PATH?"
        )
        error = Error(ErrorCode.GH_CLI_NOT_FOUND, exception=e)
        return Err(error)
    except ApplicationError as e:
        print_stderr(f"ApplicationError during gh execution: {e}")
        return Err(e.error)
    except Exception as e:
        print_stderr(f"Unexpected error during gh execution: {e}")
        error = Error(
            ErrorCode.GH_UNEXPECTED_ERROR,
            exception=e,
            details={"traceback": traceback.format_exc()},
            format_args={"message": str(e)},
        )
        return Err(error)
