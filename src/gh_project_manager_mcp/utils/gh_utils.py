# src/gh_project_manager_mcp/utils/gh_utils.py
"""Utilities for interacting with the GitHub CLI (`gh`)."""

import json
import os
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
    token = get_github_token()
    if not token:
        print("DEBUG [GH Command]: No GitHub token found in environment")
        return {
            "error": "GitHub token not found in environment",
            "details": "Set GITHUB_TOKEN or GH_TOKEN environment variable.",
        }

    # Redact the token for logging (mostra apenas os primeiros 4 caracteres)
    redacted_token = token[:4] + "..." if token else "None"
    print(f"DEBUG [GH Command]: Using token starting with '{redacted_token}'")

    # Prepare the full command with 'gh' as the executable
    full_command = ["gh"] + command
    print(f"DEBUG [GH Command]: Running command: {' '.join(full_command)}")

    # Run the command using subprocess
    try:
        # Verificando se gh está acessível
        try:
            gh_version_cmd = ["gh", "--version"]
            gh_version = subprocess.run(
                gh_version_cmd,
                capture_output=True,
                text=True,
                check=False,
                env={"GITHUB_TOKEN": token} if token else None,
            )
            print(f"DEBUG [GH Command]: GH Version check: exit={gh_version.returncode}")
            print(
                f"DEBUG [GH Command]: GH Version: {gh_version.stdout.strip() if gh_version.returncode == 0 else 'Error'}"
            )

            if gh_version.returncode != 0:
                print(
                    f"DEBUG [GH Command]: GH Version check failed: {gh_version.stderr}"
                )
                return {
                    "error": "Failed to verify GitHub CLI installation",
                    "details": gh_version.stderr,
                    "exit_code": gh_version.returncode,
                }
        except Exception as e:
            print(f"DEBUG [GH Command]: Error checking GH version: {str(e)}")

        # Verificando a autenticação do gh
        try:
            auth_check_cmd = ["gh", "auth", "status"]
            auth_check = subprocess.run(
                auth_check_cmd,
                capture_output=True,
                text=True,
                check=False,
                env={"GITHUB_TOKEN": token} if token else None,
            )
            print(f"DEBUG [GH Command]: Auth check: exit={auth_check.returncode}")
            if auth_check.returncode == 0:
                print(f"DEBUG [GH Command]: Auth status: {auth_check.stdout.strip()}")
            else:
                print(f"DEBUG [GH Command]: Auth failed: {auth_check.stderr}")
                return {
                    "error": "GitHub CLI authentication failed",
                    "details": auth_check.stderr,
                    "exit_code": auth_check.returncode,
                }
        except Exception as e:
            print(f"DEBUG [GH Command]: Error checking auth status: {str(e)}")

        # Executando o comando principal
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            check=False,
            env={"GITHUB_TOKEN": token} if token else None,
        )

        # Check if the command was successful
        if result.returncode == 0:
            print(
                f"DEBUG [GH Command]: Command succeeded with output length: {len(result.stdout)}"
            )
            stdout = result.stdout.strip()

            # If the output is empty, return an empty string
            if not stdout:
                return ""

            # Try to parse the output as JSON
            try:
                # Check if the output is an array
                if stdout.startswith("[") and stdout.endswith("]"):
                    return json.loads(stdout)
                # Check if the output is an object
                elif stdout.startswith("{") and stdout.endswith("}"):
                    return json.loads(stdout)
                # Otherwise, return the raw output as a string
                else:
                    return stdout
            except json.JSONDecodeError:
                print(
                    "DEBUG [GH Command]: Output is not valid JSON, returning as string"
                )
                # If the output is not valid JSON, return it as a string
                return stdout
        else:
            # Command failed
            print(
                f"DEBUG [GH Command]: Command failed with exit code {result.returncode}"
            )
            print(f"DEBUG [GH Command]: Error output: {result.stderr}")

            # Build a structured error response
            error_response = {
                "error": f"GitHub CLI command failed with exit code {result.returncode}",
                "details": result.stderr,
                "exit_code": result.returncode,
                "stdout": result.stdout,  # Include stdout for debugging
                "stderr": result.stderr,
            }

            # Try to parse stderr as JSON in case GitHub CLI returned a JSON error
            try:
                stderr_json = json.loads(result.stderr)
                error_response["stderr_json"] = stderr_json
            except json.JSONDecodeError:
                pass  # Stderr is not JSON, that's fine

            return error_response

    except FileNotFoundError:
        print("DEBUG [GH Command]: GitHub CLI not found")
        # The 'gh' executable was not found
        return {
            "error": "GitHub CLI not found",
            "details": "Please install GitHub CLI (https://cli.github.com/)",
        }
    except Exception as e:
        # Handle any other exceptions
        import traceback

        error_trace = traceback.format_exc()
        print(f"DEBUG [GH Command]: Unexpected error: {str(e)}")
        print(f"DEBUG [GH Command]: Traceback: {error_trace}")
        return {
            "error": f"Unexpected error: {str(e)}",
            "details": error_trace,
        }


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
