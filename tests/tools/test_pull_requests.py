"""Unit tests for the pull_requests tool module."""

# tests/tools/test_pull_requests.py
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from unittest.mock import patch

import pytest

# Assuming TOOL_PARAM_CONFIG might be needed for body resolution check
from gh_project_manager_mcp.config import TOOL_PARAM_CONFIG

# Function to test
from gh_project_manager_mcp.tools.pull_requests import (
    _checkout_github_pull_request_impl,
    _checks_github_pull_request_impl,
    _close_github_pull_request_impl,
    _create_pull_request_impl,
    _edit_github_pull_request_impl,
    _list_github_pull_requests_impl,
)

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock import MockerFixture
    from unittest.mock import MagicMock

# --- Fixtures ---


@pytest.fixture
def mock_resolve_param() -> "MagicMock":
    """Provide a mock for the resolve_param utility function.
    
    This fixture mocks the resolve_param function from the pull_requests module,
    with a default behavior that passes through runtime values.
    
    Returns:
        The mock object for resolve_param that can be customized in tests.
    """
    # Basic mock: return runtime value if not None, else None/default
    # Body has special handling in create_pr, might need refinement if body default exists
    def side_effect(capability: str, param_name: str, runtime_value: Any, *args: Any, **kwargs: Any) -> Any:
        # Body has special handling in create_pr, might need refinement if body default exists
        if param_name == "body":
            # Simulate config check: only resolve if 'body' is configured, else return runtime value
            if "body" in TOOL_PARAM_CONFIG.get(capability, {}):
                return runtime_value  # Let implementation handle None -> ""
            else:
                return runtime_value  # Return as-is if not in config
        return runtime_value

    with patch(
        "gh_project_manager_mcp.tools.pull_requests.resolve_param",
        side_effect=side_effect,
    ) as mocker_fixture:
        yield mocker_fixture


@pytest.fixture
def mock_run_gh() -> "MagicMock":
    """Provide a mock for the run_gh_command utility function.
    
    This fixture mocks the run_gh_command function imported in the pull_requests module,
    allowing tests to control what the command returns.
    
    Returns:
        The mock object for run_gh_command that can be customized in tests.
    """
    with patch(
        "gh_project_manager_mcp.tools.pull_requests.run_gh_command"
    ) as mocker_fixture:
        yield mocker_fixture


# --- Test Classes ---

class TestCreatePullRequest:
    """Tests for the _create_pull_request_impl function.
    
    This test class verifies the functionality for creating GitHub pull requests,
    handling different parameter combinations, and error scenarios.
    """

    def test_create_pr_minimal(self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock") -> None:
        """Test creating a PR with minimal parameters.
        
        Given:
            - A request to create a PR with only mandatory parameters
        When:
            - _create_pull_request_impl is called
        Then:
            - run_gh_command is called with the correct base 'pr create' command,
              JSON flag, empty body, and the JSON result is returned
        """
        # Given
        expected_result = {"url": "https://github.com/owner/repo/pull/1", "number": 1}
        mock_run_gh.return_value = expected_result
        # Simulate resolve_param returns None for optional params when called with None
        mock_resolve_param.side_effect = lambda cap, param, val: None

        # When
        result = _create_pull_request_impl(
            owner="owner", repo="repo", title="New PR", head="feature-branch", base="main"
        )

        # Then
        expected_command = [
            "pr", "create",
            "--repo", "owner/repo",
            "--base", "main",
            "--head", "feature-branch",
            "--title", "New PR",
            "--body", "",  # Always includes body
            "--json", "url,number,title,body,state"
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_result

    def test_create_pr_all_params(self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock") -> None:
        """Test creating a PR with all parameters provided.
        
        Given:
            - A request to create a PR with all parameters provided
        When:
            - _create_pull_request_impl is called
        Then:
            - run_gh_command is called with all parameters correctly added to the command
              (repeated flags for reviewers/labels), and the JSON result is returned
        """
        # Given
        expected_result = {"url": "https://github.com/owner/repo/pull/2", "number": 2}
        mock_run_gh.return_value = expected_result
        # Simulate resolve_param returning the provided values
        mock_resolve_param.side_effect = lambda cap, param, val: val

        # When
        result = _create_pull_request_impl(
            owner="owner",
            repo="repo",
            title="Full PR",
            head="feature-x",
            base="develop",
            body="PR body content.",
            reviewers=["lead_dev", "qa_tester"],
            pr_labels=["needs-review", "frontend"],
            draft=True
        )

        # Then
        expected_command = [
            "pr",
            "create",
            "--repo", "owner/repo",
            "--base", "develop",
            "--head", "feature-x",
            "--title", "Full PR",
            "--body", "PR body content.",
            "--json", "url,number,title,body,state",
            "--draft",
            "--reviewer", "lead_dev",
            "--reviewer", "qa_tester",
            "--label", "needs-review",
            "--label", "frontend",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_result

    def test_create_pr_reviewers_labels_resolved_string(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock", mocker: "MockerFixture"
    ) -> None:
        """Test creating a PR where list params resolve from config/env.
        
        Given:
            - A request to create a PR where reviewers and labels resolve to lists
              (simulating env vars)
        When:
            - _create_pull_request_impl is called
        Then:
            - run_gh_command is called with repeated flags for reviewers/labels from
              the lists, and the JSON result is returned
        """
        # Given
        expected_result = {"url": "https://github.com/owner/repo/pull/3", "number": 3}
        mock_run_gh.return_value = expected_result
        resolved_reviewers = ["rev1", "rev2"]
        resolved_labels = ["label_a", "label_b"]

        # Simulate resolve_param returning lists for list types
        def side_effect(cap: str, param: str, val: Any) -> Any:
            if param == "reviewers":
                return resolved_reviewers
            # Use correct param name from implementation
            if param == "pr_labels":
                return resolved_labels
            if param == "body":
                return None # Simulate body not resolved
            return None

        mock_resolve_param.side_effect = side_effect

        # When
        result = _create_pull_request_impl(
            owner="owner",
            repo="repo",
            title="String Resolve PR",
            head="feat/z",
            base="main",
            # Pass pr_labels here to trigger resolution
            pr_labels=[]
        )

        # Then
        expected_command = [
            "pr", "create",
            "--repo", "owner/repo",
            "--base", "main",
            "--head", "feat/z",
            "--title", "String Resolve PR",
            "--body", "",
            "--json", "url,number,title,body,state",
            "--reviewer", "rev1",
            "--reviewer", "rev2",
            "--label", "label_a",
            "--label", "label_b",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_result

    def test_create_pr_gh_command_error(self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock") -> None:
        """Test error handling when gh fails during PR creation.
        
        Given:
            - A request to create a PR
        When:
            - run_gh_command returns an error dictionary
        Then:
            - The error dictionary from run_gh_command is returned directly
        """
        # Given
        error_output = {"error": "gh command failed", "stderr": "Branch conflict"}
        mock_run_gh.return_value = error_output
        # Simulate resolve_param returning None for optional args
        mock_resolve_param.side_effect = lambda cap, param, val: (
            val if val is not None else None
        )

        # When
        result = _create_pull_request_impl(
            owner="owner", repo="repo", title="Fail PR", head="bad-branch", base="main"
        )

        # Then
        assert result == error_output
        mock_run_gh.assert_called_once()

    def test_create_pr_gh_command_non_json_string(self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock") -> None:
        """Test handling unexpected non-JSON string output from gh pr create.
        
        Given:
            - A request to create a PR with the --json flag requested
        When:
            - run_gh_command returns a non-JSON string
        Then:
            - An error dictionary indicating an unexpected string result should be returned
        """
        # Given
        non_json_output = "Some unexpected success message that isn't JSON"
        mock_run_gh.return_value = non_json_output
        mock_resolve_param.side_effect = lambda cap, param, val: None

        # When
        result = _create_pull_request_impl(
            owner="owner",
            repo="repo",
            title="Weird String PR",
            head="branch-a",
            base="main",
        )

        # Then
        expected_error = {
            "error": "Unexpected string result from gh pr create",
            "raw": non_json_output,
        }
        assert result == expected_error


class TestPullRequestChecks:
    """Tests for the _checks_github_pull_request_impl function.
    
    This test class verifies the functionality for checking the status of GitHub
    pull request checks/statuses, handling different parameters, and error scenarios.
    """

    # Test data
    MOCK_CHECKS_JSON = {
        "checks": [
            {"name": "build", "status": "SUCCESS", "conclusion": "SUCCESS"},
            {"name": "test", "status": "FAILURE", "conclusion": "FAILURE"},
            {"name": "lint", "status": "PENDING", "conclusion": None},
        ],
        "failing": 1,
        "passing": 1,
        "pending": 1,
        "status": "failure",  # Overall status
    }

    def test_pr_checks_success_current_branch(self, mock_run_gh: "MagicMock") -> None:
        """Test fetching checks for the current branch PR successfully.
        
        Given:
            - A request for checks on the current branch's PR
        When:
            - _checks_github_pull_request_impl is called with no identifier
        Then:
            - run_gh_command is called correctly, and the JSON result is returned
        """
        # Given
        mock_run_gh.return_value = self.MOCK_CHECKS_JSON

        # When
        result = _checks_github_pull_request_impl(owner="owner", repo="repo")

        # Then
        expected_command = [
            "pr",
            "checks",
            "--repo",
            "owner/repo",
            "--json",
            "checks,failing,passing,pending,status",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == self.MOCK_CHECKS_JSON

    def test_pr_checks_success_specific_pr(self, mock_run_gh: "MagicMock") -> None:
        """Test fetching checks for a specific PR identifier successfully.
        
        Given:
            - A request for checks on a specific PR number
        When:
            - _checks_github_pull_request_impl is called with pr_identifier=123
        Then:
            - run_gh_command is called correctly, and the JSON result is returned
        """
        # Given
        mock_run_gh.return_value = self.MOCK_CHECKS_JSON

        # When
        result = _checks_github_pull_request_impl(
            owner="owner", repo="repo", pr_identifier=123
        )

        # Then
        expected_command = [
            "pr",
            "checks",
            "123",
            "--repo",
            "owner/repo",
            "--json",
            "checks,failing,passing,pending,status",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == self.MOCK_CHECKS_JSON

    def test_pr_checks_success_with_flags(self, mock_run_gh: "MagicMock") -> None:
        """Test fetching checks with fail-fast and required flags.
        
        Given:
            - A request for checks with flags enabled
        When:
            - _checks_github_pull_request_impl is called with fail_fast=True, required=True
        Then:
            - run_gh_command is called with the correct flags
        """
        # Given
        mock_run_gh.return_value = self.MOCK_CHECKS_JSON

        # When
        result = _checks_github_pull_request_impl(
            owner="owner", repo="repo", pr_identifier="main", fail_fast=True, required=True
        )

        # Then
        expected_command = [
            "pr",
            "checks",
            "main",
            "--repo",
            "owner/repo",
            "--json",
            "checks,failing,passing,pending,status",
            "--fail-fast",
            "--required",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == self.MOCK_CHECKS_JSON

    def test_pr_checks_gh_error(self, mock_run_gh: "MagicMock") -> None:
        """Test error handling when gh fails fetching PR checks.
        
        Given:
            - A request for checks
        When:
            - run_gh_command returns an error
        Then:
            - The error dictionary is returned directly
        """
        # Given
        error_output = {"error": "gh command failed", "stderr": "PR not found"}
        mock_run_gh.return_value = error_output

        # When
        result = _checks_github_pull_request_impl(
            owner="owner", repo="repo", pr_identifier=999
        )

        # Then
        assert result == error_output
        mock_run_gh.assert_called_once()


class TestCheckoutPullRequest:
    """Tests for the _checkout_github_pull_request_impl function.
    
    This test class verifies the functionality for checking out GitHub pull requests
    locally, handling different parameters, and error scenarios.
    """

    def test_pr_checkout_success_simple(self, mock_run_gh: "MagicMock") -> None:
        """Test checking out a PR branch with a simple identifier.
        
        Given:
            - A request to checkout a PR branch
        When:
            - _checkout_github_pull_request_impl is called
        Then:
            - run_gh_command is called correctly, and success status is returned
        """
        # Given
        mock_run_gh.return_value = "Checked out branch 'feature-branch' for PR #123"

        # When
        result = _checkout_github_pull_request_impl(
            owner="owner", repo="repo", pr_identifier=123
        )

        # Then
        expected_command = ["pr", "checkout", "123", "--repo", "owner/repo"]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result.get("status") == "success"
        assert "Checked out branch" in result.get("message", "")

    def test_pr_checkout_success_with_flags(self, mock_run_gh: "MagicMock") -> None:
        """Test checking out a PR branch with various flags enabled.
        
        Given:
            - A request to checkout a PR branch with flags
        When:
            - _checkout_github_pull_request_impl is called with flags
        Then:
            - run_gh_command is called with the correct flags
        """
        # Given
        mock_run_gh.return_value = "Checked out branch 'local-name' for PR owner/repo#124"

        # When
        result = _checkout_github_pull_request_impl(
            owner="owner",
            repo="repo",
            pr_identifier="https://github.com/owner/repo/pull/124",
            checkout_branch_name="local-name",
            recurse_submodules=True,
            force=True,
            detach=False,  # Explicitly false
        )

        # Then
        expected_command = [
            "pr",
            "checkout",
            "https://github.com/owner/repo/pull/124",
            "--repo",
            "owner/repo",
            "--branch",
            "local-name",
            "--recurse-submodules",
            "--force",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result.get("status") == "success"

    def test_pr_checkout_gh_error(self, mock_run_gh: "MagicMock") -> None:
        """Test error handling when gh fails checking out a PR branch.
        
        Given:
            - A request to checkout a PR branch
        When:
            - run_gh_command returns an error
        Then:
            - The error dictionary is returned directly
        """
        # Given
        error_output = {
            "error": "gh command failed",
            "stderr": "Local branch already exists",
        }
        mock_run_gh.return_value = error_output

        # When
        result = _checkout_github_pull_request_impl(
            owner="owner", repo="repo", pr_identifier=125
        )

        # Then
        assert result == error_output
        mock_run_gh.assert_called_once()


class TestClosePullRequest:
    """Tests for the _close_github_pull_request_impl function.
    
    This test class verifies the functionality for closing GitHub pull requests,
    handling different parameters, and error scenarios.
    """

    def test_pr_close_success_simple(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test closing a PR successfully with a simple identifier.
        
        Given:
            - A request to close a PR
        When:
            - _close_github_pull_request_impl is called
        Then:
            - run_gh_command is called correctly, and success status is returned
        """
        # Given
        mock_run_gh.return_value = "Closed pull request #130"
        mock_resolve_param.return_value = None  # No default comment

        # When
        result = _close_github_pull_request_impl(
            owner="owner", repo="repo", pr_identifier=130
        )

        # Then
        expected_command = ["pr", "close", "130", "--repo", "owner/repo"]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result.get("status") == "success"
        assert "Closed pull request" in result.get("message", "")

    def test_pr_close_success_with_comment_and_delete(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test closing a PR with a comment and deleting the branch.
        
        Given:
            - A request to close a PR with comment and delete branch
        When:
            - _close_github_pull_request_impl is called with flags
        Then:
            - run_gh_command is called with the correct flags
        """
        # Given
        mock_run_gh.return_value = (
            "Closed pull request owner/repo#131 and deleted branch 'feature'"
        )

        # Use side_effect to target specific param
        def side_effect(cap: str, param: str, val: Any, *args: Any, **kwargs: Any) -> Any:
            if cap == "pull_request" and param == "close_comment":
                return "Closing this PR."
            return None  # Default for other potential resolves

        mock_resolve_param.side_effect = side_effect

        # When
        result = _close_github_pull_request_impl(
            owner="owner",
            repo="repo",
            pr_identifier="https://github.com/owner/repo/pull/131",
            comment="ignored",  # Runtime value, will be passed to resolve_param
            delete_branch=True,
        )

        # Then
        expected_command = [
            "pr",
            "close",
            "https://github.com/owner/repo/pull/131",
            "--repo",
            "owner/repo",
            "--comment",
            "Closing this PR.",  # Assert expects the resolved value
            "--delete-branch",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result.get("status") == "success"
        assert "Closed pull request" in result.get("message", "")
        assert "deleted branch" in result.get("message", "")

    def test_pr_close_gh_error(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test error handling when gh fails closing a PR.
        
        Given:
            - A request to close a PR
        When:
            - run_gh_command returns an error
        Then:
            - The error dictionary is returned directly
        """
        # Given
        error_output = {"error": "gh command failed", "stderr": "PR already closed"}
        mock_run_gh.return_value = error_output
        mock_resolve_param.return_value = None  # No default comment

        # When
        result = _close_github_pull_request_impl(
            owner="owner", repo="repo", pr_identifier=132
        )

        # Then
        assert result == error_output
        mock_run_gh.assert_called_once()


class TestEditPullRequest:
    """Tests for the _edit_github_pull_request_impl function.
    
    This test class verifies the functionality for editing GitHub pull requests,
    handling different parameter combinations, add/remove operations, and error scenarios.
    """

    def test_pr_edit_success_minimal(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test editing only the title of a PR successfully.
        
        Given:
            - A request to edit only the title of a PR
        When:
            - _edit_github_pull_request_impl is called
        Then:
            - run_gh_command is called correctly, and the URL is returned
        """
        # Given
        pr_url = "https://github.com/owner/repo/pull/160"
        mock_run_gh.return_value = pr_url
        mock_resolve_param.side_effect = (
            lambda cap, param, val, *args, **kwargs: val
        )  # Pass through runtime

        # When
        result = _edit_github_pull_request_impl(
            owner="owner", repo="repo", pr_identifier=160, title="New PR Title"
        )

        # Then
        expected_command = [
            "pr",
            "edit",
            "160",
            "--repo",
            "owner/repo",
            "--title",
            "New PR Title",
            # Body should not be added if None and config doesn't provide default
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == {"status": "success", "url": pr_url}

    def test_pr_edit_add_remove_multiple(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test editing multiple fields (add/remove assignees/labels/reviewers).
        
        Given:
            - A request to edit multiple fields (add/remove labels/reviewers etc)
        When:
            - _edit_github_pull_request_impl is called
        Then:
            - run_gh_command is called with multiple repeated flags
        """
        # Given
        pr_url = "https://github.com/owner/repo/pull/161"
        mock_run_gh.return_value = pr_url
        # Simulate milestone and body resolving to None
        mock_resolve_param.side_effect = lambda cap, param, val, *args, **kwargs: None

        # When
        result = _edit_github_pull_request_impl(
            owner="owner",
            repo="repo",
            pr_identifier=161,
            add_labels=["bug", "prio:high"],
            remove_labels=["needs-triage"],
            add_reviewers=["user1"],
            remove_reviewers=["user2", "user3"],
            add_assignees=["devA"],
            remove_assignees=["devB"],
        )

        # Then
        expected_command = [
            "pr",
            "edit",
            "161",
            "--repo",
            "owner/repo",
            "--add-assignee",
            "devA",
            "--remove-assignee",
            "devB",
            "--add-label",
            "bug",
            "--add-label",
            "prio:high",
            "--remove-label",
            "needs-triage",
            "--add-reviewer",
            "user1",
            "--remove-reviewer",
            "user2",
            "--remove-reviewer",
            "user3",
            # No projects added/removed in this test
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == {"status": "success", "url": pr_url}

    def test_pr_edit_with_milestone_and_body(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test editing the milestone and body of a PR.
        
        Given:
            - A request to edit the milestone and body
        When:
            - _edit_github_pull_request_impl is called
        Then:
            - run_gh_command includes the flags based on resolved values
        """
        # Given
        pr_url = "https://github.com/owner/repo/pull/162"
        mock_run_gh.return_value = pr_url

        # Simulate milestone and body resolving
        def side_effect(cap: str, param: str, val: Any, *args: Any, **kwargs: Any) -> Any:
            if cap == "pull_request" and param == "edit_milestone":
                return "v2.0"
            if cap == "pull_request" and param == "body":
                return "New body content"
            return None

        mock_resolve_param.side_effect = side_effect

        # When
        result = _edit_github_pull_request_impl(
            owner="owner",
            repo="repo",
            pr_identifier=162,
            milestone="ignored",
            body="ignored",  # Runtime ignored due to mock
        )

        # Then
        expected_command = [
            "pr",
            "edit",
            "162",
            "--repo",
            "owner/repo",
            "--body",
            "New body content",
            "--milestone",
            "v2.0",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == {"status": "success", "url": pr_url}

    def test_pr_edit_gh_error(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test error handling when gh fails editing a PR.
        
        Given:
            - A request to edit a PR
        When:
            - run_gh_command returns an error
        Then:
            - The error dictionary is returned directly
        """
        # Given
        error_output = {"error": "gh command failed", "stderr": "Milestone not found"}
        mock_run_gh.return_value = error_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, *args, **kwargs: val
        )  # Pass through

        # When
        result = _edit_github_pull_request_impl(
            owner="owner", repo="repo", pr_identifier=163, title="Error Test"
        )

        # Then
        assert result == error_output
        mock_run_gh.assert_called_once()


class TestListPullRequests:
    """Tests for the _list_github_pull_requests_impl function.
    
    This test class verifies the functionality for listing GitHub pull requests,
    handling different parameters, filters, and error scenarios.
    """

    # Test data
    MOCK_PR_LIST_ITEM = {
        "number": 170,
        "title": "List PR Example",
        "state": "OPEN",
        "url": "https://github.com/owner/repo/pull/170",
        "labels": [{"name": "bug"}],
        "assignees": [{"login": "dev1"}],
        "author": {"login": "userX"},
        "baseRefName": "main",
        "headRefName": "feature/list",
    }

    def test_pr_list_success_minimal(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test listing PRs with minimal parameters (using defaults).
        
        Given:
            - A request to list PRs with minimal parameters
        When:
            - _list_github_pull_requests_impl is called, resolving defaults
        Then:
            - run_gh_command is called with defaults, and the list is returned
        """
        # Given
        mock_run_gh.return_value = [self.MOCK_PR_LIST_ITEM]

        # Simulate resolving defaults
        def side_effect(cap: str, param: str, val: Any, *args: Any, **kwargs: Any) -> Any:
            if val is not None:
                return val
            if param == "list_limit":
                return 30
            if param == "list_state":
                return "open"
            return None  # Others resolve to None

        mock_resolve_param.side_effect = side_effect

        # When
        result = _list_github_pull_requests_impl(owner="owner", repo="repo")

        # Then
        expected_command = [
            "pr",
            "list",
            "--repo",
            "owner/repo",
            "--limit",
            "30",
            "--json",
            "number,title,state,url,labels,assignees,author,baseRefName,headRefName",
            "--state",
            "open",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == [self.MOCK_PR_LIST_ITEM]

    def test_pr_list_success_all_filters(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test listing PRs with all available filters applied.
        
        Given:
            - A request to list PRs with all filters applied
        When:
            - _list_github_pull_requests_impl is called
        Then:
            - run_gh_command is called with all filter flags
        """
        # Given
        mock_run_gh.return_value = []  # Assume filters return empty list
        # Simulate pass-through resolution
        mock_resolve_param.side_effect = lambda cap, param, val, *args, **kwargs: val

        # When
        result = _list_github_pull_requests_impl(
            owner="owner",
            repo="repo",
            state="merged",
            limit=5,
            labels=["frontend", "perf"],
            assignee="dev2",
            author="userY",
            base="release-v1",
            head="hotfix-123",
        )

        # Then
        expected_command = [
            "pr",
            "list",
            "--repo",
            "owner/repo",
            "--limit",
            "5",
            "--json",
            "number,title,state,url,labels,assignees,author,baseRefName,headRefName",
            "--state",
            "merged",
            "--assignee",
            "dev2",
            "--author",
            "userY",
            "--base",
            "release-v1",
            "--head",
            "hotfix-123",
            "--label",
            "frontend,perf",  # Comma-joined
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == []

    def test_pr_list_gh_error(
        self, 
        mock_run_gh: "MagicMock", 
        mock_resolve_param: "MagicMock"
    ) -> None:
        """Test error handling when gh fails listing PRs.
        
        Given:
            - A request to list PRs
        When:
            - run_gh_command returns an error
        Then:
            - The error is returned wrapped in a list
        """
        # Given
        error_output = {"error": "gh command failed", "stderr": "Invalid state"}
        mock_run_gh.return_value = error_output
        # Mock default resolution for limit/state
        mock_resolve_param.side_effect = lambda cap, param, val, *args, **kwargs: (
            # Use correct param names from implementation for resolution
            30 if param == "pr_limit" else ("open" if param == "pr_state" else None)
        )

        # When
        with patch("builtins.print"):
            result = _list_github_pull_requests_impl(owner="owner", repo="repo")

        # Then
        assert result == [error_output]  # Error is wrapped in a list
        mock_run_gh.assert_called_once()
