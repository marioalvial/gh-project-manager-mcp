"""Unit tests for the issues tool module."""

import json
import sys
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest

# Functions to test (Import all implemented functions)
from gh_project_manager_mcp.tools.issues import (
    _close_github_issue_impl,
    _comment_github_issue_impl,
    _create_github_issue_impl,
    _delete_github_issue_impl,
    _edit_github_issue_impl,
    _get_github_issue_impl,
    _list_github_issues_impl,
    _reopen_github_issue_impl,
    _status_github_issue_impl,
)
from pytest_mock import MockerFixture

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

# --- Fixtures ---


@pytest.fixture
def mock_resolve_param() -> Any:
    """Provide a mock for the resolve_param utility function.

    This fixture mocks the resolve_param function imported in the issues module,
    with a default behavior that passes through runtime values or returns None.

    Returns
    -------
        The mock object for resolve_param that can be customized in tests.

    """

    # Default behavior: pass through runtime value, otherwise return None
    # Tests can override this using mocker.patch if specific resolution needed
    def default_side_effect(
        capability: str, param_name: str, runtime_value: Any, *args: Any, **kwargs: Any
    ) -> Any:
        return runtime_value

    # Patch the function where it's imported in the 'issues' module
    with patch(
        "gh_project_manager_mcp.tools.issues.resolve_param",
        side_effect=default_side_effect,
    ) as mocker_fixture:
        yield mocker_fixture


@pytest.fixture
def mock_run_gh() -> Any:
    """Provide a mock for the run_gh_command utility function.

    This fixture mocks the run_gh_command function imported in the issues module,
    allowing tests to control what the command returns.

    Returns
    -------
        The mock object for run_gh_command that can be customized in tests.

    """
    # Patch the function where it's imported in the 'issues' module
    with patch("gh_project_manager_mcp.tools.issues.run_gh_command") as mocker_fixture:
        yield mocker_fixture


# --- Test _create_github_issue_impl ---


class TestCreateGithubIssue:
    """Tests for creating GitHub issues."""

    # Test data
    SAMPLE_OWNER = "octocat"
    SAMPLE_REPO = "hello-world"
    SAMPLE_TITLE = "Test Issue"
    SAMPLE_BODY = "Issue description"

    def test_create_issue_minimal_params(self, mock_run_gh, mock_resolve_param) -> None:
        """Test creating an issue with minimal required parameters.

        Given: The run_gh_command returns a successful result
               The resolve_param returns None for optional parameters
        When: Creating an issue with minimal required parameters (owner, repo,
              title, body)
        Then: run_gh_command is called with expected command arguments
              The result from run_gh_command is returned unchanged
        """
        # Given
        expected_result = {"url": "https://github.com/owner/repo/issues/1", "number": 1}
        mock_run_gh.return_value = expected_result
        # Simulate resolve_param returns None for optionals
        mock_resolve_param.return_value = None

        # When
        result = _create_github_issue_impl(
            owner="owner", repo="repo", title="Minimal Issue", body="Body text"
        )

        # Then
        expected_command = [
            "issue",
            "create",
            "--repo",
            "owner/repo",
            "--title",
            "Minimal Issue",
            "--body",
            "Body text",
            "--json",
            "url,number,title,body,state",  # Corrected fields
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_result

    def test_create_issue_all_params(self, mock_run_gh, mock_resolve_param) -> None:
        """Test creating an issue with all available parameters.

        Given: The run_gh_command returns a successful result
               The resolve_param passes through all parameter values
        When: Creating an issue with all available parameters
        Then: run_gh_command is called with expected command arguments including
              all parameters
              The result from run_gh_command is returned unchanged
        """
        # Given
        expected_result = {"url": "https://github.com/owner/repo/issues/2", "number": 2}
        mock_run_gh.return_value = expected_result
        mock_resolve_param.side_effect = lambda cap, param, val: val  # Pass through

        # When
        result = _create_github_issue_impl(
            owner="owner",
            repo="repo",
            title="Full Issue",
            body="Issue Body",
            issue_type="feature",
            assignee="user1",
            project="Project Board",
            labels=["frontend", "urgent"],
        )

        # Then - don't check exact command but check that key components are there
        assert mock_run_gh.call_count == 1
        # Get the actual call arguments
        args = mock_run_gh.call_args[0][0]

        # Verify essential command components
        assert "issue" in args
        assert "create" in args
        assert "--repo" in args
        assert "owner/repo" in args
        assert "--title" in args
        assert "Full Issue" in args
        assert "--project" in args
        assert "Project Board" in args
        assert "--assignee" in args
        assert "user1" in args

        # Verify all labels are present regardless of order
        assert "--label" in args
        assert "enhancement" in args
        assert "frontend" in args
        assert "urgent" in args

        # Check the command result is returned correctly
        assert result == expected_result

    def test_create_issue_label_resolution(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test creating an issue where labels are resolved from config/env.

        Given: The run_gh_command returns a successful result
               The resolve_param returns environment-resolved labels
        When: Creating an issue without explicitly providing labels
        Then: run_gh_command is called with the resolved labels from environment
              The result from run_gh_command is returned unchanged
        """
        # Given
        expected_result = {"url": "https://github.com/owner/repo/issues/3", "number": 3}
        mock_run_gh.return_value = expected_result
        resolved_labels_list = ["env-label1", "env-label2"]

        def side_effect(cap, param, val):
            if param == "labels":
                return resolved_labels_list
            return None  # Other optionals resolve to None

        mock_resolve_param.side_effect = side_effect

        # When
        result = _create_github_issue_impl(
            owner="owner", repo="repo", title="Env Label Issue", body="Body"
        )

        # Then
        expected_command = [
            "issue",
            "create",
            "--repo",
            "owner/repo",
            "--title",
            "Env Label Issue",
            "--body",
            "Body",
            "--json",
            "url,number,title,body,state",  # Corrected fields
            "--label",
            "env-label1",
            "--label",
            "env-label2",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_result

    def test_create_issue_gh_command_error(
        self, mock_run_gh, mock_resolve_param
    ) -> None:
        """Test error handling when gh command fails during issue creation.

        Given: The run_gh_command returns an error dictionary
               The resolve_param returns None for optional parameters
        When: Creating an issue with minimal parameters
        Then: The error from run_gh_command is returned unchanged
        """
        # Given
        error_output = {"error": "gh command failed", "stderr": "Something went wrong"}
        mock_run_gh.return_value = error_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, *args, **kwargs: None
        )  # Optionals resolve to None

        # When
        result = _create_github_issue_impl(
            owner="owner", repo="repo", title="Fail Test", body="Body for fail test."
        )

        # Then
        assert result == error_output
        # Command args checked implicitly by previous tests
        mock_run_gh.assert_called_once()

    def test_create_issue_gh_command_non_url_string(
        self, mock_run_gh, mock_resolve_param
    ) -> None:
        """Test error handling when gh returns unexpected non-JSON string.

        Given: The run_gh_command returns a non-JSON string instead of a dictionary
               The resolve_param returns None for optional parameters
        When: Creating an issue with minimal parameters
        Then: An error dictionary with the raw output is returned
        """
        # Given
        non_json_output = "Some success message that isn't JSON"
        mock_run_gh.return_value = non_json_output
        mock_resolve_param.return_value = None  # Optionals resolve to None

        # When
        result = _create_github_issue_impl(
            owner="owner", repo="repo", title="Weird String Issue", body="Body"
        )

        # Then
        expected_error = {
            "error": "Unexpected string result from gh issue create",
            "raw": non_json_output,
        }
        assert result == expected_error

    def test_unexpected_result_type(
        self, mock_resolve_param: Any, mock_run_gh: Any
    ) -> None:
        """Test handling unexpected result type from gh issue create.

        Given:
            - Valid issue details (owner, repo, title)
            - run_gh_command returns a non-dict, non-string value
        When:
            - _create_github_issue_impl is called
        Then:
            - An error dictionary with type information is returned
        """
        # Given
        test_owner = "test-owner"
        test_repo = "test-repo"
        test_title = "Test Issue"

        # This creates an object that is neither a dict nor a string
        mock_run_gh.return_value = [
            {"url": "https://github.com/test-owner/test-repo/issues/123"}
        ]

        # When
        result = _create_github_issue_impl(test_owner, test_repo, test_title)

        # Then
        assert "error" in result
        assert "Unexpected result type from gh issue create" in result["error"]
        assert "raw" in result
        assert isinstance(result["raw"], str)
        # Should contain a stringified version of the object
        assert (
            str([{"url": "https://github.com/test-owner/test-repo/issues/123"}])
            in result["raw"]
        )

    def test_issue_type_mapping(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test that issue_type maps correctly to labels.

        Given:
            - Owner, repo, title, and issue_type
            - The issue_type is a recognized type (e.g., "bug")
            - No existing labels provided
        When:
            - _create_github_issue_impl is called
        Then:
            - The correct label is added to the command
        """
        # Given
        mock_run_gh.return_value = {"url": "https://github.com/example/repo/issues/1"}

        # Set up resolve_param to handle issue_type correctly
        def resolve_side_effect(capability, param_name, value, *args, **kwargs):
            if param_name == "type" and value == "bug":
                return "bug"
            return None

        mock_resolve_param.side_effect = resolve_side_effect

        # When
        result = _create_github_issue_impl(
            owner=self.SAMPLE_OWNER,
            repo=self.SAMPLE_REPO,
            title=self.SAMPLE_TITLE,
            issue_type="bug",
        )

        # Then
        expected_command = [
            "issue",
            "create",
            "--repo",
            f"{self.SAMPLE_OWNER}/{self.SAMPLE_REPO}",
            "--title",
            self.SAMPLE_TITLE,
            "--body",
            "",
            "--json",
            "url,number,title,body,state",
            "--label",
            "bug",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["url"] == "https://github.com/example/repo/issues/1"

    def test_issue_type_unknown(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test handling of unknown issue_type values.

        Given:
            - Owner, repo, title, and issue_type
            - The issue_type is not a recognized type (not in the type_label_map)
        When:
            - _create_github_issue_impl is called
        Then:
            - No label is added for the unrecognized issue_type
        """
        # Given
        mock_run_gh.return_value = {"url": "https://github.com/example/repo/issues/1"}

        # Set up resolve_param to handle issue_type correctly
        def resolve_side_effect(capability, param_name, value, *args, **kwargs):
            if param_name == "type" and value == "unknown_type":
                return "unknown_type"
            return None

        mock_resolve_param.side_effect = resolve_side_effect

        # When
        result = _create_github_issue_impl(
            owner=self.SAMPLE_OWNER,
            repo=self.SAMPLE_REPO,
            title=self.SAMPLE_TITLE,
            issue_type="unknown_type",
        )

        # Then
        expected_command = [
            "issue",
            "create",
            "--repo",
            f"{self.SAMPLE_OWNER}/{self.SAMPLE_REPO}",
            "--title",
            self.SAMPLE_TITLE,
            "--body",
            "",
            "--json",
            "url,number,title,body,state",
            # No label flag since the type is unknown
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["url"] == "https://github.com/example/repo/issues/1"

    def test_issue_type_with_labels_not_list(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test handling of issue type when labels_resolved is not a list.

        Given:
            - Owner, repo, title, issue_type
            - resolve_param returns a non-list value for labels
        When:
            - _create_github_issue_impl is called
        Then:
            - A new list is created with just the issue type's label
        """
        # Given
        mock_run_gh.return_value = {"url": "https://github.com/example/repo/issues/1"}

        # Set up resolve_param to handle both issue_type and labels
        def resolve_side_effect(capability, param_name, value, *args, **kwargs):
            if param_name == "type" and value == "bug":
                return "bug"
            elif param_name == "labels":
                return "not-a-list"  # Intentionally return a non-list
            return None

        mock_resolve_param.side_effect = resolve_side_effect

        # When
        result = _create_github_issue_impl(
            owner=self.SAMPLE_OWNER,
            repo=self.SAMPLE_REPO,
            title=self.SAMPLE_TITLE,
            issue_type="bug",
            labels=["this-is-ignored-due-to-mock"],
        )

        # Then
        expected_command = [
            "issue",
            "create",
            "--repo",
            f"{self.SAMPLE_OWNER}/{self.SAMPLE_REPO}",
            "--title",
            self.SAMPLE_TITLE,
            "--body",
            "",
            "--json",
            "url,number,title,body,state",
            "--label",
            "bug",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["url"] == "https://github.com/example/repo/issues/1"

    def test_issue_type_with_existing_labels(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test that issue_type appends to existing labels.

        Given:
            - Owner, repo, title, issue_type, and labels
            - The issue_type is a recognized type
            - Existing labels are already provided
        When:
            - _create_github_issue_impl is called
        Then:
            - Both the existing labels and the type-derived label are included
        """
        # Given
        mock_run_gh.return_value = {"url": "https://github.com/example/repo/issues/1"}

        # Set up resolve_param to return both issue_type and labels
        def resolve_side_effect(capability, param_name, value, *args, **kwargs):
            if param_name == "type" and value == "enhancement":
                return "enhancement"
            elif param_name == "labels" and value == ["urgent"]:
                return ["urgent"]
            return None

        mock_resolve_param.side_effect = resolve_side_effect

        # When
        result = _create_github_issue_impl(
            owner=self.SAMPLE_OWNER,
            repo=self.SAMPLE_REPO,
            title=self.SAMPLE_TITLE,
            issue_type="enhancement",
            labels=["urgent"],
        )

        # Then
        expected_command = [
            "issue",
            "create",
            "--repo",
            f"{self.SAMPLE_OWNER}/{self.SAMPLE_REPO}",
            "--title",
            self.SAMPLE_TITLE,
            "--body",
            "",
            "--json",
            "url,number,title,body,state",
            "--label",
            "urgent",
            "--label",
            "enhancement",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["url"] == "https://github.com/example/repo/issues/1"

    def test_unexpected_string_result(
        self, mock_run_gh: Any, mock_resolve_param: Any, capsys: pytest.CaptureFixture
    ) -> None:
        """Test handling of unexpected string result.

        Given:
            - Valid issue creation parameters
            - run_gh_command returns a string instead of JSON dictionary
        When:
            - _create_github_issue_impl is called
        Then:
            - An error dictionary with the raw string is returned
        """
        # Given
        unexpected_output = "Created issue #1"
        mock_run_gh.return_value = unexpected_output
        mock_resolve_param.return_value = None

        # Patch the print function to prevent test output pollution and test coverage
        with patch("builtins.print") as mock_print:
            # When
            result = _create_github_issue_impl(
                owner=self.SAMPLE_OWNER, repo=self.SAMPLE_REPO, title=self.SAMPLE_TITLE
            )

            # Then
            assert "error" in result
            assert result["error"] == "Unexpected string result from gh issue create"
            assert result["raw"] == unexpected_output
            mock_print.assert_called_once()
            assert "Unexpected string result" in str(mock_print.call_args)

    def test_unexpected_other_result(
        self, mock_run_gh: Any, mock_resolve_param: Any, capsys: pytest.CaptureFixture
    ) -> None:
        """Test handling of unexpected non-string, non-dict result.

        Given:
            - Valid issue creation parameters
            - run_gh_command returns something unexpected (e.g., None)
        When:
            - _create_github_issue_impl is called
        Then:
            - An error dictionary is returned
        """
        # Given
        mock_run_gh.return_value = None
        mock_resolve_param.return_value = None

        # Patch the print function
        with patch("builtins.print") as mock_print:
            # When
            result = _create_github_issue_impl(
                owner=self.SAMPLE_OWNER, repo=self.SAMPLE_REPO, title=self.SAMPLE_TITLE
            )

            # Then
            assert "error" in result
            assert result["error"] == "Unexpected result type from gh issue create"
            assert result["raw"] == "None"
            mock_print.assert_called_once()
            assert "Unexpected result type" in str(mock_print.call_args)


# --- Test _get_github_issue_impl ---


class TestGetGithubIssue:
    """Tests for the _get_github_issue_impl function."""

    def test_get_issue_success(self, mock_run_gh: Any) -> None:
        """Test fetching a specific issue successfully.

        Given: The run_gh_command returns issue details dictionary
        When: Fetching a specific issue by number
        Then: The issue details are returned unchanged
        """
        # Given
        expected_issue_details = {
            "number": 123,
            "title": "Fetched Issue",
            "state": "OPEN",
        }
        mock_run_gh.return_value = expected_issue_details

        # When
        result = _get_github_issue_impl(owner="owner", repo="repo", issue_number=123)

        # Then
        expected_command = [
            "issue",
            "view",
            "123",
            "--repo",
            "owner/repo",
            "--json",
            (
                "number,title,state,url,body,createdAt,updatedAt,labels,"
                "assignees,comments,author,closedAt"
            ),
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_issue_details

    def test_get_issue_gh_command_error(self, mock_run_gh: Any) -> None:
        """Test error handling when gh command fails during issue fetching.

        Given: The run_gh_command returns an error dictionary
        When: Fetching a specific issue by number
        Then: The error from run_gh_command is returned unchanged
        """
        # Given
        error_output = {"error": "gh command failed", "stderr": "Issue not found"}
        mock_run_gh.return_value = error_output

        # When
        result = _get_github_issue_impl(owner="owner", repo="repo", issue_number=404)

        # Then
        assert result == error_output
        # Command args checked implicitly by previous tests
        mock_run_gh.assert_called_once()


# --- Test _list_github_issues_impl ---


class TestListGithubIssues:
    """Tests for listing GitHub issues."""

    def test_list_issues_minimal(self, mock_run_gh, mock_resolve_param) -> None:
        """Test listing issues with minimal parameters."""
        # Given
        owner = "octocat"
        repo = "hello-world"
        expected_output = [
            {"number": 1, "title": "Issue 1"},
            {"number": 2, "title": "Issue 2"},
        ]
        mock_run_gh.return_value = expected_output
        mock_resolve_param.return_value = None

        # When
        result = _list_github_issues_impl(owner=owner, repo=repo)

        # Then
        expected_command = [
            "issue",
            "list",
            "--repo",
            f"{owner}/{repo}",
            "--json",
            "number,title,state,url,createdAt,updatedAt,labels,assignees",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_output

    def test_list_issues_error_case(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test error handling when listing issues.

        Given:
            - Valid owner and repo
            - run_gh_command returns an error dictionary
        When:
            - _list_github_issues_impl is called
        Then:
            - Error is printed and empty list returned
        """
        # Given
        owner = "octocat"
        repo = "hello-world"
        error_output = {"error": "Repository not found", "details": "404 Not Found"}
        mock_run_gh.return_value = error_output
        mock_resolve_param.return_value = None

        # Patch the print function
        with patch("builtins.print") as mock_print:
            # When
            result = _list_github_issues_impl(owner=owner, repo=repo)

            # Then
            assert result == []
            mock_print.assert_called_once()
            assert "Error running gh issue list" in str(mock_print.call_args)

    def test_list_issues_with_params(self, mock_run_gh, mock_resolve_param) -> None:
        """Test listing issues with all available filters and parameters."""
        # Given
        expected_list = [{"number": 3, "title": "Filtered Issue"}]
        mock_run_gh.return_value = expected_list
        mock_resolve_param.side_effect = (
            lambda cap, param, val, *args, **kwargs: val
        )  # Pass through

        # When
        result = _list_github_issues_impl(
            owner="owner",
            repo="repo",
            state="closed",
            assignee="user2",
            labels=["bug", "urgent"],
            limit=10,
        )

        # Then
        expected_command = [
            "issue",
            "list",
            "--repo",
            "owner/repo",
            "--json",
            "number,title,state,url,createdAt,updatedAt,labels,assignees",
            "--state",
            "closed",
            "--assignee",
            "user2",
            "--label",
            "bug",
            "--label",
            "urgent",
            "--limit",
            "10",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_list

    def test_list_issues_resolve_param_defaults(
        self, mock_run_gh, mock_resolve_param
    ) -> None:
        """Test listing issues where labels resolve to a list."""
        # Given
        expected_list = [{"number": 4, "title": "Env Label Issue"}]
        mock_run_gh.return_value = expected_list
        resolved_labels_list = ["label1", "label2"]

        def side_effect(cap, param, val, *args, **kwargs):
            if param == "labels":
                return resolved_labels_list
            if param == "limit":
                return 30
            if param == "state":
                return "open"
            return None

        mock_resolve_param.side_effect = side_effect

        # When
        result = _list_github_issues_impl(owner="owner", repo="repo")

        # Then
        expected_command = [
            "issue",
            "list",
            "--repo",
            "owner/repo",
            "--json",
            "number,title,state,url,createdAt,updatedAt,labels,assignees",
            "--state",
            "open",  # Assuming default
            "--label",
            "label1",
            "--label",
            "label2",
            "--limit",
            "30",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_list

    def test_list_issues_gh_command_error(
        self, mock_run_gh, mock_resolve_param, mocker: "MockerFixture"
    ) -> None:
        """Test error handling when gh command fails during issue listing."""
        # Given
        error_output = {"error": "gh command failed", "stderr": "Invalid filter"}
        mock_run_gh.return_value = error_output
        mock_resolve_param.side_effect = lambda cap, param, val, *args, **kwargs: (
            30 if param == "limit" else ("open" if param == "state" else None)
        )
        mock_print = mocker.patch("builtins.print")

        # When
        result = _list_github_issues_impl(owner="owner", repo="repo")

        # Then
        assert result == []  # Expect empty list on error
        # Verify error was logged
        mock_print.assert_any_call(
            f"Error running gh issue list: {error_output.get('error')}", file=sys.stderr
        )

    def test_list_issues_unexpected_result(
        self, mock_run_gh, mock_resolve_param, mocker: "MockerFixture"
    ) -> None:
        """Test handling when gh returns unexpected non-list/non-error output."""
        # Given
        unexpected_output = "Just some string"
        mock_run_gh.return_value = unexpected_output
        mock_resolve_param.side_effect = lambda cap, param, val, *args, **kwargs: (
            30 if param == "limit" else ("open" if param == "state" else None)
        )
        mock_print = mocker.patch("builtins.print")

        # When
        result = _list_github_issues_impl(owner="owner", repo="repo")

        # Then
        # Implementation now returns a specific error for decode failure
        expected_error = [
            {
                "error": "Failed to decode JSON response from gh issue list",
                "raw": unexpected_output,
            }
        ]
        assert result == expected_error
        # Verify decode error was logged
        mock_print.assert_any_call(
            f"Error decoding JSON from gh issue list: {unexpected_output}",
            file=sys.stderr,
        )

    def test_string_result_valid_json_list(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test handling string result that is valid JSON list.

        Given:
            - Valid issue list parameters
            - run_gh_command returns a JSON string representing a list
        When:
            - _list_github_issues_impl is called
        Then:
            - The string is parsed and returned as a list of issues
        """
        # Given
        json_string = (
            '[{"number": 1, "title": "Issue 1"}, {"number": 2, "title": "Issue 2"}]'
        )
        expected_issues = [
            {"number": 1, "title": "Issue 1"},
            {"number": 2, "title": "Issue 2"},
        ]
        mock_run_gh.return_value = json_string
        mock_resolve_param.return_value = None

        # When
        result = _list_github_issues_impl("owner", "repo")

        # Then
        assert result == expected_issues

    def test_string_result_valid_json_not_list(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test handling string result that is valid JSON but not a list.

        Given:
            - Valid issue list parameters
            - run_gh_command returns a JSON string representing a non-list object
        When:
            - _list_github_issues_impl is called
        Then:
            - An error dictionary in a list is returned
        """
        # Given
        json_string = '{"message": "Some message"}'
        mock_run_gh.return_value = json_string
        mock_resolve_param.return_value = None

        # When - with specific printing mock to ensure the print happens
        with patch("builtins.print", autospec=True) as mock_print:
            with patch("sys.stderr") as mock_stderr:
                # Important: We need to call json.loads before it's mocked to get real behavior
                mock_json_loads = json.loads

                def side_effect(value):
                    # Call the real json.loads function so we test the real code path
                    return mock_json_loads(value)

                with patch("json.loads", side_effect=side_effect) as mock_loads:
                    result = _list_github_issues_impl("owner", "repo")

                    # Then - verify the exact lines are executed
                    mock_loads.assert_called_once_with(json_string)
                    mock_print.assert_called_once()
                    # Make sure the print message matches what we expect (testing line 167)
                    call_args = mock_print.call_args[0][0]
                    assert "gh issue list returned JSON but not a list" in call_args
                    assert json_string in call_args
                    assert (
                        mock_stderr in mock_print.call_args[1].values()
                    )  # stderr was passed

                    # Test the result (targeting line 169)
                    assert len(result) == 1
                    assert "error" in result[0]
                    assert "Expected list result" in result[0]["error"]
                    assert result[0]["raw"] == json_string

    def test_string_result_invalid_json(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test handling string result that is not valid JSON.

        Given:
            - Valid issue list parameters
            - run_gh_command returns a non-JSON string
        When:
            - _list_github_issues_impl is called
        Then:
            - An error dictionary in a list is returned
        """
        # Given
        invalid_json = "This is not JSON"
        mock_run_gh.return_value = invalid_json
        mock_resolve_param.return_value = None

        # Patch the print function
        with patch("builtins.print") as mock_print:
            # When
            result = _list_github_issues_impl("owner", "repo")

            # Then
            assert len(result) == 1
            assert "error" in result[0]
            assert "Failed to decode JSON response" in result[0]["error"]
            assert result[0]["raw"] == invalid_json
            mock_print.assert_called_once()
            assert "Error decoding JSON" in str(mock_print.call_args)

    def test_unexpected_result_type(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test handling unexpected non-list, non-dict, non-string result.

        Given:
            - Valid issue list parameters
            - run_gh_command returns something unexpected (e.g., None)
        When:
            - _list_github_issues_impl is called
        Then:
            - An empty list is returned
        """
        # Given
        mock_run_gh.return_value = None
        mock_resolve_param.return_value = None

        # Patch the print function
        with patch("builtins.print") as mock_print:
            # When
            result = _list_github_issues_impl("owner", "repo")

            # Then
            assert result == []
            mock_print.assert_called_once()
            assert "Unexpected result from gh issue list" in str(mock_print.call_args)


# --- Test _close_github_issue_impl ---


class TestCloseGithubIssue:
    """Tests for the _close_github_issue_impl function."""

    def test_close_issue_success_number(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test closing an issue by number successfully.

        Given: The run_gh_command returns a success message string
        When: Closing an issue by number
        Then: A success dictionary is returned with the issue URL
        """
        # Given
        mock_run_gh.return_value = (
            "Closed issue https://github.com/owner/repo/issues/42"
        )
        mock_resolve_param.side_effect = (
            lambda cap, param, val, *args, **kwargs: val
        )  # Pass through None

        # When
        result = _close_github_issue_impl(
            owner="owner", repo="repo", issue_identifier=42
        )

        # Then
        expected_command = ["issue", "close", "42", "--repo", "owner/repo"]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result.get("status") == "success"
        assert "Closed issue" in result.get("message", "")

    def test_close_issue_success_url_with_args(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test closing an issue by URL with comment and reason.

        Given: The run_gh_command returns the issue URL string
               The resolve_param resolves comment and reason values
        When: Closing an issue by URL with comment and reason
        Then: A success dictionary is returned with the issue URL
        """
        # Given
        issue_url = "https://github.com/owner/repo/issues/43"
        mock_run_gh.return_value = issue_url

        def side_effect(cap, param, val, *args, **kwargs):
            if param == "close_comment":
                return "Closing this one."
            if param == "close_reason":
                return "completed"
            return val

        mock_resolve_param.side_effect = side_effect

        # When
        result = _close_github_issue_impl(
            owner="owner",
            repo="repo",
            issue_identifier=issue_url,
            comment="ignored",
            reason="ignored",
        )

        # Then
        expected_command = [
            "issue",
            "close",
            issue_url,
            "--repo",
            "owner/repo",
            "--comment",
            "Closing this one.",
            "--reason",
            "completed",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == {"status": "success", "url": issue_url}

    def test_close_issue_with_invalid_reason(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test error when an invalid reason is provided.

        Given:
            - Valid parameters to close an issue
            - An invalid reason value
        When:
            - _close_github_issue_impl is called
        Then:
            - An error is returned without calling the gh command
        """
        # Given
        owner = "octocat"
        repo = "hello-world"
        issue_number = 123
        invalid_reason = "invalid_reason"

        def resolve_side_effect(capability, param_name, value, *args, **kwargs):
            if param_name == "close_reason":
                return invalid_reason
            return None

        mock_resolve_param.side_effect = resolve_side_effect

        # When
        result = _close_github_issue_impl(
            owner=owner, repo=repo, issue_identifier=issue_number, reason=invalid_reason
        )

        # Then
        assert "error" in result
        assert "Invalid reason" in result["error"]
        assert "completed" in result["error"]  # Lists valid reasons
        assert "not planned" in result["error"]
        assert "duplicate" in result["error"]
        mock_run_gh.assert_not_called()

    def test_close_issue_gh_error(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test error handling when gh command fails during issue closing.

        Given: The run_gh_command returns an error dictionary
        When: Closing an issue by number
        Then: The error from run_gh_command is returned unchanged
        """
        # Given
        error_output = {"error": "gh command failed", "stderr": "Issue already closed"}
        mock_run_gh.return_value = error_output
        mock_resolve_param.side_effect = lambda cap, param, val, *args, **kwargs: val

        # When
        result = _close_github_issue_impl(
            owner="owner", repo="repo", issue_identifier=45
        )

        # Then
        assert result == error_output
        mock_run_gh.assert_called_once()

    def test_none_result_handling(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test handling None result when closing an issue.

        Given:
            - Valid issue close parameters
            - run_gh_command returns None instead of a string or error dict
        When:
            - _close_github_issue_impl is called
        Then:
            - A success status with a default message is returned
        """
        # Given
        owner = "octocat"
        repo = "hello-world"
        issue_number = 123
        mock_run_gh.return_value = None  # Unexpected return type
        mock_resolve_param.return_value = None

        # When
        result = _close_github_issue_impl(
            owner=owner, repo=repo, issue_identifier=issue_number
        )

        # Then
        expected_command = [
            "issue",
            "close",
            str(issue_number),
            "--repo",
            f"{owner}/{repo}",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["message"] == "Issue closed successfully."


# --- Test _comment_github_issue_impl ---


class TestCommentGithubIssue:
    """Tests for the _comment_github_issue_impl function."""

    def test_comment_issue_success_body(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test adding a comment to an issue using the body parameter.

        Given: The run_gh_command returns a comment URL
        When: Adding a comment to an issue with the body parameter
        Then: A success dictionary is returned with the comment URL
        """
        # Given
        comment_url = "https://github.com/owner/repo/issues/50#issuecomment-123"
        mock_run_gh.return_value = comment_url
        mock_resolve_param.side_effect = lambda cap, param, val, *args, **kwargs: val

        # When
        result = _comment_github_issue_impl(
            owner="owner", repo="repo", issue_identifier=50, body="This is my comment."
        )

        # Then
        expected_command = [
            "issue",
            "comment",
            "50",
            "--repo",
            "owner/repo",
            "--body",
            "This is my comment.",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == {"status": "success", "comment_url": comment_url}

    def test_comment_issue_success_body_file(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test adding a comment to an issue using the body_file parameter.

        Given: The run_gh_command returns a comment URL
        When: Adding a comment to an issue with the body_file parameter
        Then: A success dictionary is returned with the comment URL
        """
        # Given
        comment_url = "https://github.com/owner/repo/issues/51#issuecomment-124"
        mock_run_gh.return_value = comment_url
        mock_resolve_param.side_effect = lambda cap, param, val, *args, **kwargs: val

        # When
        result = _comment_github_issue_impl(
            owner="owner",
            repo="repo",
            issue_identifier=51,
            body_file="/path/to/comment.md",
        )

        # Then
        expected_command = [
            "issue",
            "comment",
            "51",
            "--repo",
            "owner/repo",
            "--body-file",
            "/path/to/comment.md",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == {"status": "success", "comment_url": comment_url}

    def test_comment_issue_missing_body_and_file(self, mock_run_gh: Any) -> None:
        """Test error handling when neither body nor body_file are provided.

        Given: No mocks needed for this test
        When: Adding a comment without providing body or body_file
        Then: An error dictionary is returned without calling run_gh_command
        """
        # When
        result = _comment_github_issue_impl(
            owner="owner", repo="repo", issue_identifier=52
        )

        # Then
        assert "error" in result
        assert "Required parameter missing" in result["error"]
        mock_run_gh.assert_not_called()

    def test_comment_issue_both_body_and_file(self, mock_run_gh: Any) -> None:
        """Test error handling when both body and body_file are provided.

        Given: No mocks needed for this test
        When: Adding a comment while providing both body and body_file
        Then: An error dictionary is returned without calling run_gh_command
        """
        # When
        result = _comment_github_issue_impl(
            owner="owner",
            repo="repo",
            issue_identifier=53,
            body="Comment text",
            body_file="/path/to/file.md",
        )

        # Then
        assert "error" in result
        assert "mutually exclusive" in result["error"]
        mock_run_gh.assert_not_called()

    def test_comment_issue_body_file_stdin_disallowed(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test error handling when body_file is set to '-' (stdin).

        Given: The resolve_param returns '-' for body_file parameter
        When: Adding a comment with the body_file parameter
        Then: An error dictionary is returned without calling run_gh_command
        """
        # Given
        mock_resolve_param.side_effect = lambda cap, param, val, *args, **kwargs: (
            "-" if param == "comment_body_file" else val
        )

        # When
        result = _comment_github_issue_impl(
            owner="owner", repo="repo", issue_identifier=54, body_file="ignored"
        )

        # Then
        assert "error" in result
        assert (
            "Reading comment body from stdin ('-') is not supported" in result["error"]
        )
        mock_run_gh.assert_not_called()

    def test_comment_issue_gh_error(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test error handling when gh command fails during comment addition.

        Given: The run_gh_command returns an error dictionary
        When: Adding a comment to an issue
        Then: The error from run_gh_command is returned unchanged
        """
        # Given
        error_output = {"error": "gh command failed", "stderr": "Issue not found"}
        mock_run_gh.return_value = error_output
        mock_resolve_param.side_effect = lambda cap, param, val, *args, **kwargs: val

        # When
        result = _comment_github_issue_impl(
            owner="owner", repo="repo", issue_identifier=55, body="Comment text"
        )

        # Then
        assert result == error_output
        mock_run_gh.assert_called_once()

    def test_non_url_string_result(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test handling non-URL string result.

        Given:
            - Valid issue comment parameters
            - run_gh_command returns a string that's not a URL
        When:
            - _comment_github_issue_impl is called
        Then:
            - An error dictionary with the raw output is returned
        """
        # Given
        owner = "octocat"
        repo = "hello-world"
        issue_number = 123
        comment_body = "This is a test comment"
        unexpected_output = "Comment added successfully"  # Not a URL

        mock_run_gh.return_value = unexpected_output
        mock_resolve_param.return_value = comment_body

        # When
        result = _comment_github_issue_impl(
            owner=owner, repo=repo, issue_identifier=issue_number, body=comment_body
        )

        # Then
        expected_command = [
            "issue",
            "comment",
            str(issue_number),
            "--repo",
            f"{owner}/{repo}",
            "--body",
            comment_body,
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert "error" in result
        assert result["error"] == "Unexpected result from gh issue comment"
        assert result["raw"] == unexpected_output


# --- Test _delete_github_issue_impl ---


class TestDeleteGithubIssue:
    """Tests for the _delete_github_issue_impl function.

    This test class verifies the functionality for deleting GitHub issues,
    handling different parameters, and error scenarios.
    """

    def test_delete_issue_success_no_confirm(self, mock_run_gh: Any) -> None:
        """Test deleting an issue without confirmation (uses --yes).

        Given:
            - An issue identifier
        When:
            - _delete_github_issue_impl is called with default skip_confirmation=False
        Then:
            - run_gh_command is called with the correct parameters (no --yes flag)
            - A success dictionary with the message is returned
        """
        # Given
        mock_run_gh.return_value = "Deleted issue #60."

        # When
        result = _delete_github_issue_impl(
            owner="owner", repo="repo", issue_identifier=60
        )

        # Then
        expected_command = ["issue", "delete", "60", "--repo", "owner/repo"]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result.get("status") == "success"
        assert "Deleted issue" in result.get("message", "")

    def test_delete_issue_success_url_with_confirm(self, mock_run_gh: Any) -> None:
        """Test deleting an issue by URL with confirmation explicitly skipped.

        Given:
            - An issue URL identifier
            - skip_confirmation=True parameter
        When:
            - _delete_github_issue_impl is called
        Then:
            - run_gh_command is called with the --yes flag
            - A success dictionary is returned
        """
        # Given
        # Simulates user confirming interactively, so gh still succeeds
        issue_url = "https://github.com/owner/repo/issues/61"
        mock_run_gh.return_value = ""  # Sometimes delete outputs nothing

        # When
        result = _delete_github_issue_impl(
            owner="owner",
            repo="repo",
            issue_identifier=issue_url,
            skip_confirmation=True,
        )

        # Then
        expected_command = [
            "issue",
            "delete",
            issue_url,
            "--repo",
            "owner/repo",
            "--yes",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result.get("status") == "success"
        assert result.get("message") == ""  # Check message field now
        assert "raw_output" not in result

    def test_delete_issue_gh_error(self, mock_run_gh: Any) -> None:
        """Test error handling when gh fails during issue deletion.

        Given:
            - An issue identifier for a non-existent issue
            - run_gh_command returns an error
        When:
            - _delete_github_issue_impl is called
        Then:
            - The error dictionary is returned unchanged
        """
        # Given
        error_output = {"error": "gh command failed", "stderr": "Issue #62 not found"}
        mock_run_gh.return_value = error_output

        # When
        result = _delete_github_issue_impl(
            owner="owner", repo="repo", issue_identifier=62, skip_confirmation=True
        )

        # Then
        assert result == error_output
        mock_run_gh.assert_called_once()


# --- Test _status_github_issue_impl ---


class TestStatusGithubIssue:
    """Tests for the _status_github_issue_impl function.

    This test class verifies the functionality for getting the status of GitHub issues
    and pull requests in the current context.
    """

    def test_status_issue_success(self, mock_run_gh: Any) -> None:
        """Test getting the status of issues/PRs successfully.

        Given:
            - run_gh_command returns a status dictionary
        When:
            - _status_github_issue_impl is called
        Then:
            - run_gh_command is called with the correct JSON fields
            - The status dictionary is returned unchanged
        """
        # Given
        expected_status = {
            "relevant": [{"number": 90, "title": "Relevant PR"}],
            "current": {"number": 91, "title": "Current Branch Issue"},
            "mentioning": [{"number": 92, "title": "Mentioning Issue"}],
        }
        mock_run_gh.return_value = expected_status

        # Act
        result = _status_github_issue_impl()

        # Then
        expected_command = [
            "issue",
            "status",
            "--json",
            "currentBranch,createdBy,openIssues,closedIssues,openPullRequests",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_status

    def test_status_issue_gh_error(self, mock_run_gh: Any) -> None:
        """Test error handling when gh fails to get issue status.

        Given:
            - run_gh_command returns an error
        When:
            - _status_github_issue_impl is called
        Then:
            - The error dictionary is returned unchanged
        """
        # Given
        error_output = {"error": "gh command failed", "stderr": "No associated repo"}
        mock_run_gh.return_value = error_output

        # Act
        result = _status_github_issue_impl()

        # Then
        assert result == error_output
        mock_run_gh.assert_called_once()


# --- Test _edit_github_issue_impl ---


class TestEditGithubIssue:
    """Tests for the _edit_github_issue_impl function."""

    def test_edit_issue_success_minimal(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test editing an issue with minimal parameters."""
        # Given
        expected_result = {
            "status": "success",
            "url": "https://github.com/owner/repo/issues/123",
        }
        mock_run_gh.return_value = "https://github.com/owner/repo/issues/123"
        mock_resolve_param.return_value = None  # No resolved params

        # When
        result = _edit_github_issue_impl(
            owner="owner",
            repo="repo",
            issue_identifier=123,
            title="Updated Title",
        )

        # Then
        expected_command = [
            "issue",
            "edit",
            "123",
            "--repo",
            "owner/repo",
            "--title",
            "Updated Title",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_result

    def test_edit_issue_all_params(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test editing an issue with all parameters."""
        # Given
        expected_result = {
            "status": "success",
            "url": "https://github.com/owner/repo/issues/123",
        }
        mock_run_gh.return_value = "https://github.com/owner/repo/issues/123"
        mock_resolve_param.return_value = "5"  # Resolved milestone

        # When
        result = _edit_github_issue_impl(
            owner="owner",
            repo="repo",
            issue_identifier=123,
            title="Updated Title",
            body="Updated body content",
            add_assignees=["user1", "user2"],
            remove_assignees=["user3"],
            add_labels=["bug", "frontend"],
            remove_labels=["enhancement"],
            add_projects=["Project1"],
            remove_projects=["Project2"],
            milestone=5,
        )

        # Then
        # Check that command contains all expected elements
        call_args = mock_run_gh.call_args[0][0]

        # Base command elements
        assert "issue" in call_args
        assert "edit" in call_args
        assert "123" in call_args
        assert "--repo" in call_args
        assert "owner/repo" in call_args

        # Check additional parameters
        assert "--title" in call_args and "Updated Title" in call_args
        assert "--body" in call_args and "Updated body content" in call_args
        assert "--milestone" in call_args and "5" in call_args

        # Check assignees
        assert "--add-assignee" in call_args
        assert "user1" in call_args
        assert "user2" in call_args
        assert "--remove-assignee" in call_args
        assert "user3" in call_args

        # Check labels
        assert "--add-label" in call_args
        assert "bug" in call_args
        assert "frontend" in call_args
        assert "--remove-label" in call_args
        assert "enhancement" in call_args

        # Check projects
        assert "--add-project" in call_args
        assert "Project1" in call_args
        assert "--remove-project" in call_args
        assert "Project2" in call_args

        # Check result
        assert result == expected_result

    def test_edit_issue_non_url_response(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test editing an issue with non-URL response."""
        # Given
        expected_result = {"status": "success", "message": "Issue updated successfully"}
        mock_run_gh.return_value = "Issue updated successfully"
        mock_resolve_param.return_value = None

        # When
        result = _edit_github_issue_impl(
            owner="owner",
            repo="repo",
            issue_identifier=123,
            title="Updated Title",
        )

        # Then
        assert result == expected_result

    def test_edit_issue_gh_error(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test error handling when gh command fails during issue edit."""
        # Given
        error_output = {"error": "gh command failed", "stderr": "Access denied"}
        mock_run_gh.return_value = error_output
        mock_resolve_param.return_value = None

        # When
        result = _edit_github_issue_impl(
            owner="owner",
            repo="repo",
            issue_identifier=123,
            title="Updated Title",
        )

        # Then
        assert result == error_output

    def test_remove_projects(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
        """Test editing an issue to remove projects.

        Given:
            - Valid issue parameters
            - A list of projects to remove
        When:
            - _edit_github_issue_impl is called
        Then:
            - The correct remove-project flags are included in the command
        """
        # Given
        mock_run_gh.return_value = "https://github.com/owner/repo/issues/1"
        mock_resolve_param.side_effect = lambda cap, param, val, *args, **kwargs: val

        # When
        result = _edit_github_issue_impl(
            owner="owner",
            repo="repo",
            issue_identifier=1,
            remove_projects=["proj1", "proj2"],
        )

        # Then
        expected_command = [
            "issue",
            "edit",
            "1",
            "--repo",
            "owner/repo",
            "--remove-project",
            "proj1",
            "--remove-project",
            "proj2",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["url"] == "https://github.com/owner/repo/issues/1"

    def test_edit_empty_result(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
        """Test handling of empty or None result after editing an issue.

        Given:
            - Valid edit issue parameters
            - run_gh_command returns None or empty string
        When:
            - _edit_github_issue_impl is called
        Then:
            - A success status with default message is returned
        """
        # Given
        mock_run_gh.return_value = None
        mock_resolve_param.return_value = None

        # When
        result = _edit_github_issue_impl(
            owner="owner", repo="repo", issue_identifier=1, title="New Title"
        )

        # Then
        assert result["status"] == "success"
        assert result["message"] == "Issue updated successfully."

    def test_edit_issue_other_result_type(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test handling of other result types (not string, not dict with error).

        Given:
            - Valid issue edit parameters
            - run_gh_command returns something unexpected (None)
        When:
            - _edit_github_issue_impl is called
        Then:
            - A default success message is returned
        """
        # Given
        owner = "octocat"
        repo = "hello-world"
        issue_number = 123
        new_title = "Updated Title"
        mock_run_gh.return_value = None  # Unexpected return type
        mock_resolve_param.return_value = None

        # When
        result = _edit_github_issue_impl(
            owner=owner, repo=repo, issue_identifier=issue_number, title=new_title
        )

        # Then
        expected_command = [
            "issue",
            "edit",
            str(issue_number),
            "--repo",
            f"{owner}/{repo}",
            "--title",
            new_title,
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["message"] == "Issue updated successfully."


# --- Test _reopen_github_issue_impl ---


class TestReopenGithubIssue:
    """Tests for the _reopen_github_issue_impl function."""

    def test_reopen_issue_success_minimal(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test reopening an issue with minimal parameters."""
        # Given
        expected_result = {
            "status": "success",
            "url": "https://github.com/owner/repo/issues/123",
        }
        mock_run_gh.return_value = "https://github.com/owner/repo/issues/123"
        mock_resolve_param.return_value = None  # No resolved params

        # When
        result = _reopen_github_issue_impl(
            owner="owner",
            repo="repo",
            issue_identifier=123,
        )

        # Then
        expected_command = [
            "issue",
            "reopen",
            "123",
            "--repo",
            "owner/repo",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_result

    def test_reopen_issue_with_comment(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test reopening an issue with a comment."""
        # Given
        expected_result = {
            "status": "success",
            "url": "https://github.com/owner/repo/issues/123",
        }
        mock_run_gh.return_value = "https://github.com/owner/repo/issues/123"
        # Simulate resolve_param returning the comment
        mock_resolve_param.return_value = "Reopening this issue due to regression"

        # When
        result = _reopen_github_issue_impl(
            owner="owner",
            repo="repo",
            issue_identifier=123,
            comment="Reopening this issue due to regression",
        )

        # Then
        expected_command = [
            "issue",
            "reopen",
            "123",
            "--repo",
            "owner/repo",
            "--comment",
            "Reopening this issue due to regression",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_result

    def test_reopen_issue_non_url_response(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test reopening an issue with non-URL response."""
        # Given
        expected_result = {
            "status": "success",
            "message": "Issue reopened successfully",
        }
        mock_run_gh.return_value = "Issue reopened successfully"
        mock_resolve_param.return_value = None

        # When
        result = _reopen_github_issue_impl(
            owner="owner",
            repo="repo",
            issue_identifier=123,
        )

        # Then
        assert result == expected_result

    def test_reopen_issue_gh_error(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test error handling when gh command fails during issue reopen."""
        # Given
        error_output = {"error": "gh command failed", "stderr": "Access denied"}
        mock_run_gh.return_value = error_output
        mock_resolve_param.return_value = None

        # When
        result = _reopen_github_issue_impl(
            owner="owner",
            repo="repo",
            issue_identifier=123,
        )

        # Then
        assert result == error_output

    def test_none_result_handling(
        self, mock_run_gh: Any, mock_resolve_param: Any
    ) -> None:
        """Test handling None result when reopening an issue.

        Given:
            - Valid issue reopen parameters
            - run_gh_command returns None instead of a string or error dict
        When:
            - _reopen_github_issue_impl is called
        Then:
            - A success status with a default message is returned
        """
        # Given
        owner = "octocat"
        repo = "hello-world"
        issue_number = 123
        mock_run_gh.return_value = None  # Unexpected return type
        mock_resolve_param.return_value = None

        # When
        result = _reopen_github_issue_impl(
            owner=owner, repo=repo, issue_identifier=issue_number
        )

        # Then
        expected_command = [
            "issue",
            "reopen",
            str(issue_number),
            "--repo",
            f"{owner}/{repo}",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["message"] == "Issue reopened successfully."


# --- Test _reopen_github_issue_impl ---


class TestInitTools:
    """Tests for the init_tools function."""

    def test_init_tools_registers_all_functions(self, mocker: MockerFixture) -> None:
        """Test that init_tools registers all the functions with the server."""
        # Given
        mock_server = mocker.MagicMock()
        mocker.patch("builtins.print")  # Suppress print statements

        # Import here to avoid circular import with mocking
        from gh_project_manager_mcp.tools.issues import init_tools

        # When
        init_tools(mock_server)

        # Then
        # Each function should be registered exactly once
        assert mock_server.tool.call_count == 9

        # Verify each tool function was registered
        registered_functions = [
            call_args[0][0].__name__ for call_args in mock_server.tool().call_args_list
        ]

        expected_functions = [
            "_create_github_issue_impl",
            "_get_github_issue_impl",
            "_list_github_issues_impl",
            "_close_github_issue_impl",
            "_comment_github_issue_impl",
            "_delete_github_issue_impl",
            "_status_github_issue_impl",
            "_edit_github_issue_impl",
            "_reopen_github_issue_impl",
        ]

        for func_name in expected_functions:
            assert func_name in registered_functions
