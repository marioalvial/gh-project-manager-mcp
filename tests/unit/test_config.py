# tests/test_config.py
"""Tests for the TOOL_PARAM_CONFIG structure and completeness."""

import re
from pathlib import Path
from typing import List, Set, Tuple

import pytest
from gh_project_manager_mcp.config import TOOL_PARAM_CONFIG


@pytest.fixture
def resolve_param_calls() -> List[Tuple[str, str]]:
    """Find all resolve_param calls in tool implementation files.

    Returns
    -------
        List[Tuple[str, str]]: A list of tuples, each containing
                                (capability_str,
                                 param_name_str).

    """
    tools_dir = Path("src/gh_project_manager_mcp/tools")
    checked_params: Set[Tuple[str, str]] = set()

    for tool_file in tools_dir.glob("*.py"):
        if tool_file.name == "__init__.py":
            continue

        file_content = tool_file.read_text()
        found_params = _find_resolve_param_calls(file_content)
        checked_params.update(found_params)

    return list(checked_params)


def _find_resolve_param_calls(file_content: str) -> List[Tuple[str, str]]:
    """Find all calls to resolve_param in the given file content.

    Args:
    ----
        file_content: The string content of the Python file.

    Returns:
    -------
        A list of tuples, each containing (capability_str, param_name_str).

    """
    # Regex to find resolve_param('capability', 'param_name', ...)
    # It captures the first two string arguments (capability and param_name)
    pattern = re.compile(
        r"""
        resolve_param\(\s*            # Match 'resolve_param(' and optional whitespace
        ['"]([^\'"]+)['"]\s*,\s*      # Capture the first string literal (capability)
        ['"]([^\'"]+)['"]             # Capture the second string literal (param_name)
        # We don't need to match the rest of the arguments
    """,
        re.VERBOSE,
    )
    matches = pattern.findall(file_content)
    # Return list of (capability, param_name) tuples
    return [(cap.strip(), name.strip()) for cap, name in matches]


def get_all_parameter_names() -> List[Tuple[str, str]]:
    """Get a flat list of all (capability, param_name) tuples.

    Returns
    -------
        List[Tuple[str, str]]: A list of tuples, each containing
                                (capability_str, param_name_str).

    """
    # ... (logic) ...


class TestConfigCompleteness:
    """Tests for verifying the completeness of configuration definitions."""

    def test_tool_param_config_completeness(
        self, resolve_param_calls: List[Tuple[str, str]]
    ) -> None:
        """Verify parameters used with resolve_param have 'type' in config.

        Given: All resolve_param calls collected from tool implementation files
        When: Checking each capability/parameter combination against TOOL_PARAM_CONFIG
        Then: Every parameter present in TOOL_PARAM_CONFIG should have a 'type' key
        """
        # Given
        missing_params: List[str] = []

        # When
        for capability, param_name in resolve_param_calls:
            capability_config = TOOL_PARAM_CONFIG.get(capability)
            if capability_config is not None:
                param_config = capability_config.get(param_name)
                if param_config is not None:
                    # Only check for 'type' if the param exists in the config
                    if "type" not in param_config:
                        missing_params.append(
                            f"""Parameter '{param_name}' under capability """
                            f"'{capability}' is missing the 'type' key "
                            f"in TOOL_PARAM_CONFIG."
                            ""
                        )
            # No error if capability or param_name is not found in config,
            # as resolve_param handles this.

        # Then
        assert not missing_params, (
            "Parameters found in TOOL_PARAM_CONFIG are missing the 'type' key:\n"
            + "\n".join(missing_params)
        )

    def test_tool_param_config_structure(self) -> None:
        """Verify TOOL_PARAM_CONFIG has the expected structure.

        Given: The TOOL_PARAM_CONFIG dictionary
        When: Examining its structure
        Then: Each capability should have parameters
              Each parameter should have at least a 'type' key
        """
        # Given
        invalid_entries: List[str] = []

        # When
        for capability, params in TOOL_PARAM_CONFIG.items():
            if not isinstance(params, dict):
                invalid_entries.append(f"Capability '{capability}' is not a dictionary")
                continue

            for param_name, param_config in params.items():
                if not isinstance(param_config, dict):
                    invalid_entries.append(
                        f"Parameter '{param_name}' in capability "
                        f"'{capability}' is not a dictionary"
                    )
                    continue

                if "type" not in param_config:
                    invalid_entries.append(
                        f"Parameter '{param_name}' in capability "
                        f"'{capability}' is missing 'type' key"
                    )

                # Validate type value is one of the expected types
                if param_config.get("type") not in ["str", "int", "list", "bool"]:
                    invalid_entries.append(
                        f"Parameter '{param_name}' in capability "
                        f"'{capability}' has invalid type: "
                        f"{param_config.get('type')}"
                    )

        # Then
        assert not invalid_entries, (
            "TOOL_PARAM_CONFIG has structure issues:\n" + "\n".join(invalid_entries)
        )

    def test_all_parameters_have_type_key(self) -> None:
        """Verify every parameter entry in TOOL_PARAM_CONFIG has a 'type' key."""
        missing_params = []
        for capability, params in TOOL_PARAM_CONFIG.items():
            for param_name, param_config in params.items():
                if isinstance(param_config, dict):
                    if "type" not in param_config:
                        missing_params.append(
                            f"""Parameter '{param_name}' under capability """
                            f"'{capability}' is missing the 'type' key in "
                            f"TOOL_PARAM_CONFIG."
                            ""
                        )
                else:
                    missing_params.append(
                        f"Entry for '{param_name}' under '{capability}' is not a dict."
                    )

        assert not missing_params, "\n".join(missing_params)

    def test_parameter_types_are_valid(self) -> None:
        """Verify that all 'type' keys have valid string values."""
        invalid_entries = []
        for capability, params in TOOL_PARAM_CONFIG.items():
            for param_name, param_config in params.items():
                if not isinstance(param_config, dict):
                    invalid_entries.append(
                        f"Parameter '{param_name}' in capability "
                        f"'{capability}' is not a dictionary"
                    )
                    continue
                if "type" not in param_config:
                    invalid_entries.append(
                        f"Parameter '{param_name}' in capability "
                        f"'{capability}' is missing 'type' key"
                    )
                    continue
                # Check if the type value is one of the allowed strings
                if param_config.get("type") not in ["str", "int", "list", "bool"]:
                    invalid_entries.append(
                        f"Parameter '{param_name}' in capability "
                        f"'{capability}' has invalid type: "
                        f"{param_config.get('type')}"
                    )

        assert not invalid_entries, "\n".join(invalid_entries)


class TestGetGithubToken:
    """Tests for the get_github_token function in config.py."""

    def test_get_github_token_returns_env_var(self, monkeypatch) -> None:
        """Test that get_github_token returns the GH_TOKEN environment variable.

        Given:
            - GH_TOKEN is set in the environment
        When:
            - get_github_token() is called
        Then:
            - It returns the value of GH_TOKEN environment variable
        """
        # Import get_github_token here to avoid circular import
        from gh_project_manager_mcp.config import get_github_token

        # Given
        test_token = "test_gh_token"
        monkeypatch.setenv("GH_TOKEN", test_token)

        # When
        result = get_github_token()

        # Then
        assert result == test_token

    def test_get_github_token_github_token_env_var(self, monkeypatch) -> None:
        """Test that get_github_token returns the GITHUB_TOKEN environment variable.

        Given:
            - GH_TOKEN is not set in the environment
            - GITHUB_TOKEN is set in the environment
        When:
            - get_github_token() is called
        Then:
            - It returns the value of GITHUB_TOKEN environment variable
        """
        # Import get_github_token here to avoid circular import
        from gh_project_manager_mcp.config import get_github_token

        # Given
        test_token = "test_github_token"
        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.setenv("GITHUB_TOKEN", test_token)

        # When
        result = get_github_token()

        # Then
        assert result == test_token

    def test_github_token_has_precedence(self, monkeypatch) -> None:
        """Test that GITHUB_TOKEN takes precedence over GH_TOKEN.

        Given:
            - Both GITHUB_TOKEN and GH_TOKEN are set in the environment
        When:
            - get_github_token() is called
        Then:
            - It returns the value of GITHUB_TOKEN environment variable
        """
        # Import get_github_token here to avoid circular import
        from gh_project_manager_mcp.config import get_github_token

        # Given
        github_token = "test_github_token"
        gh_token = "test_gh_token"
        monkeypatch.setenv("GITHUB_TOKEN", github_token)
        monkeypatch.setenv("GH_TOKEN", gh_token)

        # When
        result = get_github_token()

        # Then
        assert result == github_token

    def test_get_github_token_returns_none_when_not_set(self, monkeypatch) -> None:
        """Test that get_github_token returns None when GH_TOKEN is not set.

        Given:
            - GH_TOKEN is not set in the environment
            - gh auth status returns an error (not authenticated)
        When:
            - get_github_token() is called
        Then:
            - It returns None
        """
        # Import here to avoid circular import
        import subprocess

        from gh_project_manager_mcp.config import get_github_token

        # Given - clear environment variables
        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)

        # Mock subprocess.run to simulate gh auth status failure
        class MockFailedAuth:
            def __init__(self):
                self.returncode = 1  # Error - not authenticated
                self.stdout = "Not logged in"

        def mock_run(cmd, **kwargs):
            if cmd[0] == "gh" and cmd[1] == "auth" and cmd[2] == "status":
                return MockFailedAuth()
            # Should never reach here in this test
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Also patch print to avoid pollution
        monkeypatch.setattr("builtins.print", lambda *args, **kwargs: None)

        # When
        result = get_github_token()

        # Then
        assert result is None

    def test_get_github_token_falls_back_to_gh_auth(self, monkeypatch) -> None:
        """Test that get_github_token falls back to gh auth status check.

        Given:
            - GH_TOKEN is not set in the environment
            - gh auth status call is successful
        When:
            - get_github_token() is called
        Then:
            - It returns "gh_auth_available" indicating auth is available
        """
        # Access config.py directly, don't import the function
        import subprocess
        import sys

        # Given - make sure the environment variables are cleared
        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)

        # Create a mock for subprocess.run that returns success for 'gh auth status'
        class MockRunResult:
            def __init__(self):
                self.returncode = 0  # Success
                self.stdout = "Logged in to github.com"
                self.stderr = ""

        def mock_subprocess_run(cmd, **kwargs):
            if cmd[0] == "gh" and cmd[1] == "auth" and cmd[2] == "status":
                return MockRunResult()
            return subprocess.CompletedProcess(cmd, 0, "", "")

        # Apply our mocks
        monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

        # Also need to patch the print function in config
        mock_print_calls = []

        def mock_print(*args, **kwargs):
            mock_print_calls.append(args[0])

        monkeypatch.setattr("builtins.print", mock_print)

        # Reset any cached import before importing again
        if "gh_project_manager_mcp.config" in sys.modules:
            del sys.modules["gh_project_manager_mcp.config"]

        # When - import and call the function
        from gh_project_manager_mcp.config import get_github_token

        result = get_github_token()

        # Then
        assert result == "gh_auth_available"
        assert any("successful" in call for call in mock_print_calls)

    def test_get_github_token_handles_exception(self, monkeypatch) -> None:
        """Test that get_github_token handles exceptions during gh auth status check.

        Given:
            - GH_TOKEN is not set in the environment
            - gh auth status check raises an exception
        When:
            - get_github_token() is called
        Then:
            - It returns None
        """
        # Import here to avoid circular import
        import subprocess
        import sys

        from gh_project_manager_mcp.config import get_github_token

        # Given - clear environment variables
        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)

        # Mock subprocess.run to simulate an exception
        def mock_raise_exception(*args, **kwargs):
            raise Exception("Test exception: gh not installed")

        monkeypatch.setattr(subprocess, "run", mock_raise_exception)

        # Mock print to capture the error message
        error_messages = []

        def mock_print(*args, **kwargs):
            error_messages.append(args[0])

        monkeypatch.setattr("builtins.print", mock_print)

        # Reset any cached import to ensure fresh state
        if "gh_project_manager_mcp.config" in sys.modules:
            del sys.modules["gh_project_manager_mcp.config"]

        # When
        result = get_github_token()

        # Then
        assert result is None
        assert any("Error checking gh auth status" in msg for msg in error_messages)
