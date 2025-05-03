"""Unit tests for the pull_requests tool module."""

# tests/unit/tools/test_pull_requests.py
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

# Assuming TOOL_PARAM_CONFIG might be needed for body resolution check
from gh_project_manager_mcp.config import TOOL_PARAM_CONFIG

# Function to test
from gh_project_manager_mcp.tools.pull_requests import (
    _checkout_github_pull_request_impl,
    _close_github_pull_request_impl,
    _create_pull_request_impl,
    _diff_github_pull_request_impl,
    _edit_github_pull_request_impl,
    _list_github_pull_requests_impl,
    _ready_github_pull_request_impl,
    _reopen_github_pull_request_impl,
    _review_github_pull_request_impl,
    _status_github_pull_request_impl,
    _update_branch_github_pull_request_impl,
    _view_github_pull_request_impl,
)

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

# --- Fixtures ---


@pytest.fixture
def mock_resolve_param() -> "MagicMock":
    """Provide a mock for the resolve_param utility function.

    This fixture mocks the resolve_param function imported in the pull_requests module,
    with a default behavior that passes through runtime values.

    Returns
    -------
        The mock object for resolve_param that can be customized in tests.

    """
    with patch(
        "gh_project_manager_mcp.tools.pull_requests.resolve_param"
    ) as mocker_fixture:
        # Default behavior: return runtime value if not None, else None/default
        # Body has special handling in create_pr, might need
        # refinement if body default exists
        def side_effect(
            capability: str,
            param_name: str,
            runtime_value: Any,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            # Body has special handling in create_pr, might need
            # refinement if body default exists
            if param_name == "body":
                # Simulate config check: only resolve if 'body' is configured,
                # else return runtime value
                if "body" in TOOL_PARAM_CONFIG.get(capability, {}):
                    return runtime_value  # Let implementation handle None -> ""
                else:
                    return runtime_value  # Return as-is if not in config
            # Default behavior for other params
            if runtime_value is not None:
                return runtime_value
            # Simplistic mock: just return None if runtime is None for non-body
            return None

        mocker_fixture.side_effect = side_effect
        yield mocker_fixture


@pytest.fixture
def mock_run_gh() -> "MagicMock":
    """Provide a mock for the run_gh_command utility function.

    This fixture mocks the run_gh_command function imported in the pull_requests module,
    allowing tests to control what the command returns.

    Returns
    -------
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

    def test_create_pr_minimal(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
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
            owner="owner",
            repo="repo",
            title="New PR",
            head="feature-branch",
            base="main",
        )

        # Then
        expected_command = [
            "pr",
            "create",
            "--repo",
            "owner/repo",
            "--base",
            "main",
            "--head",
            "feature-branch",
            "--title",
            "New PR",
            "--body",
            "",  # Always includes body
            "--json",
            "url,number,title,body,state",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_result

    def test_create_pr_all_params(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test creating a PR with all parameters provided.

        Given:
            - A request to create a PR with all parameters provided
        When:
            - _create_pull_request_impl is called
        Then:
            - run_gh_command is called with all parameters correctly
              added to the command
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
            draft=True,
        )

        # Then
        expected_command = [
            "pr",
            "create",
            "--repo",
            "owner/repo",
            "--base",
            "develop",
            "--head",
            "feature-x",
            "--title",
            "Full PR",
            "--body",
            "PR body content.",
            "--json",
            "url,number,title,body,state",
            "--draft",
            "--reviewer",
            "lead_dev",
            "--reviewer",
            "qa_tester",
            "--label",
            "needs-review",
            "--label",
            "frontend",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_result

    def test_create_pr_reviewers_labels_resolved_string(
        self,
        mock_run_gh: "MagicMock",
        mock_resolve_param: "MagicMock",
        mocker: "MockerFixture",
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
                return None  # Simulate body not resolved
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
            pr_labels=[],
        )

        # Then
        expected_command = [
            "pr",
            "create",
            "--repo",
            "owner/repo",
            "--base",
            "main",
            "--head",
            "feat/z",
            "--title",
            "String Resolve PR",
            "--body",
            "",
            "--json",
            "url,number,title,body,state",
            "--reviewer",
            "rev1",
            "--reviewer",
            "rev2",
            "--label",
            "label_a",
            "--label",
            "label_b",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_result

    def test_create_pr_gh_command_error(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
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

    def test_create_pr_gh_command_non_json_string(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test handling unexpected non-JSON string output from gh pr create.

        Given:
            - A request to create a PR with the --json flag requested
        When:
            - run_gh_command returns a non-JSON string
        Then:
            - An error dictionary indicating an unexpected string result
              should be returned
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
        mock_run_gh.return_value = (
            "Checked out branch 'local-name' for PR owner/repo#124"
        )

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
        def side_effect(
            cap: str, param: str, val: Any, *args: Any, **kwargs: Any
        ) -> Any:
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
    handling different parameter combinations, add/remove operations, and error
    scenarios.
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
        def side_effect(
            cap: str, param: str, val: Any, *args: Any, **kwargs: Any
        ) -> Any:
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

    def test_edit_with_assignees(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test editing a PR with assignees.

        Given:
            - PR edit with add and remove assignees
        When:
            - _edit_github_pull_request_impl is called
        Then:
            - Correct command is built with assignee flags
        """
        # Given
        owner = "octocat"
        repo = "hello-world"
        pr_number = 42
        add_assignees = ["user1", "user2"]
        remove_assignees = ["user3"]
        expected_result = "https://github.com/octocat/hello-world/pull/42"

        # Configure mocks
        mock_run_gh.return_value = expected_result
        mock_resolve_param.return_value = None

        # When
        result = _edit_github_pull_request_impl(
            owner=owner,
            repo=repo,
            pr_identifier=pr_number,
            add_assignees=add_assignees,
            remove_assignees=remove_assignees,
        )

        # Then
        expected_command = [
            "pr",
            "edit",
            str(pr_number),
            "--repo",
            f"{owner}/{repo}",
            "--add-assignee",
            "user1",
            "--add-assignee",
            "user2",
            "--remove-assignee",
            "user3",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["url"] == expected_result

    def test_edit_with_labels(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test editing a PR with labels.

        Given:
            - PR edit with add and remove labels
        When:
            - _edit_github_pull_request_impl is called
        Then:
            - Correct command is built with label flags
        """
        # Given
        owner = "octocat"
        repo = "hello-world"
        pr_number = 42
        add_labels = ["bug", "enhancement"]
        remove_labels = ["question"]
        expected_result = "https://github.com/octocat/hello-world/pull/42"

        # Configure mocks
        mock_run_gh.return_value = expected_result
        mock_resolve_param.return_value = None

        # When
        result = _edit_github_pull_request_impl(
            owner=owner,
            repo=repo,
            pr_identifier=pr_number,
            add_labels=add_labels,
            remove_labels=remove_labels,
        )

        # Then
        expected_command = [
            "pr",
            "edit",
            str(pr_number),
            "--repo",
            f"{owner}/{repo}",
            "--add-label",
            "bug",
            "--add-label",
            "enhancement",
            "--remove-label",
            "question",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["url"] == expected_result

    def test_edit_with_projects(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test editing a PR with projects.

        Given:
            - PR edit with add and remove projects
        When:
            - _edit_github_pull_request_impl is called
        Then:
            - Correct command is built with project flags
        """
        # Given
        owner = "octocat"
        repo = "hello-world"
        pr_number = 42
        add_projects = ["Project1", "Project2"]
        remove_projects = ["OldProject"]
        expected_result = "https://github.com/octocat/hello-world/pull/42"

        # Configure mocks
        mock_run_gh.return_value = expected_result
        mock_resolve_param.return_value = None

        # When
        result = _edit_github_pull_request_impl(
            owner=owner,
            repo=repo,
            pr_identifier=pr_number,
            add_projects=add_projects,
            remove_projects=remove_projects,
        )

        # Then
        expected_command = [
            "pr",
            "edit",
            str(pr_number),
            "--repo",
            f"{owner}/{repo}",
            "--add-project",
            "Project1",
            "--add-project",
            "Project2",
            "--remove-project",
            "OldProject",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["url"] == expected_result

    def test_edit_with_reviewers(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test editing a PR with reviewers.

        Given:
            - PR edit with add and remove reviewers
        When:
            - _edit_github_pull_request_impl is called
        Then:
            - Correct command is built with reviewer flags
        """
        # Given
        owner = "octocat"
        repo = "hello-world"
        pr_number = 42
        add_reviewers = ["reviewer1", "team/reviewers"]
        remove_reviewers = ["ex-reviewer"]
        expected_result = "https://github.com/octocat/hello-world/pull/42"

        # Configure mocks
        mock_run_gh.return_value = expected_result
        mock_resolve_param.return_value = None

        # When
        result = _edit_github_pull_request_impl(
            owner=owner,
            repo=repo,
            pr_identifier=pr_number,
            add_reviewers=add_reviewers,
            remove_reviewers=remove_reviewers,
        )

        # Then
        expected_command = [
            "pr",
            "edit",
            str(pr_number),
            "--repo",
            f"{owner}/{repo}",
            "--add-reviewer",
            "reviewer1",
            "--add-reviewer",
            "team/reviewers",
            "--remove-reviewer",
            "ex-reviewer",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["url"] == expected_result

    def test_unexpected_result(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test handling of unexpected result formats.

        Given:
            - PR edit parameters
            - run_gh_command returns something other than a string URL or error dict
        When:
            - _edit_github_pull_request_impl is called
        Then:
            - An error dictionary with the raw value is returned
        """
        # Given
        owner = "octocat"
        repo = "hello-world"
        pr_number = 42
        unexpected_result = None  # Unusual return value

        # Configure mocks
        mock_run_gh.return_value = unexpected_result
        mock_resolve_param.return_value = None

        # When
        result = _edit_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_number, title="New Title"
        )

        # Then
        assert "error" in result
        assert result["error"] == "Unexpected result from gh pr edit"
        assert result["raw"] == unexpected_result


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
        def side_effect(
            cap: str, param: str, val: Any, *args: Any, **kwargs: Any
        ) -> Any:
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
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
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

    def test_list_prs_with_labels_type_hint(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test listing PRs with labels processed through type_hint="list".

        Given:
            - Repository owner and name
            - Labels parameter that should be processed
        When:
            - _list_github_pull_requests_impl is called
        Then:
            - resolve_param is called with the correct parameters for labels
        """
        # Given
        test_owner = "test-owner"
        test_repo = "test-repo"
        test_labels = ["bug", "help wanted"]

        # Reset the mock to clear any previous calls
        mock_resolve_param.reset_mock()

        # Configure the mock to return the labels when asked for them
        # Note: The implementation uses 'list_labels' (not 'pr_labels')
        mock_resolve_param.side_effect = lambda cap, name, val, **kwargs: (
            test_labels if name == "list_labels" else None
        )

        mock_run_gh.return_value = [{"number": 123, "title": "PR with labels"}]

        # When
        result = _list_github_pull_requests_impl(
            owner=test_owner, repo=test_repo, labels=test_labels
        )

        # Then
        # Check that the mock was called with correct parameters through inspection
        # rather than using assert_any_call
        call_args_list = mock_resolve_param.call_args_list
        found_list_labels_call = False

        for args, kwargs in call_args_list:
            # Check if this call matches what we're looking for
            if (
                len(args) >= 3
                and args[0] == "pull_request"
                and args[1] == "list_labels"
                and args[2] == test_labels
            ):
                found_list_labels_call = True
                break

        assert (
            found_list_labels_call
        ), "resolve_param was not called with expected arguments"

        # Verify the result is processed correctly
        assert result == mock_run_gh.return_value


# --- Test _update_branch_github_pull_request_impl ---


class TestUpdateBranchPullRequest:
    """Tests for the _update_branch_github_pull_request_impl function."""

    def test_update_branch_pr_success(self, mock_run_gh: MagicMock) -> None:
        """Test successfully updating a PR branch.

        Given: Valid PR identifier
        When: _update_branch_github_pull_request_impl is called
        Then: gh update-branch command is called correctly and output is returned
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        success_response = "Pull request #123 branch 'feature-branch' has been updated"
        mock_run_gh.return_value = success_response

        # When
        result = _update_branch_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier
        )

        # Then
        expected_command = [
            "pr",
            "update-branch",
            "123",
            "--repo",
            "test-owner/test-repo",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["message"] == success_response

    def test_update_branch_pr_with_rebase(self, mock_run_gh: MagicMock) -> None:
        """Test updating a PR branch with rebase option.

        Given: Valid PR identifier with rebase=True
        When: _update_branch_github_pull_request_impl is called
        Then: gh update-branch command is called with --rebase flag
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        success_response = "Pull request #123 branch 'feature-branch' has been rebased"
        mock_run_gh.return_value = success_response

        # When
        result = _update_branch_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier, rebase=True
        )

        # Then
        expected_command = [
            "pr",
            "update-branch",
            "123",
            "--repo",
            "test-owner/test-repo",
            "--rebase",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["message"] == success_response

    def test_update_branch_pr_without_pr_identifier(
        self, mock_run_gh: MagicMock
    ) -> None:
        """Test updating current PR branch.

        Given: No PR identifier provided
        When: _update_branch_github_pull_request_impl is called
        Then: gh update-branch command is called without a PR identifier
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        success_response = "Current branch 'feature-branch' has been updated"
        mock_run_gh.return_value = success_response

        # When
        result = _update_branch_github_pull_request_impl(owner=owner, repo=repo)

        # Then
        expected_command = ["pr", "update-branch", "--repo", "test-owner/test-repo"]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["message"] == success_response

    def test_update_branch_pr_empty_response(self, mock_run_gh: MagicMock) -> None:
        """Test handling empty response.

        Given: gh command returns an empty string
        When: _update_branch_github_pull_request_impl is called
        Then: Function returns a default success message
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        mock_run_gh.return_value = ""  # Empty string response

        # When
        result = _update_branch_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier
        )

        # Then
        assert result["status"] == "success"
        assert result["message"] == "PR branch updated."

    def test_update_branch_pr_gh_error(self, mock_run_gh: MagicMock) -> None:
        """Test handling of gh command error.

        Given: Valid parameters but gh command returning an error
        When: _update_branch_github_pull_request_impl is called
        Then: Error details are returned from the function
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        error_response = {"error": "Command failed", "details": "PR not found"}
        mock_run_gh.return_value = error_response

        # When
        result = _update_branch_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier
        )

        # Then
        assert result == error_response

    def test_update_branch_pr_non_string_non_error(
        self, mock_run_gh: MagicMock
    ) -> None:
        """Test handling non-string, non-error response.

        Given: gh command returns a non-string, non-error dict
        When: _update_branch_github_pull_request_impl is called
        Then: Function returns a generic success message
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        mock_run_gh.return_value = {"some_key": "some_value"}  # Not a string or error

        # When
        result = _update_branch_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier
        )

        # Then
        assert result["status"] == "success"
        assert result["message"] == "PR branch updated."


class TestDiffPullRequest:
    """Tests for the _diff_github_pull_request_impl function."""

    def test_diff_pr_success(self, mock_run_gh: MagicMock) -> None:
        """Test successful diff of a PR.

        Given: Valid PR identifier and parameters
        When: _diff_github_pull_request_impl is called
        Then: gh diff command is called correctly and output is returned
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        expected_diff = (
            "--- a/file.txt\n+++ b/file.txt\n@@ -1,1 +1,1 @@\n-old line\n+new line"
        )
        mock_run_gh.return_value = expected_diff

        # When
        result = _diff_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier
        )

        # Then
        expected_command = ["pr", "diff", "123", "--repo", "test-owner/test-repo"]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["diff"] == expected_diff

    def test_diff_pr_with_options(self, mock_run_gh: MagicMock) -> None:
        """Test PR diff with various options.

        Given: PR identifier with color, patch, and name-only options
        When: _diff_github_pull_request_impl is called
        Then: gh diff command is called with appropriate flags
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        color = "always"
        patch = True
        name_only = True
        mock_run_gh.return_value = "file1.txt\nfile2.txt"

        # When
        result = _diff_github_pull_request_impl(
            owner=owner,
            repo=repo,
            pr_identifier=pr_identifier,
            color=color,
            patch=patch,
            name_only=name_only,
        )

        # Then
        expected_command = [
            "pr",
            "diff",
            "123",
            "--repo",
            "test-owner/test-repo",
            "--color",
            "always",
            "--patch",
            "--name-only",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["diff"] == "file1.txt\nfile2.txt"

    def test_diff_pr_without_pr_identifier(self, mock_run_gh: MagicMock) -> None:
        """Test diff command without a PR identifier (current branch).

        Given: No PR identifier provided
        When: _diff_github_pull_request_impl is called
        Then: gh diff command is called without a PR identifier
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        mock_run_gh.return_value = "diff output"

        # When
        result = _diff_github_pull_request_impl(owner=owner, repo=repo)

        # Then
        expected_command = ["pr", "diff", "--repo", "test-owner/test-repo"]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["diff"] == "diff output"

    def test_diff_pr_invalid_color(self, mock_run_gh: MagicMock) -> None:
        """Test handling invalid color option.

        Given: An invalid color option
        When: _diff_github_pull_request_impl is called
        Then: gh diff command should ignore the invalid color option
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        invalid_color = "invalid"
        mock_run_gh.return_value = "diff output"

        # When
        with patch("sys.stderr"):  # Capturing the warning print
            result = _diff_github_pull_request_impl(
                owner=owner, repo=repo, pr_identifier=pr_identifier, color=invalid_color
            )

        # Then
        expected_command = ["pr", "diff", "123", "--repo", "test-owner/test-repo"]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["diff"] == "diff output"

    def test_diff_pr_gh_error(self, mock_run_gh: MagicMock) -> None:
        """Test handling of gh command error.

        Given: Valid parameters but gh command returning an error
        When: _diff_github_pull_request_impl is called
        Then: Error details are returned from the function
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        error_response = {"error": "Command failed", "details": "PR not found"}
        mock_run_gh.return_value = error_response

        # When
        result = _diff_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier
        )

        # Then
        assert result == error_response

    def test_diff_pr_unexpected_result(self, mock_run_gh: MagicMock) -> None:
        """Test handling unexpected result type.

        Given: Valid parameters but gh command returning an unexpected result type
        When: _diff_github_pull_request_impl is called
        Then: Function returns an error dictionary
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        mock_run_gh.return_value = {
            "not_error_key": "some value"
        }  # Not a string or error dict

        # When
        result = _diff_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier
        )

        # Then
        assert "error" in result
        assert "Unexpected result" in result["error"]
        assert "raw" in result


class TestReadyPullRequest:
    """Tests for the _ready_github_pull_request_impl function."""

    def test_ready_pr_success(self, mock_run_gh: MagicMock) -> None:
        """Test successfully marking a PR as ready for review.

        Given: Valid PR identifier
        When: _ready_github_pull_request_impl is called
        Then: gh ready command is called correctly and success is returned
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        success_response = "Pull request #123 is marked as ready for review"
        mock_run_gh.return_value = success_response

        # When
        result = _ready_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier
        )

        # Then
        expected_command = ["pr", "ready", "123", "--repo", "test-owner/test-repo"]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["message"] == success_response

    def test_ready_pr_gh_error(self, mock_run_gh: MagicMock) -> None:
        """Test handling of gh command error.

        Given: Valid parameters but gh command returning an error
        When: _ready_github_pull_request_impl is called
        Then: Error details are returned from the function
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        error_response = {"error": "Command failed", "details": "PR not found"}
        mock_run_gh.return_value = error_response

        # When
        result = _ready_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier
        )

        # Then
        assert result == error_response

    def test_ready_pr_empty_response(self, mock_run_gh: MagicMock) -> None:
        """Test handling empty response.

        Given: gh command returns an empty or non-string/non-error response
        When: _ready_github_pull_request_impl is called
        Then: Function returns a generic success message
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        mock_run_gh.return_value = None  # Empty or unexpected response

        # When
        result = _ready_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier
        )

        # Then
        assert result["status"] == "success"
        assert "Marked as ready successfully" in result["message"]


class TestReopenPullRequest:
    """Tests for the _reopen_github_pull_request_impl function."""

    def test_reopen_pr_success(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test successfully reopening a closed PR.

        Given: Valid PR identifier
        When: _reopen_github_pull_request_impl is called
        Then: gh reopen command is called correctly and success is returned
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        success_response = "Reopened pull request #123"
        mock_run_gh.return_value = success_response
        mock_resolve_param.return_value = None  # No comment

        # When
        result = _reopen_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier
        )

        # Then
        expected_command = ["pr", "reopen", "123", "--repo", "test-owner/test-repo"]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["message"] == success_response

    def test_reopen_pr_with_comment(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test reopening a PR with a comment.

        Given: Valid PR identifier with a reopening comment
        When: _reopen_github_pull_request_impl is called
        Then: gh reopen command is called with --comment flag
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        comment = "Reopening to address additional issues"
        success_response = "Reopened pull request #123"
        mock_run_gh.return_value = success_response
        mock_resolve_param.return_value = comment  # Return the comment

        # When
        result = _reopen_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier, comment=comment
        )

        # Then
        expected_command = [
            "pr",
            "reopen",
            "123",
            "--repo",
            "test-owner/test-repo",
            "--comment",
            comment,
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["message"] == success_response

    def test_reopen_pr_gh_error(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test handling of gh command error.

        Given: Valid parameters but gh command returning an error
        When: _reopen_github_pull_request_impl is called
        Then: Error details are returned from the function
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        error_response = {"error": "Command failed", "details": "PR not found"}
        mock_run_gh.return_value = error_response
        mock_resolve_param.return_value = None  # No comment

        # When
        result = _reopen_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier
        )

        # Then
        assert result == error_response

    def test_reopen_pr_empty_response(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test handling empty response.

        Given: gh command returns an empty or non-string/non-error response
        When: _reopen_github_pull_request_impl is called
        Then: Function returns a generic success message
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        mock_run_gh.return_value = None  # Empty or unexpected response
        mock_resolve_param.return_value = None  # No comment

        # When
        result = _reopen_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier
        )

        # Then
        assert result["status"] == "success"
        assert "Reopened successfully" in result["message"]


class TestReviewPullRequest:
    """Tests for the _review_github_pull_request_impl function."""

    def test_review_pr_approve(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test approving a PR.

        Given: Valid PR identifier with approve action
        When: _review_github_pull_request_impl is called
        Then: gh review command is called with --approve flag
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        action = "approve"
        success_response = "Approved pull request #123"
        mock_run_gh.return_value = success_response
        mock_resolve_param.return_value = None  # No body

        # When
        result = _review_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier, action=action
        )

        # Then
        expected_command = [
            "pr",
            "review",
            "123",
            "--repo",
            "test-owner/test-repo",
            "--approve",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["message"] == success_response

    def test_review_pr_request_changes(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test requesting changes on a PR.

        Given: Valid PR identifier with request_changes action and body
        When: _review_github_pull_request_impl is called
        Then: gh review command is called with --request-changes flag and body
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        action = "request_changes"
        body = "Please fix these issues before we can merge"
        success_response = "Requested changes on pull request #123"
        mock_run_gh.return_value = success_response
        mock_resolve_param.return_value = body  # Return the body

        # When
        result = _review_github_pull_request_impl(
            owner=owner,
            repo=repo,
            pr_identifier=pr_identifier,
            action=action,
            body=body,
        )

        # Then
        expected_command = [
            "pr",
            "review",
            "123",
            "--repo",
            "test-owner/test-repo",
            "--request-changes",
            "--body",
            body,
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["message"] == success_response

    def test_review_pr_comment(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test commenting on a PR.

        Given: Valid PR identifier with comment action and body
        When: _review_github_pull_request_impl is called
        Then: gh review command is called with --comment flag and body
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        action = "comment"
        body = "Looks good overall, just a few minor suggestions"
        success_response = "Added a review comment to pull request #123"
        mock_run_gh.return_value = success_response
        mock_resolve_param.return_value = body  # Return the body

        # When
        result = _review_github_pull_request_impl(
            owner=owner,
            repo=repo,
            pr_identifier=pr_identifier,
            action=action,
            body=body,
        )

        # Then
        expected_command = [
            "pr",
            "review",
            "123",
            "--repo",
            "test-owner/test-repo",
            "--comment",
            "--body",
            body,
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["message"] == success_response

    def test_review_pr_with_body_file(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test reviewing a PR with body_file.

        Given: Valid PR identifier with body_file parameter
        When: _review_github_pull_request_impl is called
        Then: gh review command is called with --body-file flag
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        action = "comment"
        body_file = "/path/to/review.md"
        success_response = "Added a review comment to pull request #123"
        mock_run_gh.return_value = success_response

        # Configure mock_resolve_param to return appropriate values
        def side_effect(cap, param, val):
            if param == "review_body":
                return None
            if param == "review_body_file":
                return body_file
            return None

        mock_resolve_param.side_effect = side_effect

        # When
        result = _review_github_pull_request_impl(
            owner=owner,
            repo=repo,
            pr_identifier=pr_identifier,
            action=action,
            body_file=body_file,
        )

        # Then
        expected_command = [
            "pr",
            "review",
            "123",
            "--repo",
            "test-owner/test-repo",
            "--comment",
            "--body-file",
            body_file,
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["message"] == success_response

    def test_review_pr_invalid_action(self, mock_run_gh: MagicMock) -> None:
        """Test handling of invalid review action.

        Given: Valid PR identifier with an invalid action
        When: _review_github_pull_request_impl is called
        Then: Error details are returned from the function
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        action = "invalid_action"

        # When
        result = _review_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier, action=action
        )

        # Then
        mock_run_gh.assert_not_called()
        assert "error" in result
        assert "Invalid action" in result["error"]

    def test_review_pr_error_body_with_approve(self, mock_run_gh: MagicMock) -> None:
        """Test error when trying to use body with approve action.

        Given: Valid PR identifier with approve action and body
        When: _review_github_pull_request_impl is called
        Then: Error is returned indicating approve doesn't allow body
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        action = "approve"
        body = "This should error"

        # When
        result = _review_github_pull_request_impl(
            owner=owner,
            repo=repo,
            pr_identifier=pr_identifier,
            action=action,
            body=body,
        )

        # Then
        mock_run_gh.assert_not_called()
        assert "error" in result
        assert "cannot be used with 'approve'" in result["error"]

    def test_review_pr_error_missing_body_for_comment(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test error when missing body for comment action.

        Given: Valid PR identifier with comment action but no body
        When: _review_github_pull_request_impl is called
        Then: Error is returned indicating body is required
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        action = "comment"
        mock_resolve_param.return_value = None  # No body resolved

        # When
        result = _review_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier, action=action
        )

        # Then
        mock_run_gh.assert_not_called()
        assert "error" in result
        assert "body/body_file is required" in result["error"]

    def test_review_pr_error_body_and_body_file(self, mock_run_gh: MagicMock) -> None:
        """Test error when both body and body_file are provided.

        Given: Valid PR identifier with both body and body_file
        When: _review_github_pull_request_impl is called
        Then: Error is returned indicating mutually exclusive parameters
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        action = "comment"
        body = "Comment body"
        body_file = "/path/to/file.md"

        # When
        result = _review_github_pull_request_impl(
            owner=owner,
            repo=repo,
            pr_identifier=pr_identifier,
            action=action,
            body=body,
            body_file=body_file,
        )

        # Then
        mock_run_gh.assert_not_called()
        assert "error" in result
        assert "mutually exclusive" in result["error"]

    def test_review_pr_error_stdin_body_file(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test error when body_file is set to stdin ('-').

        Given: Valid PR identifier with body_file as stdin
        When: _review_github_pull_request_impl is called
        Then: Error is returned indicating stdin is not supported
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        action = "comment"
        mock_resolve_param.side_effect = (
            lambda cap, param, val: "-" if param == "review_body_file" else None
        )

        # When
        result = _review_github_pull_request_impl(
            owner=owner,
            repo=repo,
            pr_identifier=pr_identifier,
            action=action,
            body_file="-",
        )

        # Then
        mock_run_gh.assert_not_called()
        assert "error" in result
        assert "stdin" in result["error"]

    def test_review_pr_gh_error(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test handling of gh command error.

        Given: Valid parameters but gh command returning an error
        When: _review_github_pull_request_impl is called
        Then: Error details are returned from the function
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        action = "approve"
        error_response = {"error": "Command failed", "details": "PR not found"}
        mock_run_gh.return_value = error_response
        mock_resolve_param.return_value = None  # No body

        # When
        result = _review_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier, action=action
        )

        # Then
        assert result == error_response

    def test_review_pr_empty_response(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test handling empty response.

        Given: gh command returns an empty or non-string/non-error response
        When: _review_github_pull_request_impl is called
        Then: Function returns a generic success message
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        action = "approve"
        mock_run_gh.return_value = None  # Empty or unexpected response
        mock_resolve_param.return_value = None  # No body

        # When
        result = _review_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier, action=action
        )

        # Then
        assert result["status"] == "success"
        assert "submitted (approve) successfully" in result["message"]


class TestStatusPullRequest:
    """Tests for the _status_github_pull_request_impl function."""

    def test_status_pr_success(self, mock_run_gh: MagicMock) -> None:
        """Test successfully getting PR status.

        Given: No specific parameters (uses current repo)
        When: _status_github_pull_request_impl is called
        Then: gh status command is called correctly and output is returned
        """
        # Given
        expected_status = {
            "createdBy": [{"number": 123, "title": "My PR"}],
            "mentioned": [],
            "reviewRequested": [],
        }
        mock_run_gh.return_value = expected_status

        # When
        result = _status_github_pull_request_impl()

        # Then
        expected_command = [
            "pr",
            "status",
            "--json",
            "createdBy,mentioned,reviewRequested",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_status

    def test_status_pr_empty_results(self, mock_run_gh: MagicMock) -> None:
        """Test handling empty PR status results.

        Given: No PRs match the status criteria
        When: _status_github_pull_request_impl is called
        Then: Function returns a message indicating no PRs found
        """
        # Given
        mock_run_gh.return_value = {}  # Empty dict from gh

        # When
        result = _status_github_pull_request_impl()

        # Then
        assert result["status"] == "success"
        assert "No pull requests found" in result["message"]

    def test_status_pr_gh_error(self, mock_run_gh: MagicMock) -> None:
        """Test handling of gh command error.

        Given: gh command returning an error
        When: _status_github_pull_request_impl is called
        Then: Error details are returned from the function
        """
        # Given
        error_response = {
            "error": "Command failed",
            "details": "Not in a git repository",
        }
        mock_run_gh.return_value = error_response

        # When
        result = _status_github_pull_request_impl()

        # Then
        assert result == error_response

    def test_status_pr_unexpected_result(self, mock_run_gh: MagicMock) -> None:
        """Test handling unexpected result type.

        Given: gh command returning an unexpected result type
        When: _status_github_pull_request_impl is called
        Then: Function returns an error dictionary
        """
        # Given
        mock_run_gh.return_value = "Not a dict"  # Should be a dict

        # When
        result = _status_github_pull_request_impl()

        # Then
        assert "error" in result
        assert "Unexpected result" in result["error"]
        assert "raw" in result


class TestViewPullRequest:
    """Tests for the _view_github_pull_request_impl function."""

    def test_view_pr_success(self, mock_run_gh: MagicMock) -> None:
        """Test successfully viewing a PR.

        Given: Valid PR identifier
        When: _view_github_pull_request_impl is called
        Then: gh view command is called correctly and PR data is returned
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        pr_data = {
            "number": 123,
            "title": "Test PR",
            "state": "OPEN",
            "url": "https://github.com/test-owner/test-repo/pull/123",
        }
        mock_run_gh.return_value = pr_data

        # When
        result = _view_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier
        )

        # Then
        expected_command = [
            "pr",
            "view",
            "123",
            "--repo",
            "test-owner/test-repo",
            "--json",
            "number,title,state,url,body,createdAt,updatedAt,labels,"
            "assignees,author,baseRefName,headRefName,comments,reviews",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == pr_data

    def test_view_pr_with_comments(self, mock_run_gh: MagicMock) -> None:
        """Test viewing a PR with comments flag.

        Given: Valid PR identifier with comments=True
        When: _view_github_pull_request_impl is called
        Then: gh view command is called with JSON fields including comments
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        pr_data = {
            "number": 123,
            "title": "Test PR",
            "comments": [{"author": "user1", "body": "Comment text"}],
            "reviews": [{"state": "APPROVED", "author": "user2"}],
        }
        mock_run_gh.return_value = pr_data

        # When
        result = _view_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier, comments=True
        )

        # Then
        # The --json should include comments and reviews regardless of the comments flag
        # because the function always includes them in the JSON request
        expected_command = [
            "pr",
            "view",
            "123",
            "--repo",
            "test-owner/test-repo",
            "--json",
            "number,title,state,url,body,createdAt,updatedAt,labels,"
            "assignees,author,baseRefName,headRefName,comments,reviews",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == pr_data

    def test_view_pr_gh_error(self, mock_run_gh: MagicMock) -> None:
        """Test handling of gh command error.

        Given: Valid parameters but gh command returning an error
        When: _view_github_pull_request_impl is called
        Then: Error details are returned from the function
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        error_response = {"error": "Command failed", "details": "PR not found"}
        mock_run_gh.return_value = error_response

        # When
        result = _view_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier
        )

        # Then
        assert result == error_response

    def test_view_pr_unexpected_result(self, mock_run_gh: MagicMock) -> None:
        """Test handling unexpected result type.

        Given: Valid parameters but gh command returning a non-dict, non-error
        When: _view_github_pull_request_impl is called
        Then: Function returns an error dictionary
        """
        # Given
        owner = "test-owner"
        repo = "test-repo"
        pr_identifier = "123"
        mock_run_gh.return_value = "Not a dict"  # Should be a dict

        # When
        result = _view_github_pull_request_impl(
            owner=owner, repo=repo, pr_identifier=pr_identifier
        )

        # Then
        assert "error" in result
        assert "Unexpected result" in result["error"]
        assert "raw" in result
