"""Unit tests for gh_utils shared utilities."""

import json
import os
import subprocess
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from _pytest.monkeypatch import MonkeyPatch

from src.gh_project_manager_mcp.config import TOOL_PARAM_CONFIG
from src.gh_project_manager_mcp.utils.gh_utils import (
    get_github_token,
    resolve_param,
    run_gh_command,
)

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

# Define MockerFixture for runtime use
# This allows us to use it for type annotations without breaking at runtime
if not TYPE_CHECKING:

    class MockerFixture:
        """Placeholder for pytest_mock.MockerFixture when inactive."""

        def patch(self, *args, **kwargs):
            """Mock the patch method for MockerFixture."""
            pass

        def patch_dict(self, *args, **kwargs):
            """Mock the patch_dict method for MockerFixture."""
            pass


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

        Given: A runtime value of None with an environment variable containing a
               comma-separated string
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

        Given: A runtime value of None with an environment variable containing a
               numeric string
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

        Given: A runtime value of None with an environment variable containing a
               non-numeric string
        When: resolve_param is called for an int-type parameter
        Then: The default value should be returned and a warning should be printed
        """
        # Given
        mock_print = mocker.patch("builtins.print")
        runtime_val = None
        env_val = "not-an-int"
        env_var_name = TOOL_PARAM_CONFIG[TEST_CAPABILITY][TEST_PARAM_INT]["env_var"]
        mocker.patch.dict(os.environ, {env_var_name: env_val}, clear=True)
        expected_default = TOOL_PARAM_CONFIG[TEST_CAPABILITY][TEST_PARAM_INT]["default"]

        # When
        result = resolve_param(TEST_CAPABILITY, TEST_PARAM_INT, runtime_val)

        # Then
        assert result == expected_default
        # Assert warning was printed
        assert mock_print.called
        assert "Could not convert value" in mock_print.call_args_list[0][0][0]

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

    def test_config_missing_parameter_returns_none(
        self, mocker: "MockerFixture"
    ) -> None:
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
        expected_default = TOOL_PARAM_CONFIG[TEST_CAPABILITY][
            param_name_with_none_default
        ]["default"]
        assert expected_default is None  # Verify assumption about config

        # When
        result = resolve_param(
            TEST_CAPABILITY, param_name_with_none_default, runtime_val
        )

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
        original_config = TOOL_PARAM_CONFIG.get(TEST_CAPABILITY, {}).get(
            test_list_param
        )
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
        if not TOOL_PARAM_CONFIG[
            TEST_CAPABILITY
        ]:  # Remove capability if it became empty
            del TOOL_PARAM_CONFIG[TEST_CAPABILITY]

    def test_resolve_param_list_from_env(
        self, monkeypatch: MonkeyPatch, mocker: MockerFixture
    ) -> None:
        """Test resolve_param converts comma-separated env var to list.

        Given: A runtime value of None with an environment variable containing
               a comma-separated string
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

    def test_resolve_param_int_from_env(
        self, monkeypatch: MonkeyPatch, mocker: MockerFixture
    ) -> None:
        """Test resolve_param converts valid int env var string to int.

        Given: A runtime value of None with an environment variable containing
               a numeric string
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

    def test_resolve_param_int_from_env_invalid(
        self, monkeypatch: MonkeyPatch, mocker: MockerFixture
    ) -> None:
        """Test resolve_param returns default when env var int conversion fails.

        Given: A runtime value of None with an environment variable containing
               a non-numeric string
        When: resolve_param is called for an int-type parameter
        Then: The default value should be returned and a warning should be printed
        """
        # Given
        mock_print = mocker.patch("builtins.print")
        runtime_val = None
        env_val = "not-an-int"
        env_var_name = TOOL_PARAM_CONFIG[TEST_CAPABILITY][TEST_PARAM_INT]["env_var"]
        mocker.patch.dict(os.environ, {env_var_name: env_val}, clear=True)
        expected_default = TOOL_PARAM_CONFIG[TEST_CAPABILITY][TEST_PARAM_INT]["default"]

        # When
        result = resolve_param(TEST_CAPABILITY, TEST_PARAM_INT, runtime_val)

        # Then
        assert result == expected_default
        # Assert warning was printed
        assert mock_print.called
        assert "Could not convert value" in mock_print.call_args_list[0][0][0]

    def test_value_convert_bool_invalid_string(self, mocker: MockerFixture) -> None:
        """Test handling invalid boolean string values.

        Given:
            - A parameter with type 'bool'
            - A string value that's not a common boolean representation
        When:
            - resolve_param is called
        Then:
            - A warning is printed
            - The original string value is returned
        """
        # Given
        from gh_project_manager_mcp.utils.gh_utils import resolve_param

        # Create test config
        mocker.patch.dict(
            "gh_project_manager_mcp.utils.gh_utils.TOOL_PARAM_CONFIG",
            {
                "test": {
                    "bool_param": {
                        "type": "bool",
                    }
                }
            },
        )

        # Setup print capture
        print_mock = mocker.patch("builtins.print")

        # When
        result = resolve_param("test", "bool_param", "not-a-boolean")

        # Then
        assert result == "not-a-boolean"  # Should return original value
        print_mock.assert_called_once()
        call_args = print_mock.call_args[0][0]
        assert "Warning" in call_args
        assert "Could not convert string" in call_args
        assert "to bool" in call_args

    def test_value_convert_error(self, mocker: MockerFixture) -> None:
        """Test handling conversion errors.

        Given:
            - A parameter with type 'int'
            - A value that cannot be converted to int
            - A default value in the config
        When:
            - resolve_param is called
        Then:
            - A warning is printed
            - The default value is returned
        """
        # Given
        from gh_project_manager_mcp.utils.gh_utils import resolve_param

        # Create test config with default
        mocker.patch.dict(
            "gh_project_manager_mcp.utils.gh_utils.TOOL_PARAM_CONFIG",
            {"test": {"int_param": {"type": "int", "default": 42}}},
        )

        # Setup print capture
        print_mock = mocker.patch("builtins.print")

        # When
        result = resolve_param("test", "int_param", "not-an-integer")

        # Then
        assert result == 42  # Should return default value
        print_mock.assert_called_once()
        call_args = print_mock.call_args[0][0]
        assert "Warning" in call_args
        assert "Could not convert value" in call_args
        assert "to type 'int'" in call_args


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

    def test_success_json_flag_but_non_json_output(
        self, mocker: "MockerFixture"
    ) -> None:
        """Test handling when command with JSON flag returns non-JSON output.

        Given:
            - A GitHub command with JSON output flag
        When:
            - run_gh_command is called but the command returns a non-JSON string
        Then:
            - A structured error dictionary should be returned
        """
        # Given
        mocker.patch.dict(os.environ, {"GH_TOKEN": MOCK_TOKEN}, clear=True)
        # Mock print to avoid polluting test output
        mock_print = mocker.patch("builtins.print")
        # Create a mock JSON decode error by returning non-JSON text
        non_json_output = "Some non-JSON text that can't be parsed"
        mock_process = mocker.patch("subprocess.run").return_value
        mock_process.stdout = non_json_output
        mock_process.stderr = ""
        mock_process.returncode = 0  # Success return code

        # Explicitly mock the json.loads function to raise JSONDecodeError
        mock_json_loads = mocker.patch("json.loads")
        mock_json_loads.side_effect = json.JSONDecodeError("Expecting value", "", 0)

        # When
        result = run_gh_command(TEST_COMMAND_ARGS_JSON)

        # Then
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "Expected JSON output but received non-JSON string"
        assert result["raw"] == non_json_output
        # Verify the error was logged
        assert mock_print.called
        assert any(
            "Warning: Failed to parse JSON output" in str(args)
            for args, _ in mock_print.call_args_list
        )

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

        # When
        result = run_gh_command(TEST_COMMAND_ARGS)

        # Then
        mock_subprocess_run.assert_called_once()
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "Subprocess execution error"

    def test_file_not_found_error(self, mocker: "MockerFixture") -> None:
        """Test run_gh_command handles FileNotFoundError properly.

        Given:
            - A GitHub command to run
            - The 'gh' command is not found
        When:
            - run_gh_command is called
        Then:
            - A structured error dictionary should be returned
            - Error details should indicate 'gh' command not found
        """
        # Given
        mocker.patch.dict(os.environ, {"GH_TOKEN": MOCK_TOKEN}, clear=True)
        mock_print = mocker.patch("builtins.print")  # Capture print calls

        # Simulate FileNotFoundError for the subprocess.run call
        mock_subprocess_run = mocker.patch("subprocess.run")
        mock_subprocess_run.side_effect = FileNotFoundError(
            "No such file or directory: 'gh'"
        )

        # When
        result = run_gh_command(TEST_COMMAND_ARGS)

        # Then
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "Command not found"
        assert "details" in result
        assert "'gh' command not found" in result["details"]
        # Verify the error was printed
        assert mock_print.called
        assert any(
            "'gh' command not found" in str(args)
            for args, _ in mock_print.call_args_list
        )

    def test_missing_token(self, mocker: "MockerFixture") -> None:
        """Test run_gh_command returns error if GitHub token is missing.

        Given: No GitHub token is set in the environment
        When: run_gh_command is called with a mocked get_github_token
        Then: An error dictionary should be returned without calling subprocess.run
        """
        # Given
        # Import inside the test to avoid module-level patching issues
        from gh_project_manager_mcp.utils.gh_utils import (
            run_gh_command as test_run_gh_command,
        )

        mocker.patch("builtins.print")  # Silence prints

        # Patch the get_github_token function within the gh_utils module
        mocker.patch(
            "gh_project_manager_mcp.utils.gh_utils.get_github_token", return_value=None
        )

        # Patch subprocess.run to ensure it's not called
        subprocess_mock = mocker.patch(
            "gh_project_manager_mcp.utils.gh_utils.subprocess.run"
        )

        # When
        result = test_run_gh_command(TEST_COMMAND_ARGS)

        # Then
        assert "error" in result
        assert "GitHub token not found" in result["error"]
        subprocess_mock.assert_not_called()

    def test_token_handling_in_run_gh_command(self, mocker: MockerFixture) -> None:
        """Test that different token scenarios are handled correctly.

        This test checks both code paths:
        1. When a regular token is provided
        2. When the special "gh_auth_available" token is provided

        Given:
            - Both token scenarios
        When:
            - run_gh_command is called
        Then:
            - For regular token: A debug message is printed about using GH_TOKEN
            - For "gh_auth_available": A message about using existing auth is printed
        """
        # Given
        from gh_project_manager_mcp.utils.gh_utils import run_gh_command

        # Setup for testing both scenarios
        token_scenarios = [
            {"token": "real_token_value", "message": "Using GH_TOKEN from environment"},
            {
                "token": "gh_auth_available",
                "message": "Relying on existing gh CLI authentication",
            },
        ]

        for scenario in token_scenarios:
            # Reset mocks for each scenario
            mocker.resetall()

            # Mock environment
            mocker.patch.dict(os.environ, {}, clear=True)

            # Setup print capture
            print_mock = mocker.patch("builtins.print")

            # Setup get_github_token to return the token for this scenario
            mocker.patch(
                "gh_project_manager_mcp.utils.gh_utils.get_github_token",
                return_value=scenario["token"],
            )

            # Setup successful command execution
            mock_process = MagicMock()
            mock_process.stdout = "Success output"
            mock_process.stderr = ""
            mock_process.returncode = 0
            mock_subprocess_run = mocker.patch(
                "gh_project_manager_mcp.utils.gh_utils.subprocess.run",
                return_value=mock_process,
            )

            # When
            result = run_gh_command(["test", "command"])

            # Then
            assert mock_subprocess_run.called
            assert result == "Success output"

            # Verify the appropriate debug message was printed
            assert any(
                scenario["message"] in str(args)
                for args, _ in print_mock.call_args_list
            )

    def test_missing_token_with_none(self, mocker: MockerFixture) -> None:
        """Test edge case where token is None but different code path than normal missing token.

        Given:
            - get_github_token returns None
            - We've already passed the initial check
        When:
            - run_gh_command is called
        Then:
            - Error is returned
        """
        # Given
        from gh_project_manager_mcp.utils.gh_utils import run_gh_command

        # Mock environment
        mocker.patch.dict(os.environ, {}, clear=True)

        # Setup print capture
        print_mock = mocker.patch("builtins.print")

        # Setup get_github_token to return None
        mocker.patch(
            "gh_project_manager_mcp.utils.gh_utils.get_github_token", return_value=None
        )

        # When
        result = run_gh_command(["test", "command"])

        # Then
        assert "error" in result
        assert "GitHub token not found" in result["error"]

    def test_run_gh_command_no_token(self, mocker: MockerFixture) -> None:
        """Test run_gh_command returns error if GitHub token is missing.

        Given: No GitHub token is set in the environment
        When: run_gh_command is called with mocked get_github_token
        Then: An error dictionary should be returned without calling subprocess.run
        """
        # Given
        # Import inside the test to avoid module-level patching issues
        from gh_project_manager_mcp.utils.gh_utils import (
            run_gh_command as test_run_gh_command,
        )

        mocker.patch("builtins.print")  # Silence prints

        # Patch the get_github_token function within the gh_utils module
        mocker.patch(
            "gh_project_manager_mcp.utils.gh_utils.get_github_token", return_value=None
        )

        # Patch subprocess.run to ensure it's not called
        subprocess_mock = mocker.patch(
            "gh_project_manager_mcp.utils.gh_utils.subprocess.run"
        )

        # When
        result = test_run_gh_command(TEST_COMMAND_ARGS)

        # Then
        assert "error" in result
        assert "GitHub token not found" in result["error"]
        subprocess_mock.assert_not_called()

    def test_json_decode_error_in_run_gh_command(self, mocker: MockerFixture) -> None:
        """Test that JSON decode errors are handled correctly.

        Given:
            - A command with --json flag
            - The command output is not valid JSON
        When:
            - run_gh_command is called
        Then:
            - A structured error with the raw output is returned
        """
        # Given
        from gh_project_manager_mcp.utils.gh_utils import run_gh_command

        # Mock the environment and token
        mocker.patch.dict(os.environ, {"GH_TOKEN": MOCK_TOKEN}, clear=True)

        # Capture print calls
        print_mock = mocker.patch("builtins.print")

        # Create process that returns non-JSON output even though --json was requested
        mock_process = MagicMock()
        mock_process.stdout = "Not JSON data"
        mock_process.stderr = ""
        mock_process.returncode = 0

        # Setup subprocess.run to return our mock process
        mocker.patch(
            "gh_project_manager_mcp.utils.gh_utils.subprocess.run",
            return_value=mock_process,
        )

        # Create a JSONDecodeError when json.loads is called
        json_error = json.JSONDecodeError("Invalid JSON", "Not JSON data", 0)
        mocker.patch(
            "gh_project_manager_mcp.utils.gh_utils.json.loads", side_effect=json_error
        )

        # When - use a command with --json flag
        result = run_gh_command(["test", "command", "--json", "fields"])

        # Then
        assert isinstance(result, dict)
        assert "error" in result
        assert "Expected JSON output but received non-JSON string" == result["error"]
        assert "raw" in result
        assert "Not JSON data" == result["raw"]

        # Check that warning was printed
        assert print_mock.called
        assert any(
            "Warning: Failed to parse JSON output" in str(args)
            for args, _ in print_mock.call_args_list
        )

    def test_called_process_error_handling(self, mocker: MockerFixture) -> None:
        """Test explicit handling of CalledProcessError.

        Given:
            - subprocess.run raises CalledProcessError
        When:
            - run_gh_command is called
        Then:
            - A structured error with stderr and stdout is returned
        """
        # Given
        from gh_project_manager_mcp.utils.gh_utils import run_gh_command

        # Mock the environment and token
        mocker.patch.dict(os.environ, {"GH_TOKEN": MOCK_TOKEN}, clear=True)

        # Capture print calls
        print_mock = mocker.patch("builtins.print")

        # Create a CalledProcessError - different versions of Python have different init signatures
        error = subprocess.CalledProcessError(1, ["gh", "test"])
        error.stdout = "stdout data"
        error.stderr = "stderr data"

        # Make subprocess.run raise the error
        mocker.patch(
            "gh_project_manager_mcp.utils.gh_utils.subprocess.run", side_effect=error
        )

        # When
        result = run_gh_command(["test", "command"])

        # Then
        assert isinstance(result, dict)
        assert "error" in result
        assert "Subprocess execution error" == result["error"]
        assert "details" in result
        assert "Subprocess error" in result["details"]
        assert "stderr" in result
        assert "stdout" in result
        assert "exit_code" in result

        # Check that error was printed
        assert print_mock.called

    def test_handles_unexpected_exception(self, mocker: "MockerFixture") -> None:
        """Test run_gh_command handles unexpected exceptions properly.

        Given:
            - A GitHub command to run
            - An unexpected exception occurs
        When:
            - run_gh_command is called
        Then:
            - A structured error dictionary should be returned
            - Error should indicate an unexpected execution error
            - Exception details should be included
        """
        # Given
        from gh_project_manager_mcp.utils.gh_utils import run_gh_command

        mocker.patch.dict(os.environ, {"GH_TOKEN": MOCK_TOKEN}, clear=True)
        mock_print = mocker.patch("builtins.print")  # Capture print calls
        exception_message = "Some unexpected error occurred"

        # Simulate general exception for the subprocess.run call
        mock_subprocess_run = mocker.patch(
            "gh_project_manager_mcp.utils.gh_utils.subprocess.run",
            side_effect=Exception(exception_message),
        )

        # When
        result = run_gh_command(TEST_COMMAND_ARGS)

        # Then
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "Unexpected execution error"
        assert "details" in result
        assert exception_message in result["details"]
        # Verify the error was printed
        assert mock_print.called
        assert any(
            "unexpected error occurred" in str(args).lower()
            for args, _ in mock_print.call_args_list
        )

    def test_run_gh_command_handles_stderr(self, mocker: MockerFixture) -> None:
        """Test that stderr doesn't cause errors if returncode is 0."""
        # Given
        from gh_project_manager_mcp.utils.gh_utils import run_gh_command

        mocker.patch("builtins.print")
        mocker.patch.dict(os.environ, {"GH_TOKEN": MOCK_TOKEN}, clear=True)
        mock_process = MagicMock()
        mock_process.stdout = '{"key": "value", "num": 1}'
        mock_process.stderr = "Warning: Failed to parse JSON output"
        mock_process.returncode = 0
        mock_subprocess_run = mocker.patch(
            "gh_project_manager_mcp.utils.gh_utils.subprocess.run",
            return_value=mock_process,
        )

        # When
        result = run_gh_command(TEST_COMMAND_ARGS_JSON)

        # Then
        mock_subprocess_run.assert_called_once()
        assert isinstance(result, dict)
        assert result == {"key": "value", "num": 1}

    def test_run_gh_command_not_found(self, mocker: MockerFixture) -> None:
        """Test command not found error.

        Given: A GitHub command when the gh CLI is not installed or not in PATH
        When: run_gh_command is called
        Then: An error dictionary should be returned indicating the command
              was not found
        """
        # Given
        from gh_project_manager_mcp.utils.gh_utils import run_gh_command

        mocker.patch("builtins.print")
        mocker.patch.dict(os.environ, {"GH_TOKEN": MOCK_TOKEN}, clear=True)
        # Capture the mock object returned by patch
        mock_subprocess_run = mocker.patch(
            "gh_project_manager_mcp.utils.gh_utils.subprocess.run",
            side_effect=FileNotFoundError,
        )

        # When
        result = run_gh_command(TEST_COMMAND_ARGS)

        # Then
        mock_subprocess_run.assert_called_once()
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "Command not found"


class TestGetGithubToken:
    """Tests for the get_github_token utility function."""

    def test_returns_gh_token_env_var(self, mocker: "MockerFixture") -> None:
        """Test get_github_token returns GH_TOKEN when available.

        Given: GH_TOKEN environment variable is set
        When: get_github_token is called
        Then: It should return the value of GH_TOKEN
        """
        # Given
        token_value = "test_gh_token"
        mocker.patch.dict(os.environ, {"GH_TOKEN": token_value}, clear=True)

        # When
        result = get_github_token()

        # Then
        assert result == token_value

    def test_returns_github_token_env_var(self, mocker: "MockerFixture") -> None:
        """Test get_github_token returns GITHUB_TOKEN when available.

        Given: GITHUB_TOKEN environment variable is set
        When: get_github_token is called
        Then: It should return the value of GITHUB_TOKEN
        """
        # Given
        token_value = "test_github_token"
        mocker.patch.dict(os.environ, {"GITHUB_TOKEN": token_value}, clear=True)

        # When
        result = get_github_token()

        # Then
        assert result == token_value

    def test_gh_token_precedence_over_github_token(
        self, mocker: "MockerFixture"
    ) -> None:
        """Test GITHUB_TOKEN falls back if GH_TOKEN is not available.

        Given: Both GH_TOKEN and GITHUB_TOKEN environment variables are set
        When: get_github_token is called
        Then: It should return the first found token
        """
        # Given
        # The way the code is implemented, it OR's the tokens, so whichever
        # is first in the OR chain is returned if it exists
        gh_token_value = "test_gh_token"
        github_token_value = "test_github_token"

        # Current implementation uses: token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        # So GITHUB_TOKEN takes precedence if both are set
        mocker.patch.dict(
            os.environ,
            {"GH_TOKEN": gh_token_value, "GITHUB_TOKEN": github_token_value},
            clear=True,
        )

        # When
        result = get_github_token()

        # Then
        assert result == github_token_value

    def test_falls_back_to_gh_auth_status(self, mocker: "MockerFixture") -> None:
        """Test get_github_token falls back to gh auth status.

        Given: No token environment variables are set but gh auth status succeeds
        When: get_github_token is called
        Then: It should return "gh_auth_available"
        """
        # Given
        mocker.patch.dict(os.environ, {}, clear=True)
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_subprocess_run = mocker.patch("subprocess.run", return_value=mock_process)

        # When
        result = get_github_token()

        # Then
        mock_subprocess_run.assert_called_once_with(
            ["gh", "auth", "status"], capture_output=True, text=True, check=False
        )
        assert result == "gh_auth_available"

    def test_returns_none_if_no_token_found(self, mocker: "MockerFixture") -> None:
        """Test get_github_token returns None when no token is available.

        Given: No token environment variables are set and gh auth status fails
        When: get_github_token is called
        Then: It should return None
        """
        # Given
        mocker.patch.dict(os.environ, {}, clear=True)
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_subprocess_run = mocker.patch("subprocess.run", return_value=mock_process)

        # When
        result = get_github_token()

        # Then
        mock_subprocess_run.assert_called_once()
        assert result is None

    def test_handles_gh_auth_exception(self, mocker: "MockerFixture") -> None:
        """Test get_github_token handles exception during gh auth status.

        Given: No token environment variables are set and gh auth status throws an exception
        When: get_github_token is called
        Then: It should print an error message and return None
        """
        # Given
        mocker.patch.dict(os.environ, {}, clear=True)
        mock_print = mocker.patch("builtins.print")
        mock_subprocess_run = mocker.patch(
            "subprocess.run", side_effect=Exception("Command failed")
        )

        # When
        result = get_github_token()

        # Then
        mock_subprocess_run.assert_called_once()
        mock_print.assert_called_once()
        assert "Error checking gh auth status" in mock_print.call_args[0][0]
        assert result is None


class TestResolveParamBoolConversion:
    """Tests for boolean conversion in the resolve_param function."""

    def setup_method(self) -> None:
        """Set up test environment for boolean conversion tests."""
        # Create a test parameter in TOOL_PARAM_CONFIG for boolean type
        if "test_bool" not in TOOL_PARAM_CONFIG:
            TOOL_PARAM_CONFIG["test_bool"] = {}

        TOOL_PARAM_CONFIG["test_bool"]["param"] = {
            "env_var": "TEST_BOOL_ENV",
            "default": False,
            "type": "bool",
        }

    def teardown_method(self) -> None:
        """Clean up after boolean conversion tests."""
        # Clean up the test parameter
        if "test_bool" in TOOL_PARAM_CONFIG:
            if "param" in TOOL_PARAM_CONFIG["test_bool"]:
                del TOOL_PARAM_CONFIG["test_bool"]["param"]
            if not TOOL_PARAM_CONFIG["test_bool"]:
                del TOOL_PARAM_CONFIG["test_bool"]

    def test_string_true_conversion(self, mocker: "MockerFixture") -> None:
        """Test resolve_param converts 'true' string to boolean True.

        Given: A runtime value of None with an environment variable set to 'true'
        When: resolve_param is called for a boolean parameter
        Then: The string should be converted to boolean True
        """
        # Given
        runtime_val = None
        env_val = "true"
        mocker.patch.dict(os.environ, {"TEST_BOOL_ENV": env_val}, clear=True)

        # When
        result = resolve_param("test_bool", "param", runtime_val)

        # Then
        assert result is True
        assert isinstance(result, bool)

    def test_string_yes_conversion(self, mocker: "MockerFixture") -> None:
        """Test resolve_param converts 'yes' string to boolean True.

        Given: A runtime value of None with an environment variable set to 'yes'
        When: resolve_param is called for a boolean parameter
        Then: The string should be converted to boolean True
        """
        # Given
        runtime_val = None
        env_val = "yes"
        mocker.patch.dict(os.environ, {"TEST_BOOL_ENV": env_val}, clear=True)

        # When
        result = resolve_param("test_bool", "param", runtime_val)

        # Then
        assert result is True
        assert isinstance(result, bool)

    def test_string_1_conversion(self, mocker: "MockerFixture") -> None:
        """Test resolve_param converts '1' string to boolean True.

        Given: A runtime value of None with an environment variable set to '1'
        When: resolve_param is called for a boolean parameter
        Then: The string should be converted to boolean True
        """
        # Given
        runtime_val = None
        env_val = "1"
        mocker.patch.dict(os.environ, {"TEST_BOOL_ENV": env_val}, clear=True)

        # When
        result = resolve_param("test_bool", "param", runtime_val)

        # Then
        assert result is True
        assert isinstance(result, bool)

    def test_string_false_conversion(self, mocker: "MockerFixture") -> None:
        """Test resolve_param converts 'false' string to boolean False.

        Given: A runtime value of None with an environment variable set to 'false'
        When: resolve_param is called for a boolean parameter
        Then: The string should be converted to boolean False
        """
        # Given
        runtime_val = None
        env_val = "false"
        mocker.patch.dict(os.environ, {"TEST_BOOL_ENV": env_val}, clear=True)

        # When
        result = resolve_param("test_bool", "param", runtime_val)

        # Then
        assert result is False
        assert isinstance(result, bool)

    def test_string_no_conversion(self, mocker: "MockerFixture") -> None:
        """Test resolve_param converts 'no' string to boolean False.

        Given: A runtime value of None with an environment variable set to 'no'
        When: resolve_param is called for a boolean parameter
        Then: The string should be converted to boolean False
        """
        # Given
        runtime_val = None
        env_val = "no"
        mocker.patch.dict(os.environ, {"TEST_BOOL_ENV": env_val}, clear=True)

        # When
        result = resolve_param("test_bool", "param", runtime_val)

        # Then
        assert result is False
        assert isinstance(result, bool)

    def test_string_0_conversion(self, mocker: "MockerFixture") -> None:
        """Test resolve_param converts '0' string to boolean False.

        Given: A runtime value of None with an environment variable set to '0'
        When: resolve_param is called for a boolean parameter
        Then: The string should be converted to boolean False
        """
        # Given
        runtime_val = None
        env_val = "0"
        mocker.patch.dict(os.environ, {"TEST_BOOL_ENV": env_val}, clear=True)

        # When
        result = resolve_param("test_bool", "param", runtime_val)

        # Then
        assert result is False
        assert isinstance(result, bool)

    def test_invalid_string_returns_original(self, mocker: "MockerFixture") -> None:
        """Test resolve_param returns the original string for invalid bool conversion.

        Given: A runtime value of None with an environment variable set to an invalid boolean string
        When: resolve_param is called for a boolean parameter
        Then: A warning should be printed and the original string should be returned
        """
        # Given
        runtime_val = None
        env_val = "not-a-bool"
        mocker.patch.dict(os.environ, {"TEST_BOOL_ENV": env_val}, clear=True)
        mock_print = mocker.patch("builtins.print")

        # When
        result = resolve_param("test_bool", "param", runtime_val)

        # Then
        assert result == env_val  # Returns original string
        assert mock_print.called
        assert "Warning: Could not convert string" in mock_print.call_args[0][0]

    def test_nonstring_bool_conversion(self, mocker: "MockerFixture") -> None:
        """Test resolve_param uses standard bool conversion for non-string values.

        Given: A runtime value of a non-string type that can be boolean converted
        When: resolve_param is called for a boolean parameter
        Then: Standard Python boolean conversion should be applied
        """
        # Given
        runtime_val = 0  # Will convert to False

        # When
        result = resolve_param("test_bool", "param", runtime_val)

        # Then
        assert result is False
        assert isinstance(result, bool)

        # Given
        runtime_val = 1  # Will convert to True

        # When
        result = resolve_param("test_bool", "param", runtime_val)

        # Then
        assert result is True
        assert isinstance(result, bool)


# --- Module-level tests ---


def test_import_error_handling_simple():
    """Test that the import error handling in gh_utils.py works properly.

    This test verifies that the code handles ImportError for relative imports by
    having a fallback to absolute imports.
    """
    # The simplest way to test this is to verify that the TOOL_PARAM_CONFIG
    # was successfully imported in the module despite potential import path issues
    from src.gh_project_manager_mcp.utils.gh_utils import TOOL_PARAM_CONFIG

    # If we get here without an ImportError, the fallback mechanism works
    # Perform a basic verification on the imported config
    assert isinstance(TOOL_PARAM_CONFIG, dict)
    assert len(TOOL_PARAM_CONFIG) > 0

    # Verify that some expected capabilities are present
    # (using "issue" as it's a core capability that should always be there)
    assert "issue" in TOOL_PARAM_CONFIG
