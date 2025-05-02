"""Unit tests for the issues tool module."""

import sys
from typing import Any, Callable, Dict, List, Optional, Union, TYPE_CHECKING
from unittest.mock import patch

import pytest

# Functions to test (Import all implemented functions)
from gh_project_manager_mcp.tools.issues import (
    _close_github_issue_impl,
    _comment_github_issue_impl,
    _create_github_issue_impl,
    _create_issue_branch_impl,
    _delete_github_issue_impl,
    _get_github_issue_impl,
    _list_github_issues_impl,
    _list_issue_linked_branches_impl,
    _status_github_issue_impl,
    _transfer_github_issue_impl,
    _unlock_github_issue_impl,
    _unpin_github_issue_impl,
)

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

# --- Fixtures ---


@pytest.fixture
def mock_resolve_param() -> Any:
    """Provide a mock for the resolve_param utility function.
    
    This fixture mocks the resolve_param function imported in the issues module,
    with a default behavior that passes through runtime values or returns None.
    
    Returns:
        The mock object for resolve_param that can be customized in tests.
    """
    # Default behavior: pass through runtime value, otherwise return None
    # Tests can override this using mocker.patch if specific resolution needed
    def default_side_effect(capability: str, param_name: str, runtime_value: Any, *args: Any, **kwargs: Any) -> Any:
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
    
    Returns:
        The mock object for run_gh_command that can be customized in tests.
    """
    # Patch the function where it's imported in the 'issues' module
    with patch("gh_project_manager_mcp.tools.issues.run_gh_command") as mocker_fixture:
        yield mocker_fixture


# --- Test _create_github_issue_impl ---

class TestCreateGithubIssue:
    """Tests for the _create_github_issue_impl function."""

    def test_create_issue_minimal(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
        """Test creating an issue with minimal parameters.
        
        Given: The run_gh_command returns a successful result
               The resolve_param returns None for optional parameters
        When: Creating an issue with minimal required parameters (owner, repo, title, body)
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
            "issue", "create",
            "--repo", "owner/repo",
            "--title", "Minimal Issue",
            "--body", "Body text",
            "--json", "url,number,title,body,state" # Corrected fields
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_result

    def test_create_issue_all_params(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
        """Test creating an issue with all parameters.
        
        Given: The run_gh_command returns a successful result
               The resolve_param passes through all parameter values
        When: Creating an issue with all available parameters 
        Then: run_gh_command is called with expected command arguments including all parameters
              The result from run_gh_command is returned unchanged
        """
        # Given
        expected_result = {"url": "https://github.com/owner/repo/issues/2", "number": 2}
        mock_run_gh.return_value = expected_result
        mock_resolve_param.side_effect = lambda cap, param, val: val # Pass through

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

        # Then
        expected_command = [
            "issue", "create",
            "--repo", "owner/repo",
            "--title", "Full Issue",
            "--body", "Issue Body",
            "--json", "url,number,title,body,state", # Corrected fields
            "--project", "Project Board",
            "--assignee", "user1",
            "--label", "enhancement", # From issue_type="feature"
            "--label", "frontend",
            "--label", "urgent",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_result

    def test_create_issue_label_resolution(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
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
            return None # Other optionals resolve to None
        mock_resolve_param.side_effect = side_effect

        # When
        result = _create_github_issue_impl(
            owner="owner", repo="repo", title="Env Label Issue", body="Body"
        )

        # Then
        expected_command = [
            "issue", "create",
            "--repo", "owner/repo",
            "--title", "Env Label Issue",
            "--body", "Body",
            "--json", "url,number,title,body,state", # Corrected fields
            "--label", "env-label1",
            "--label", "env-label2",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_result

    def test_create_issue_gh_command_error(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
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
        mock_run_gh.assert_called_once()  # Command args checked implicitly by previous tests

    def test_create_issue_gh_command_non_url_string(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
        """Test error handling when gh returns unexpected non-JSON string.
        
        Given: The run_gh_command returns a non-JSON string instead of a dictionary
               The resolve_param returns None for optional parameters
        When: Creating an issue with minimal parameters
        Then: An error dictionary with the raw output is returned
        """
        # Given
        non_json_output = "Some success message that isn't JSON"
        mock_run_gh.return_value = non_json_output
        mock_resolve_param.return_value = None # Optionals resolve to None

        # When
        result = _create_github_issue_impl(
            owner="owner", repo="repo", title="Weird String Issue", body="Body"
        )

        # Then
        expected_error = {
            "error": "Unexpected string result from gh issue create", # Corrected error message
            "raw": non_json_output,
        }
        assert result == expected_error


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
        expected_issue_details = {"number": 123, "title": "Fetched Issue", "state": "OPEN"}
        mock_run_gh.return_value = expected_issue_details

        # When
        result = _get_github_issue_impl(owner="owner", repo="repo", issue_number=123)

        # Then
        expected_command = [
            "issue", "view", "123",
            "--repo", "owner/repo",
            "--json", (
                "number,title,state,url,body,createdAt,updatedAt,labels,"
                "assignees,comments,author,closedAt"
            )
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
        mock_run_gh.assert_called_once()


# --- Test _list_github_issues_impl ---

class TestListGithubIssues:
    """Tests for the _list_github_issues_impl function."""
    
    def test_list_issues_minimal(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
        """Test listing issues with minimal parameters (using defaults)."""
        # Given
        expected_list = [
            {"number": 1, "title": "Issue 1"},
            {"number": 2, "title": "Issue 2"}
        ]
        mock_run_gh.return_value = expected_list

        # Simulate resolve_param returning defaults
        def side_effect(cap, param, val, *args, **kwargs):
            if val is not None:
                return val
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
            "issue", "list",
            "--repo", "owner/repo",
            "--json", "number,title,state,url,createdAt,updatedAt,labels,assignees", # Correct JSON fields
            "--state", "open", # Assuming default state is open
            "--limit", "30" # Assuming default limit is 30
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_list

    def test_list_issues_all_params(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
        """Test listing issues with all available filters and parameters."""
        # Given
        expected_list = [{"number": 3, "title": "Filtered Issue"}]
        mock_run_gh.return_value = expected_list
        mock_resolve_param.side_effect = lambda cap, param, val, *args, **kwargs: val # Pass through

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
            "issue", "list",
            "--repo", "owner/repo",
            "--json", "number,title,state,url,createdAt,updatedAt,labels,assignees", # Correct JSON fields
            "--state", "closed",
            "--assignee", "user2",
            "--label", "bug",
            "--label", "urgent",
            "--limit", "10"
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_list

    def test_list_issues_labels_resolved_string(self, mock_run_gh: Any, mock_resolve_param: Any, mocker: "MockerFixture") -> None:
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
            "issue", "list",
            "--repo", "owner/repo",
            "--json", "number,title,state,url,createdAt,updatedAt,labels,assignees", # Correct JSON fields
            "--state", "open", # Assuming default
            "--label", "label1",
            "--label", "label2",
            "--limit", "30"
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_list

    def test_list_issues_gh_command_error(self, mock_run_gh: Any, mock_resolve_param: Any, mocker: "MockerFixture") -> None:
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
            f"Error running gh issue list: {error_output.get('error')}",
            file=sys.stderr
        )

    def test_list_issues_unexpected_result(self, mock_run_gh: Any, mock_resolve_param: Any, mocker: "MockerFixture") -> None:
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
            {"error": "Failed to decode JSON response from gh issue list", "raw": unexpected_output}
        ]
        assert result == expected_error
        # Verify decode error was logged
        mock_print.assert_any_call(
            f"Error decoding JSON from gh issue list: {unexpected_output}",
            file=sys.stderr
        )


# --- Test _close_github_issue_impl ---

class TestCloseGithubIssue:
    """Tests for the _close_github_issue_impl function."""

    def test_close_issue_success_number(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
        """Test closing an issue by number successfully.
        
        Given: The run_gh_command returns a success message string
        When: Closing an issue by number
        Then: A success dictionary is returned with the issue URL
        """
        # Given
        mock_run_gh.return_value = "Closed issue https://github.com/owner/repo/issues/42"
        mock_resolve_param.side_effect = (
            lambda cap, param, val, *args, **kwargs: val
        )  # Pass through None

        # When
        result = _close_github_issue_impl(owner="owner", repo="repo", issue_identifier=42)

        # Then
        expected_command = ["issue", "close", "42", "--repo", "owner/repo"]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result.get("status") == "success"
        assert "Closed issue" in result.get("message", "")

    def test_close_issue_success_url_with_args(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
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

    def test_close_issue_invalid_reason(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
        """Test closing an issue with an invalid reason returns an error.
        
        Given: The resolve_param returns an invalid reason value
        When: Closing an issue with a reason parameter
        Then: An error dictionary is returned without calling run_gh_command
        """
        # Given
        mock_resolve_param.side_effect = lambda cap, param, val, *args, **kwargs: (
            "invalid_state" if param == "close_reason" else val
        )

        # When
        result = _close_github_issue_impl(
            owner="owner", repo="repo", issue_identifier=44, reason="ignored"
        )

        # Then
        assert "error" in result
        assert "Invalid reason 'invalid_state'" in result["error"]
        mock_run_gh.assert_not_called()

    def test_close_issue_gh_error(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
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
        result = _close_github_issue_impl(owner="owner", repo="repo", issue_identifier=45)

        # Then
        assert result == error_output
        mock_run_gh.assert_called_once()


# --- Test _comment_github_issue_impl ---

class TestCommentGithubIssue:
    """Tests for the _comment_github_issue_impl function."""

    def test_comment_issue_success_body(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
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
    
    def test_comment_issue_success_body_file(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
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
            owner="owner", repo="repo", issue_identifier=51, body_file="/path/to/comment.md"
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
    
    def test_comment_issue_body_file_stdin_disallowed(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
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
        assert "Reading comment body from stdin ('-') is not supported" in result["error"]
        mock_run_gh.assert_not_called()
    
    def test_comment_issue_gh_error(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
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
        result = _delete_github_issue_impl(owner="owner", repo="repo", issue_identifier=60)

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
            owner="owner", repo="repo", issue_identifier=issue_url, skip_confirmation=True
        )

        # Then
        expected_command = ["issue", "delete", issue_url, "--repo", "owner/repo", "--yes"]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result.get("status") == "success"
        assert result.get("message") == ""  # Check message field now
        assert "raw_output" not in result

    def test_delete_issue_gh_error(self, mock_run_gh: Any) -> None:
        """Test error handling when gh command fails during issue deletion.
        
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


# --- Test _create_issue_branch_impl ---

class TestCreateIssueBranch:
    """Tests for the _create_issue_branch_impl function.
    
    This test class verifies the functionality for creating branches from GitHub issues,
    handling different parameters, and error scenarios.
    """

    def test_create_issue_branch_simple(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
        """Test creating a branch from an issue with default branch name.
        
        Given:
            - An issue identifier
            - Optional parameters resolving to None
        When:
            - _create_issue_branch_impl is called with minimal parameters
        Then:
            - run_gh_command is called with the correct parameters
            - A success dictionary with the branch creation message is returned
        """
        # Given
        mock_run_gh.return_value = "Created branch 'issue-70-branch' from issue #70"
        mock_resolve_param.side_effect = (
            lambda cap, param, val, *args, **kwargs: val
        )  # Pass through None

        # Act
        result = _create_issue_branch_impl(owner="owner", repo="repo", issue_identifier=70)

        # Assert
        expected_command = ["issue", "develop", "70", "--repo", "owner/repo"]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result.get("status") == "success"
        assert "Created branch" in result.get("message", "")

    def test_create_issue_branch_all_args(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
        """Test creating a branch with specific name, base, and checkout flag.
        
        Given:
            - An issue identifier
            - branch_name, base_branch parameters resolving to specific values
            - checkout=True parameter
        When:
            - _create_issue_branch_impl is called with all parameters
        Then:
            - run_gh_command is called with all flags (--branch, --base, --checkout)
            - A success dictionary with the checkout message is returned
        """
        # Given
        mock_run_gh.return_value = "Checked out branch 'my-issue-branch' from issue #71"

        # Simulate branch_name and base_branch resolving
        def side_effect(cap: str, param: str, val: Any) -> Any:
            if param == "branch_name":
                return "my-issue-branch"
            # Use the correct parameter name used by resolve_param in the impl
            if param == "develop_base_branch":
                return "develop"
            return None # Other params resolve to None
        mock_resolve_param.side_effect = side_effect

        # Act
        result = _create_issue_branch_impl(
            owner="owner",
            repo="repo",
            issue_identifier=71,
            branch_name="my-issue-branch", # This value goes to resolve_param
            checkout=True,
            base_branch="develop",      # This value goes to resolve_param
        )

        # Assert
        expected_command = [
            "issue",
            "develop",
            "71",
            "--repo",
            "owner/repo",
            "--branch",
            "my-issue-branch",
            "--base",
            "develop",
            "--checkout",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result.get("status") == "success"
        assert "Checked out branch" in result.get("message", "")

    def test_create_issue_branch_gh_error(self, mock_run_gh: Any, mock_resolve_param: Any) -> None:
        """Test error handling when gh fails to create issue branch.
        
        Given:
            - An issue identifier
            - run_gh_command returns an error
        When:
            - _create_issue_branch_impl is called
        Then:
            - The error dictionary is returned unchanged
        """
        # Given
        error_output = {"error": "gh command failed", "stderr": "Branch already exists"}
        mock_run_gh.return_value = error_output
        mock_resolve_param.side_effect = lambda cap, param, val, *args, **kwargs: val

        # Act
        result = _create_issue_branch_impl(owner="owner", repo="repo", issue_identifier=72)

        # Then
        assert result == error_output
        mock_run_gh.assert_called_once()


# --- Test _list_issue_linked_branches_impl ---

class TestListIssueLinkedBranches:
    """Tests for the _list_issue_linked_branches_impl function.
    
    This test class verifies the functionality for listing branches linked to GitHub issues,
    handling different output formats, and error scenarios.
    """

    def test_list_issue_linked_branches_success(self, mock_run_gh: Any) -> None:
        """Test listing linked branches for an issue successfully.
        
        Given:
            - An issue identifier
            - run_gh_command returns a list of branches
        When:
            - _list_issue_linked_branches_impl is called
        Then:
            - run_gh_command is called with the --list flag
            - A success dictionary with the branches list is returned
        """
        # Given
        expected_branches = [
            {"branchName": "issue-80-fix", "repo": "owner/repo"},
            {"branchName": "user/issue-80-dev", "repo": "owner/repo"},
        ]
        mock_run_gh.return_value = expected_branches

        # Act
        result = _list_issue_linked_branches_impl(
            owner="owner", repo="repo", issue_identifier=80
        )

        # Assert
        expected_command = ["issue", "develop", "80", "--repo", "owner/repo", "--list"]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result.get("status") == "success"
        assert result.get("linked_branches") == expected_branches

    def test_list_issue_linked_branches_none(self, mock_run_gh: Any) -> None:
        """Test listing linked branches when none exist.
        
        Given:
            - An issue identifier
            - run_gh_command returns an empty string (no branches)
        When:
            - _list_issue_linked_branches_impl is called
        Then:
            - run_gh_command is called with the --list flag
            - A success dictionary is returned with appropriate content
        """
        # Given
        # Mock depends on whether gh returns empty list [] or empty string ""
        mock_run_gh.return_value = "" # Assuming empty string for no branches

        # Act
        result = _list_issue_linked_branches_impl(
            owner="owner", repo="repo", issue_identifier=81
        )

        # Then
        expected_command = ["issue", "develop", "81", "--repo", "owner/repo", "--list"]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result.get("status") == "success"
        if "linked_branches" in result:
            assert result.get("linked_branches") == []
        elif "output" in result:
            assert result.get("output") == ""

    def test_list_issue_linked_branches_gh_error(self, mock_run_gh: Any) -> None:
        """Test error handling when gh fails to list linked branches.
        
        Given:
            - An issue identifier
            - run_gh_command returns an error
        When:
            - _list_issue_linked_branches_impl is called
        Then:
            - The error dictionary is returned unchanged
        """
        # Given
        error_output = {"error": "gh command failed", "stderr": "Issue not found"}
        mock_run_gh.return_value = error_output

        # Act
        result = _list_issue_linked_branches_impl(
            owner="owner", repo="repo", issue_identifier=82
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


# --- Test _transfer_github_issue_impl ---

class TestTransferGithubIssue:
    """Tests for the _transfer_github_issue_impl function.
    
    This test class verifies the functionality for transferring GitHub issues
    to different repositories.
    """

    def test_transfer_issue_success(self, mock_run_gh: Any) -> None:
        """Test transferring an issue to another repository successfully.
        
        Given:
            - An issue identifier and destination repository
            - run_gh_command returns the new issue URL
        When:
            - _transfer_github_issue_impl is called
        Then:
            - run_gh_command is called with the correct parameters
            - A success dictionary with the new URL is returned
        """
        # Given
        destination_repo = "new-owner/new-repo"
        transfer_url = f"https://github.com/{destination_repo}/issues/1"
        mock_run_gh.return_value = transfer_url

        # When
        result = _transfer_github_issue_impl(
            owner="old-owner",
            repo="old-repo",
            issue_identifier=100,
            destination_repo=destination_repo,
        )

        # Then
        expected_command = [
            "issue", 
            "transfer", 
            "100", 
            destination_repo,
            "--repo", 
            "old-owner/old-repo", 
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result.get("status") == "success"
        assert result.get("new_url") == transfer_url

    def test_transfer_issue_gh_error(self, mock_run_gh: Any) -> None:
        """Test error handling when gh fails to transfer an issue.
        
        Given:
            - An issue identifier and destination repository
            - run_gh_command returns an error
        When:
            - _transfer_github_issue_impl is called
        Then:
            - The error dictionary is returned unchanged
        """
        # Given
        error_output = {"error": "gh command failed", "stderr": "Permission denied"}
        mock_run_gh.return_value = error_output

        # When
        result = _transfer_github_issue_impl(
            owner="old-owner",
            repo="old-repo",
            issue_identifier=101,
            destination_repo="new-owner/new-repo",
        )

        # Then
        assert result == error_output
        mock_run_gh.assert_called_once()


# --- Test _unlock_github_issue_impl ---

class TestUnlockGithubIssue:
    """Tests for the _unlock_github_issue_impl function.
    
    This test class verifies the functionality for unlocking GitHub issues
    to allow comments and other interactions.
    """

    def test_unlock_issue_success(self, mock_run_gh: Any) -> None:
        """Test unlocking an issue successfully.
        
        Given:
            - An issue identifier
            - run_gh_command returns a success message
        When:
            - _unlock_github_issue_impl is called
        Then:
            - run_gh_command is called with the correct parameters
            - A success dictionary with the message is returned
        """
        # Given
        mock_run_gh.return_value = "Issue #110 unlocked"

        # When
        result = _unlock_github_issue_impl(
            owner="owner", repo="repo", issue_identifier=110
        )

        # Then
        expected_command = ["issue", "unlock", "110", "--repo", "owner/repo"]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result.get("status") == "success"
        assert "unlocked" in result.get("message", "")

    def test_unlock_issue_gh_error(self, mock_run_gh: Any) -> None:
        """Test error handling when gh fails to unlock an issue.
        
        Given:
            - An issue identifier
            - run_gh_command returns an error
        When:
            - _unlock_github_issue_impl is called
        Then:
            - The error dictionary is returned unchanged
        """
        # Given
        error_output = {"error": "gh command failed", "stderr": "Issue already unlocked"}
        mock_run_gh.return_value = error_output

        # When
        result = _unlock_github_issue_impl(
            owner="owner", repo="repo", issue_identifier=111
        )

        # Then
        assert result == error_output
        mock_run_gh.assert_called_once()


# --- Test _unpin_github_issue_impl ---

class TestUnpinGithubIssue:
    """Tests for the _unpin_github_issue_impl function.
    
    This test class verifies the functionality for unpinning GitHub issues
    from a repository's pinned issues list.
    """

    def test_unpin_issue_success(self, mock_run_gh: Any) -> None:
        """Test unpinning an issue successfully.
        
        Given:
            - An issue identifier
            - run_gh_command returns a success message
        When:
            - _unpin_github_issue_impl is called
        Then:
            - run_gh_command is called with the correct parameters
            - A success dictionary with the message is returned
        """
        # Given
        mock_run_gh.return_value = "Issue #120 unpinned from repository"

        # When
        result = _unpin_github_issue_impl(
            owner="owner", repo="repo", issue_identifier=120
        )

        # Then
        expected_command = ["issue", "unpin", "120", "--repo", "owner/repo"]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result.get("status") == "success"
        assert "unpinned" in result.get("message", "")

    def test_unpin_issue_gh_error(self, mock_run_gh: Any) -> None:
        """Test error handling when gh fails to unpin an issue.
        
        Given:
            - An issue identifier
            - run_gh_command returns an error
        When:
            - _unpin_github_issue_impl is called
        Then:
            - The error dictionary is returned unchanged
        """
        # Given
        error_output = {"error": "gh command failed", "stderr": "Issue not pinned"}
        mock_run_gh.return_value = error_output

        # When
        result = _unpin_github_issue_impl(
            owner="owner", repo="repo", issue_identifier=121
        )

        # Then
        assert result == error_output
        mock_run_gh.assert_called_once()
