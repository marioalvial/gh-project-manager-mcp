"""Unit tests for gh_utils shared utilities."""
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from unittest.mock import MagicMock, call, patch

import pytest

from src.gh_project_manager_mcp.config import TOOL_PARAM_CONFIG
from src.gh_project_manager_mcp.utils.gh_utils import resolve_param, run_gh_command

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

# --- Test Constants ---
TEST_CAPABILITY = "issue"
TEST_PARAM_STR = "assignee"  # Default: '@me', Env: DEFAULT_ISSUE_ASSIGNEE
TEST_PARAM_LIST = "labels"  # Default: None, Env: DEFAULT_ISSUE_LABELS
TEST_PARAM_INT = "limit"  # Default: 30, Env: DEFAULT_ISSUE_LIST_LIMIT
TEST_PARAM_NONE_DEFAULT = "project"  # Default: None, Env: DEFAULT_ISSUE_PROJECT
TEST_COMMAND_ARGS = ["test", "command"]
TEST_COMMAND_ARGS_JSON = ["test", "command", "--json", "field"]
MOCK_TOKEN = "ghp_mocktoken123"


class TestResolveParam:
    """Tests for the resolve_param utility function."""

    def test_runtime_value_provided(self, mocker: "MockerFixture") -> None:
        """Test resolve_param returns runtime value when provided.
        
        Given: A runtime value is provided with an environment variable also set
        When: resolve_param is called with those values
        Then: The runtime value should be returned, ignoring the environment value
        """
        # Given
        runtime_val = "runtime_user"
        env_vars = {
            TOOL_PARAM_CONFIG[TEST_CAPABILITY][TEST_PARAM_STR]["env_var"]: "env_user"
        }
        mocker.patch.dict(os.environ, env_vars, clear=True)

        # When
        result = resolve_param(TEST_CAPABILITY, TEST_PARAM_STR, runtime_val)

        # Then
        assert result == runtime_val

    def test_runtime_value_is_none_env_set(self, mocker: "MockerFixture") -> None:
        """Test resolve_param returns env var when runtime value is None.
        
        Given: A runtime value of None with an environment variable set
        When: resolve_param is called
        Then: The environment variable value should be returned
        """
        # Given
        runtime_val = None
        env_val = "env_user"
        env_var_name = TOOL_PARAM_CONFIG[TEST_CAPABILITY][TEST_PARAM_STR]["env_var"]
        mocker.patch.dict(os.environ, {env_var_name: env_val}, clear=True)

        # When
        result = resolve_param(TEST_CAPABILITY, TEST_PARAM_STR, runtime_val)

        # Then
        assert result == env_val

    def test_runtime_and_env_none_default_exists(self, mocker: "MockerFixture") -> None:
        """Test resolve_param returns default value when runtime/env are None.
        
        Given: A runtime value of None with no environment variable set
        When: resolve_param is called for a parameter with a default value
        Then: The default value from the config should be returned
        """
        # Given
        runtime_val = None
        mocker.patch.dict(os.environ, {}, clear=True)  # Ensure env var is not set
        expected_default = TOOL_PARAM_CONFIG[TEST_CAPABILITY][TEST_PARAM_STR]["default"]

        # When
        result = resolve_param(TEST_CAPABILITY, TEST_PARAM_STR, runtime_val)

        # Then
        assert result == expected_default

    def test_runtime_and_env_none_no_default(self, mocker: "MockerFixture") -> None:
        """Test resolve_param returns None when runtime/env/default are None.
        
        Given: A runtime value of None with no environment variable and no default value
        When: resolve_param is called
        Then: None should be returned
        """
        # Given
        runtime_val = None
        mocker.patch.dict(os.environ, {}, clear=True)  # Ensure env var is not set

        # When
        result = resolve_param(TEST_CAPABILITY, TEST_PARAM_NONE_DEFAULT, runtime_val)

        # Then
        assert result is None

    def test_env_var_list_conversion(self, mocker: "MockerFixture") -> None:
        """Test resolve_param converts comma-separated env var to list.
        
        Given: A runtime value of None with an environment variable containing a comma-separated string
        When: resolve_param is called for a list-type parameter
        Then: The environment variable should be converted to a list of strings
        """
        # Given
        runtime_val = None
        env_val = "bug, documentation, help wanted "  # Note extra space
        env_var_name = TOOL_PARAM_CONFIG[TEST_CAPABILITY][TEST_PARAM_LIST]["env_var"]
        mocker.patch.dict(os.environ, {env_var_name: env_val}, clear=True)
        expected_list = ["bug", "documentation", "help wanted"]

        # When
        result = resolve_param(TEST_CAPABILITY, TEST_PARAM_LIST, runtime_val)

        # Then
        assert isinstance(result, list)
        assert result == expected_list

    def test_env_var_empty_list_conversion(self, mocker: "MockerFixture") -> None:
        """Test resolve_param converts empty env var string to empty list.
        
        Given: A runtime value of None with an empty environment variable
        When: resolve_param is called for a list-type parameter
        Then: An empty list should be returned
        """
        # Given
        runtime_val = None
        env_val = ""
        env_var_name = TOOL_PARAM_CONFIG[TEST_CAPABILITY][TEST_PARAM_LIST]["env_var"]
        mocker.patch.dict(os.environ, {env_var_name: env_val}, clear=True)

        # When
        result = resolve_param(TEST_CAPABILITY, TEST_PARAM_LIST, runtime_val)

        # Then
        assert result == []

    def test_env_var_int_conversion(self, mocker: "MockerFixture") -> None:
        """Test resolve_param converts valid int env var string to int.
        
        Given: A runtime value of None with an environment variable containing a numeric string
        When: resolve_param is called for an int-type parameter
        Then: The environment variable should be converted to an integer
        """
        # Given
        runtime_val = None
        env_val = "50"
        env_var_name = TOOL_PARAM_CONFIG[TEST_CAPABILITY][TEST_PARAM_INT]["env_var"]
        mocker.patch.dict(os.environ, {env_var_name: env_val}, clear=True)

        # When
        result = resolve_param(TEST_CAPABILITY, TEST_PARAM_INT, runtime_val)

        # Then
        assert result == 50

    def test_env_var_invalid_int_uses_default(self, mocker: "MockerFixture") -> None:
        """Test resolve_param returns default when env var int conversion fails.
        
        Given: A runtime value of None with an environment variable containing a non-numeric string
        When: resolve_param is called for an int-type parameter
        Then: The default value should be returned and a warning should be printed
        """
        # Given
        runtime_val = None
        env_val = "not-an-int"
        env_var_name = TOOL_PARAM_CONFIG[TEST_CAPABILITY][TEST_PARAM_INT]["env_var"]
        mocker.patch.dict(os.environ, {env_var_name: env_val}, clear=True)
        expected_default = TOOL_PARAM_CONFIG[TEST_CAPABILITY][TEST_PARAM_INT]["default"]
        mock_print = mocker.patch("builtins.print")  # Capture the mock object

        # When
        result = resolve_param(TEST_CAPABILITY, TEST_PARAM_INT, runtime_val)

        # Then
        assert result == expected_default
        # Assert warning was printed
        found_call = False
        for call_args in mock_print.call_args_list:
            args, kwargs = call_args
            if (
                args
                and f"Warning: Could not convert value '{env_val}'" in args[0]
                and "Returning default value." in args[0]
            ):
                found_call = True
                break
        assert found_call, (
            "Expected 'Could not convert value... Returning default value.' "
            "warning not printed"
        )

    def test_runtime_empty_string_respected(self, mocker: "MockerFixture") -> None:
        """Test resolve_param respects empty string runtime value.
        
        Given: An empty string runtime value with an environment variable set
        When: resolve_param is called
        Then: The empty string should be returned, ignoring the environment variable
        """
        # Given
        runtime_val = ""
        env_vars = {
            TOOL_PARAM_CONFIG[TEST_CAPABILITY][TEST_PARAM_STR]["env_var"]: "env_user"
        }
        mocker.patch.dict(os.environ, env_vars, clear=True)

        # When
        result = resolve_param(TEST_CAPABILITY, TEST_PARAM_STR, runtime_val)

        # Then
        assert result == ""

    def test_runtime_empty_list_respected(self, mocker: "MockerFixture") -> None:
        """Test resolve_param respects empty list runtime value.
        
        Given: An empty list runtime value with an environment variable set
        When: resolve_param is called
        Then: The empty list should be returned, ignoring the environment variable
        """
        # Given
        runtime_val = []
        env_val = "env_label1,env_label2"
        env_var_name = TOOL_PARAM_CONFIG[TEST_CAPABILITY][TEST_PARAM_LIST]["env_var"]
        mocker.patch.dict(os.environ, {env_var_name: env_val}, clear=True)

        # When
        result = resolve_param(TEST_CAPABILITY, TEST_PARAM_LIST, runtime_val)

        # Then
        assert result == []

    def test_config_missing_parameter_returns_none(self, mocker: "MockerFixture") -> None:
        """Test resolve_param returns None and warns for missing config entry.
        
        Given: A runtime value of None with a non-existent capability or parameter
        When: resolve_param is called
        Then: None should be returned
        """
        # Given
        runtime_val = None
        mocker.patch.dict(os.environ, {}, clear=True)
        mocker.patch("builtins.print")  # Mock print to check warning
        missing_capability = "non_existent_capability"
        missing_param = "non_existent_param"

        # When
        result = resolve_param(missing_capability, missing_param, runtime_val)

        # Then
        assert result is None

    def test_uses_str_default(self, mocker: "MockerFixture") -> None:
        """Test resolve_param correctly uses string default from config.
        
        Given: A runtime value of None with no environment variable set
        When: resolve_param is called for a parameter with a string default
        Then: The string default value should be returned
        """
        # Given
        runtime_val = None
        mocker.patch.dict(os.environ, {}, clear=True)  # Ensure env var is not set
        param_name_with_default = "assignee"  # Has default "@me"
        expected_default = TOOL_PARAM_CONFIG[TEST_CAPABILITY][param_name_with_default][
            "default"
        ]

        # When
        result = resolve_param(TEST_CAPABILITY, param_name_with_default, runtime_val)

        # Then
        assert result == expected_default

    def test_uses_int_default(self, mocker: "MockerFixture") -> None:
        """Test resolve_param correctly uses integer default from config.
        
        Given: A runtime value of None with no environment variable set
        When: resolve_param is called for a parameter with an integer default
        Then: The integer default value should be returned
        """
        # Given
        runtime_val = None
        mocker.patch.dict(os.environ, {}, clear=True)  # Ensure env var is not set
        param_name_with_default = "limit"  # Has default 30
        expected_default = TOOL_PARAM_CONFIG[TEST_CAPABILITY][param_name_with_default][
            "default"
        ]

        # When
        result = resolve_param(TEST_CAPABILITY, param_name_with_default, runtime_val)

        # Then
        assert result == expected_default
        assert isinstance(result, int)

    def test_uses_none_default(self, mocker: "MockerFixture") -> None:
        """Test resolve_param correctly uses None default from config.
        
        Given: A runtime value of None with no environment variable set
        When: resolve_param is called for a parameter with a None default
        Then: None should be returned
        """
        # Given
        runtime_val = None
        mocker.patch.dict(os.environ, {}, clear=True)  # Ensure env var is not set
        param_name_with_none_default = "project"  # Has default None
        expected_default = TOOL_PARAM_CONFIG[TEST_CAPABILITY][param_name_with_none_default][
            "default"
        ]
        assert expected_default is None  # Verify assumption about config

        # When
        result = resolve_param(TEST_CAPABILITY, param_name_with_none_default, runtime_val)

        # Then
        assert result is None

    def test_uses_list_default(self, mocker: "MockerFixture") -> None:
        """Test resolve_param correctly uses list default from config.
        
        Given: A runtime value of None with no environment variable set
        When: resolve_param is called for a parameter with a list default
        Then: The list default value should be returned
        """
        # Given
        runtime_val = None
        mocker.patch.dict(os.environ, {}, clear=True)  # Ensure env var is not set
        # Temporarily add a list default to the config for testing this scenario
        test_list_param = "test_list_default"
        default_list_value = ["default1", "default2"]
        original_config = TOOL_PARAM_CONFIG.get(TEST_CAPABILITY, {}).get(test_list_param)
        if TEST_CAPABILITY not in TOOL_PARAM_CONFIG:
            TOOL_PARAM_CONFIG[TEST_CAPABILITY] = {}
        TOOL_PARAM_CONFIG[TEST_CAPABILITY][test_list_param] = {
            "env_var": None,
            "default": default_list_value,
            "type": "list",
        }

        # When
        result = resolve_param(TEST_CAPABILITY, test_list_param, runtime_val)

        # Then
        assert result == default_list_value
        assert isinstance(result, list)

        # Cleanup: Restore original config state
        if original_config:
            TOOL_PARAM_CONFIG[TEST_CAPABILITY][test_list_param] = original_config
        else:
            del TOOL_PARAM_CONFIG[TEST_CAPABILITY][test_list_param]
        if not TOOL_PARAM_CONFIG[TEST_CAPABILITY]:  # Remove capability if it became empty
            del TOOL_PARAM_CONFIG[TEST_CAPABILITY]


class TestRunGhCommand:
    """Tests for the run_gh_command utility function."""

    def test_success_json_output(self, mocker: "MockerFixture") -> None:
        """Test run_gh_command successfully parses JSON output.
        
        Given: A GitHub command with JSON output flag
        When: run_gh_command is called and the command succeeds
        Then: The JSON output should be parsed and returned as a dictionary
        """
        # Given
        mocker.patch.dict(os.environ, {"GH_TOKEN": MOCK_TOKEN}, clear=True)
        mock_process = MagicMock()
        mock_process.stdout = '{"key": "value", "num": 1}'
        mock_process.stderr = ""
        mock_process.returncode = 0
        mock_subprocess_run = mocker.patch("subprocess.run", return_value=mock_process)

        # When
        result = run_gh_command(TEST_COMMAND_ARGS_JSON)

        # Then
        mock_subprocess_run.assert_called_once()
        assert isinstance(result, dict)
        assert result == {"key": "value", "num": 1}

    def test_success_string_output(self, mocker: "MockerFixture") -> None:
        """Test run_gh_command returns raw string output when not JSON.
        
        Given: A GitHub command without JSON output flag
        When: run_gh_command is called and the command succeeds
        Then: The raw string output should be returned
        """
        # Given
        mocker.patch.dict(os.environ, {"GH_TOKEN": MOCK_TOKEN}, clear=True)
        mock_process = MagicMock()
        mock_process.stdout = "https://github.com/owner/repo/issues/1"
        mock_process.stderr = ""
        mock_process.returncode = 0
        mock_subprocess_run = mocker.patch("subprocess.run", return_value=mock_process)

        # When
        result = run_gh_command(TEST_COMMAND_ARGS)

        # Then
        mock_subprocess_run.assert_called_once()
        assert isinstance(result, str)
        assert result == "https://github.com/owner/repo/issues/1"

    def test_success_json_flag_but_non_json_output(self, mocker: "MockerFixture") -> None:
        """Test run_gh_command handles non-JSON output when JSON was expected.
        
        Given: A GitHub command with JSON output flag but non-JSON response
        When: run_gh_command is called and the command succeeds
        Then: An error dictionary with the raw output should be returned
        """
        # Given
        mocker.patch.dict(os.environ, {"GH_TOKEN": MOCK_TOKEN}, clear=True)
        raw_output = "This is not JSON"
        mock_process = MagicMock()
        mock_process.stdout = raw_output
        mock_process.stderr = ""
        mock_process.returncode = 0
        mock_subprocess_run = mocker.patch("subprocess.run", return_value=mock_process)
        mock_print = mocker.patch("builtins.print")  # Capture the mock object

        # When
        result = run_gh_command(TEST_COMMAND_ARGS_JSON)

        # Then
        mock_subprocess_run.assert_called_once()
        assert result == {
            "error": "Expected JSON output but received non-JSON string",
            "raw": raw_output,
        }
        # Check that the print warning about decode failure happened
        found_warning = False
        for call_args in mock_print.call_args_list:
            args, kwargs = call_args
            if args and "Warning: Failed to parse JSON output" in args[0]:
                found_warning = True
                break
        assert found_warning, "Expected 'Failed to parse JSON output' warning not printed"

    def test_called_process_error(self, mocker: "MockerFixture") -> None:
        """Test run_gh_command handles CalledProcessError from subprocess.
        
        Given: A GitHub command that raises a CalledProcessError
        When: run_gh_command is called
        Then: An error dictionary with details should be returned
        """
        # Given
        mocker.patch.dict(os.environ, {"GH_TOKEN": MOCK_TOKEN}, clear=True)
        error_stderr = "gh: command failed"
        # Simulate CalledProcessError
        mock_subprocess_run = mocker.patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(
                returncode=1, cmd=["gh"] + TEST_COMMAND_ARGS, stderr=error_stderr
            ),
        )
        mock_print = mocker.patch("builtins.print")  # To check error print

        # When
        result = run_gh_command(TEST_COMMAND_ARGS)

        # Then
        mock_subprocess_run.assert_called_once()
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "Subprocess execution error"

    def test_file_not_found_error(self, mocker: "MockerFixture") -> None:
        """Test run_gh_command handles FileNotFoundError (gh not installed/found).
        
        Given: A GitHub command when the gh CLI is not installed or not in PATH
        When: run_gh_command is called
        Then: An error dictionary should be returned indicating the command was not found
        """
        # Given
        mocker.patch.dict(os.environ, {"GH_TOKEN": MOCK_TOKEN}, clear=True)
        # Capture the mock object returned by patch
        mock_subprocess_run = mocker.patch("subprocess.run", side_effect=FileNotFoundError)
        mocker.patch("builtins.print")  # To check error print

        # When
        result = run_gh_command(TEST_COMMAND_ARGS)

        # Then
        mock_subprocess_run.assert_called_once()
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "Command not found"

    def test_missing_token(self, mocker: "MockerFixture") -> None:
        """Test run_gh_command returns error if GitHub token is missing.
        
        Given: No GitHub token is set in the environment
        When: run_gh_command is called
        Then: An error dictionary should be returned without calling subprocess.run
        """
        # Given
        mocker.patch.dict(os.environ, {}, clear=True)  # Ensure token is not set
        mock_subprocess_run = mocker.patch("subprocess.run")  # Should not be called

        # When
        result = run_gh_command(TEST_COMMAND_ARGS)

        # Then
        mock_subprocess_run.assert_not_called()
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "GitHub token not found. Set GITHUB_TOKEN or GH_TOKEN environment variable."

    def test_handles_unexpected_exception(self, mocker: "MockerFixture") -> None:
        """Test run_gh_command handles unexpected exceptions during subprocess call.
        
        Given: A GitHub command that raises an unexpected exception
        When: run_gh_command is called
        Then: An error dictionary with the exception details should be returned
        """
        # Given
        mocker.patch.dict(os.environ, {"GH_TOKEN": MOCK_TOKEN}, clear=True)
        error_message = "Something completely unexpected happened"
        mock_subprocess_run = mocker.patch(
            "subprocess.run", side_effect=Exception(error_message)
        )
        mock_print = mocker.patch("builtins.print")

        # When
        result = run_gh_command(TEST_COMMAND_ARGS)

        # Then
        mock_subprocess_run.assert_called_once()
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "Unexpected execution error"
        assert result["details"] == error_message
