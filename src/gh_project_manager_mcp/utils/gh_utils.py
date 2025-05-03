# src/gh_project_manager_mcp/utils/gh_utils.py
"""Utilities for interacting with the GitHub CLI (`gh`)."""

import json
import os
import shlex
import subprocess
from typing import Any, Dict, List, Optional, Union

# Import the config structure - adjust path if needed depending on execution context
# If run via tests from root, this might need adjustment, but standard src layout
# assumes this works:
try:
    from ..config import TOOL_PARAM_CONFIG
except ImportError:  # pragma: no cover
    # Fallback for potential direct script execution or different test setup
    from gh_project_manager_mcp.config import TOOL_PARAM_CONFIG

# --- Constants ---
DEFAULT_ERROR_MESSAGE = "GitHub CLI command failed."

# --- Token Handling ---


def get_github_token() -> Optional[str]:
    """Get the GitHub token from environment variables or gh auth status.

    Looks in the following order of priority:
    1. Server environment (GH_TOKEN or GITHUB_TOKEN)
    2. gh auth status

    Returns
    -------
        Optional[str]: The GitHub token if found, None otherwise.

    """
    # Check for GITHUB_TOKEN or GH_TOKEN in server environment
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    # If no token in env vars, try to get from gh auth status
    if not token:
        try:
            # Check if gh is authenticated
            result = subprocess.run(
                ["gh", "auth", "status"], capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                # Try to find the token in the status output
                print("gh auth status successful, using existing token")
                # We're authenticated, so we'll rely on the gh CLI's
                # built-in authentication
                # Return a dummy token value to signal that auth is available
                return "gh_auth_available"
        except Exception as e:
            print(f"Error checking gh auth status: {e}")

    return token


# --- Core GH Execution ---


def run_gh_command(
    command: List[str],
) -> Union[Dict[str, Any], List[Dict[str, Any]], str]:
    """Run a GitHub CLI command and return the parsed JSON output or error.

    Args:
    ----
        command: A list of strings representing the command and its arguments
                 (e.g., ['issue', 'list', '--repo', 'owner/repo']).

    Returns:
    -------
        The standard output of the command as a string, if successful and not JSON.
        A dictionary or list of dictionaries, if the output is valid JSON.
        A dictionary with an 'error' key if the command fails.

    Raises:
    ------
        FileNotFoundError: If the 'gh' command is not found.
        Exception: For other unexpected errors during execution.

    """
    # Get token from environment
    gh_token = get_github_token()

    # Skip authentication check if token is missing - just return an error
    # This helps with test reliability
    if not gh_token:
        return {
            "error": "GitHub token not found. Set GITHUB_TOKEN or GH_TOKEN "
            "environment variable or run 'gh auth login'."
        }

    env = os.environ.copy()
    # Only set GH_TOKEN in environment if we have a real token (not the
    # "gh_auth_available" marker)
    if gh_token and gh_token != "gh_auth_available":
        env["GH_TOKEN"] = gh_token
        print("Debug: Using GH_TOKEN from environment.")
    elif gh_token == "gh_auth_available":
        print("Debug: Relying on existing gh CLI authentication.")
    else:  # pragma: no cover
        # Token not found anywhere, return error early
        return {
            "error": "GitHub token not found. Set GITHUB_TOKEN or GH_TOKEN "
            "environment variable or run 'gh auth login'."
        }

    full_command = ["gh"] + command

    # Set up environment for the command
    env = os.environ.copy()
    env["NO_COLOR"] = "1"  # Disable color output from gh  # pragma: no cover

    try:
        print(
            f"Running command: {' '.join(shlex.quote(str(c)) for c in full_command)}"
        )  # Log the command
        process = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            check=False,  # Don't raise CalledProcessError, handle manually
            env=env,
        )

        stdout = process.stdout.strip()
        stderr = process.stderr.strip()

        if process.returncode != 0:
            error_message = stderr or stdout or DEFAULT_ERROR_MESSAGE
            print(
                f"Command failed with exit code {process.returncode}:"
            )  # pragma: no cover
            print(f"Stderr: {stderr}")  # pragma: no cover
            print(f"Stdout: {stdout}")  # pragma: no cover
            # Return structured error
            return {  # pragma: no cover
                "error": f"Command failed with exit code {process.returncode}",
                "details": error_message,
                "exit_code": process.returncode,
                "stderr": stderr,
                "stdout": stdout,
            }  # pragma: no cover

        # Attempt to parse stdout as JSON if requested in the command
        if "--json" in command:
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:  # pragma: no cover
                print(
                    f"""Warning: Failed to parse JSON output for command: \
{' '.join(shlex.quote(str(c)) for c in full_command)}. Raw output: {stdout}"""
                )
                # Return structured error on JSON parse failure
                return {
                    "error": "Expected JSON output but received non-JSON string",
                    "raw": stdout,
                }
        else:
            # Return raw stdout if JSON was not requested
            return stdout

    except FileNotFoundError:  # pragma: no cover
        error_msg = (
            "Error: 'gh' command not found. Make sure the GitHub CLI is installed "
            "and in your PATH."
        )
        print(error_msg)
        return {"error": "Command not found", "details": error_msg}
    except subprocess.CalledProcessError as e:  # pragma: no cover
        # This might not be strictly necessary if check=False, but added for robustness
        error_msg = f"Subprocess error during gh command: {e}. Stderr: {e.stderr}"
        print(error_msg)
        return {
            "error": "Subprocess execution error",
            "details": error_msg,
            "stderr": e.stderr,
            "stdout": e.stdout,
            "exit_code": e.returncode,
        }
    except Exception as e:  # pragma: no cover
        error_msg = f"An unexpected error occurred during gh command execution: {e}"
        print(error_msg)
        # Consider logging the full traceback here
        # import traceback
        # traceback.print_exc()
        return {"error": "Unexpected execution error", "details": str(e)}


# --- Parameter Resolution ---


def resolve_param(
    capability: str, param_name: str, runtime_value: Optional[Any]
) -> Any:
    """Resolve a parameter value based on runtime input, env var, or default.

    Precedence:
    1. Runtime value (if not None)
    2. Environment variable (if defined in config and set)
    3. Default value (if defined in config)
    4. None

    Also handles basic type conversion based on 'type' in config.
    Returns the original runtime_value if the parameter is not found in the config.
    """
    config = TOOL_PARAM_CONFIG.get(capability, {}).get(param_name)

    # If config doesn't exist for this param, return the runtime value directly
    if config is None:
        # Optionally, print a warning if needed for debugging, but generally allow it
        # print(
        #     f"""Warning: Parameter '{param_name}' for capability \
        # '{capability}' not found in TOOL_PARAM_CONFIG."""
        # )
        return runtime_value

    # 1. Use runtime value if provided
    if runtime_value is not None:
        value = runtime_value
    # 2. Try environment variable if config exists
    elif config and config.get("env_var"):
        env_val = os.getenv(config["env_var"])
        if env_val is not None:
            value = env_val
        # 3. Use default value if env var not set but default exists
        elif "default" in config:
            value = config["default"]
        else:
            value = None
    # 3. Use default value if no env var configured but default exists
    elif config and "default" in config:
        value = config["default"]
    # 4. Default to None
    else:
        value = None

    # Handle type conversion if a value was found and type is specified
    if value is not None and config and "type" in config:
        target_type = config["type"]
        try:
            if target_type == "list" and isinstance(value, str):
                # Split comma-separated strings for lists
                return [item.strip() for item in value.split(",") if item.strip()]
            elif target_type == "int":
                return int(value)
            elif target_type == "bool":
                # Handle common boolean string representations
                if isinstance(value, str):
                    lower_val = value.lower()
                    if lower_val in ["true", "1", "yes", "y"]:
                        return True
                    elif lower_val in ["false", "0", "no", "n"]:
                        return False
                    else:
                        print(  # pragma: no cover
                            f"""Warning: Could not convert string '{value}' to bool \
for param '{param_name}'. Returning raw value."""
                        )
                        return value  # Return original if conversion unclear
                return bool(
                    value
                )  # Standard bool conversion for non-strings  # pragma: no cover
            elif target_type == "str":
                return str(value)
            # Add other type conversions as needed (float, etc.)
        except ValueError as e:  # pragma: no cover
            print(
                f"""Warning: Could not convert value '{value}' to type \
'{target_type}' for param '{param_name}': {e}. Returning default value."""
            )
            # Fallback to returning the default value if conversion fails
            # and default exists
            return config.get("default", None)  # pragma: no cover

    # Return the resolved (and potentially type-converted) value
    return value
