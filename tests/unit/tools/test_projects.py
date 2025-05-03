# tests/tools/test_projects.py
"""Unit tests for the GitHub projects tools."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

# Import implementations as they are added
from gh_project_manager_mcp.tools.projects import (
    _add_github_project_item_impl,
    _archive_github_project_item_impl,
    _create_github_project_field_impl,
    _create_github_project_item_impl,
    _delete_github_project_field_impl,
    _delete_github_project_item_impl,
    _edit_github_project_item_impl,
    _list_github_project_fields_impl,
    _list_github_project_items_impl,
    _view_github_project_impl,
)

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from _pytest.capture import CaptureFixture
    from pytest_mock import MockerFixture


# --- Fixtures ---
@pytest.fixture
def mock_run_gh() -> "MagicMock":
    """Provide a mock for the run_gh_command utility function.

    This fixture mocks the run_gh_command function imported in the projects module,
    allowing tests to control what the command returns.

    Returns
    -------
        The mock object for run_gh_command that can be customized in tests.

    """
    # Use the correct path for patching within the projects module
    with patch("gh_project_manager_mcp.tools.projects.run_gh_command") as mock:
        yield mock


@pytest.fixture
def mock_resolve_param(mocker: "MockerFixture") -> "MagicMock":
    """Provide a mock for the resolve_param utility function.

    This fixture mocks the resolve_param function imported in the projects module,
    with a default behavior that passes through runtime values.

    Returns
    -------
        The mock object for resolve_param that can be customized in tests.

    """
    # Use the correct path for patching within the projects module
    mock = mocker.patch("gh_project_manager_mcp.tools.projects.resolve_param")
    # Default behavior: return the value passed in
    mock.side_effect = lambda capability, param_name, value, type_hint=None: value
    return mock


@pytest.fixture
def mock_resolve_param_for_project_edit(mocker: "MockerFixture") -> "MagicMock":
    """Return a resolve_param mock pre-configured for project edit tests."""
    mock = mocker.patch("gh_project_manager_mcp.tools.projects.resolve_param")

    def side_effect(category, param, value, type_hint=None):
        if param == "item_edit_owner":
            return "test-owner"
        elif param == "item_edit_project_id":
            return "test-project-id"
        return value

    mock.side_effect = side_effect
    return mock


# --- Test Cases ---


class TestListGithubProjectFields:
    """Tests for the _list_github_project_fields_impl function.

    This test class verifies the functionality for listing GitHub project fields,
    handling different parameter combinations, and error scenarios.
    """

    # Test data
    MOCK_FIELD_LIST_ITEM = {
        "id": "PVTF_lADOB3Xs84AAzA0",
        "name": "Status",
        "dataType": "SINGLE_SELECT",
        # ... other potential fields like options
    }

    def test_success_basic(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test listing project fields with basic parameters.

        Given:
            - A project ID
            - Owner and limit resolving to None
        When:
            - _list_github_project_fields_impl is called
        Then:
            - run_gh_command is called with correct parameters
            - The function returns the expected output
        """
        # Given
        mock_project_id = 123
        expected_gh_output = [self.MOCK_FIELD_LIST_ITEM]
        mock_run_gh.return_value = expected_gh_output
        # Simulate owner and limit resolving to None (using default fixture behavior)
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: None

        expected_command = [
            "project",
            "field-list",
            str(mock_project_id),
            "--format",
            "json",
            # No owner or limit flags expected
        ]

        # When
        result = _list_github_project_fields_impl(project_id=mock_project_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_gh_output

    def test_success_with_owner_limit(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test listing project fields with owner and limit parameters.

        Given:
            - A project URL
            - Owner and limit parameters
        When:
            - _list_github_project_fields_impl is called with these parameters
        Then:
            - run_gh_command is called with all expected flags
            - The function returns the expected output
        """
        # Given
        mock_project_url = "https://github.com/orgs/my-org/projects/4"
        mock_owner = "my-org"
        mock_limit = 10
        expected_gh_output = []
        mock_run_gh.return_value = expected_gh_output
        # Simulate parameters resolving to the provided values
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: val

        expected_command = [
            "project",
            "field-list",
            mock_project_url,
            "--format",
            "json",
            "--owner",
            mock_owner,
            "--limit",
            str(mock_limit),
        ]

        # When
        result = _list_github_project_fields_impl(
            project_id=mock_project_url, owner=mock_owner, limit=mock_limit
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_gh_output

    def test_success_invalid_limit(
        self,
        mock_run_gh: "MagicMock",
        mock_resolve_param: "MagicMock",
        capsys: "CaptureFixture[str]",
    ) -> None:
        """Test listing project fields handles invalid limit value.

        Given:
            - A project ID
            - An owner parameter
            - An invalid limit value
        When:
            - _list_github_project_fields_impl is called
        Then:
            - A warning is printed to stderr
            - run_gh_command is called without the limit flag
            - The function returns the expected output
        """
        # Given
        mock_project_id = 456
        mock_owner = "test-user"
        mock_invalid_limit = 0
        expected_gh_output = [self.MOCK_FIELD_LIST_ITEM]
        mock_run_gh.return_value = expected_gh_output
        # Simulate owner resolving, but limit resolving to the invalid value
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: val

        expected_command = [
            "project",
            "field-list",
            str(mock_project_id),
            "--format",
            "json",
            "--owner",
            mock_owner,
            # No limit flag expected
        ]

        # When
        _list_github_project_fields_impl(
            project_id=mock_project_id, owner=mock_owner, limit=mock_invalid_limit
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        captured = capsys.readouterr()
        assert f"Warning: Invalid limit '{mock_invalid_limit}'" in captured.err

    def test_gh_error(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test error handling when gh fails listing project fields.

        Given:
            - A project ID
            - run_gh_command returns an error dictionary
        When:
            - _list_github_project_fields_impl is called
        Then:
            - The error dictionary is returned, wrapped in a list
        """
        # Given
        mock_project_id = 789
        error_output = {
            "error": "gh command failed",
            "stderr": "Project not found",
            "exit_code": 1,
        }
        mock_run_gh.return_value = error_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # Resolve to None

        expected_command = [
            "project",
            "field-list",
            str(mock_project_id),
            "--format",
            "json",
        ]

        # When
        result = _list_github_project_fields_impl(project_id=mock_project_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == [error_output]  # Error is wrapped in a list

    def test_unexpected_output(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test handling unexpected non-list/non-error output for field list.

        Given:
            - A project ID
            - run_gh_command returns a non-list, non-error output
        When:
            - _list_github_project_fields_impl is called
        Then:
            - An error dictionary is returned, wrapped in a list
        """
        # Given
        mock_project_id = 101
        unexpected_output = "Some plain string"
        mock_run_gh.return_value = unexpected_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # Resolve to None

        expected_command = [
            "project",
            "field-list",
            str(mock_project_id),
            "--format",
            "json",
        ]
        expected_error = {
            "error": "Unexpected result from gh project field-list",
            "raw": unexpected_output,
        }

        # When
        result = _list_github_project_fields_impl(project_id=mock_project_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == [expected_error]  # Error is wrapped in a list

    def test_old_gh_format(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test handling old gh output format ({'fields': [...]}) for field list.

        Given:
            - A project ID
            - run_gh_command returns data in the old format with a 'fields' key
        When:
            - _list_github_project_fields_impl is called
        Then:
            - The inner list from the 'fields' key is returned
        """
        # Given
        mock_project_id = 112
        old_format_output = {
            "fields": [self.MOCK_FIELD_LIST_ITEM, {"id": "other", "name": "Priority"}]
        }
        mock_run_gh.return_value = old_format_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # Resolve to None

        expected_command = [
            "project",
            "field-list",
            str(mock_project_id),
            "--format",
            "json",
        ]

        # When
        result = _list_github_project_fields_impl(project_id=mock_project_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == old_format_output["fields"]  # Should extract the list

    def test_edge_case_unexpected_other_output(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test handling edge case unexpected output format for field list.

        Given:
            - A project ID
            - run_gh_command returns a format that's not a list, error dict, or dict with 'fields'
        When:
            - _list_github_project_fields_impl is called
        Then:
            - An error dictionary is returned, wrapped in a list
        """
        # Given
        mock_project_id = 101
        # Return non-error dict without 'fields' key
        unexpected_output = {"something_else": "value"}
        mock_run_gh.return_value = unexpected_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # Resolve to None

        expected_command = [
            "project",
            "field-list",
            str(mock_project_id),
            "--format",
            "json",
        ]
        expected_error = {
            "error": "Unexpected result from gh project field-list",
            "raw": unexpected_output,
        }

        # When
        result = _list_github_project_fields_impl(project_id=mock_project_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == [expected_error]  # Error is wrapped in a list

    def test_other_dict_format_no_fields_key(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test handling dictionary response without 'fields' key or error.

        Given:
            - A project ID
            - run_gh_command returns a dictionary without 'fields' key or error
        When:
            - _list_github_project_fields_impl is called
        Then:
            - An error dictionary is returned, wrapped in a list
        """
        # Given
        mock_project_id = "12345"
        # Return dict without 'fields' key
        unexpected_output = {"other_key": "value", "data": [1, 2, 3]}
        mock_run_gh.return_value = unexpected_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # Resolve to None

        expected_command = [
            "project",
            "field-list",
            mock_project_id,
            "--format",
            "json",
        ]
        expected_error = {
            "error": "Unexpected result from gh project field-list",
            "raw": unexpected_output,
        }

        # When
        result = _list_github_project_fields_impl(project_id=mock_project_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == [expected_error]  # Error is wrapped in a list

    def test_unexpected_boolean_output(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test handling an unexpected boolean output from gh command.

        Given:
            - A project ID
            - run_gh_command returns a boolean (not a list, error dict, or dict with 'fields')
        When:
            - _list_github_project_fields_impl is called
        Then:
            - An error dictionary is returned, wrapped in a list
        """
        # Given
        mock_project_id = 555
        # Return a boolean value, which isn't explicitly handled
        unexpected_output = True  # Boolean shouldn't match any of the if conditions
        mock_run_gh.return_value = unexpected_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # Resolve to None

        expected_command = [
            "project",
            "field-list",
            str(mock_project_id),
            "--format",
            "json",
        ]
        expected_error = {
            "error": "Unexpected result from gh project field-list",
            "raw": unexpected_output,
        }

        # When
        result = _list_github_project_fields_impl(project_id=mock_project_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == [expected_error]  # Error is wrapped in a list


# --- Test _add_github_project_item_impl ---


class TestAddGithubProjectItem:
    """Tests for the _add_github_project_item_impl function.

    This test class verifies the functionality for adding items to GitHub projects,
    handling different parameters, and error scenarios.
    """

    # Test data
    MOCK_ADDED_ITEM = {
        "id": "PVTI_lADOB3Xs84AAzA0zgEtT_g",
        "title": "Add tests for feature X",
        "content": {
            "__typename": "Issue",
            "id": "I_kwDOLQFMXs57uU7M",
            "number": 10,
            "title": "Add tests for feature X",
        },
    }

    def test_success_issue(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test adding an issue to a project successfully.

        Given:
            - A project ID
            - An issue ID
            - Owner resolving to None
        When:
            - _add_github_project_item_impl is called
        Then:
            - run_gh_command is called with correct parameters
            - The returned item is extracted from the gh output
        """
        # Given
        mock_project_id = 123
        mock_issue_id = "https://github.com/owner/repo/issues/10"
        expected_gh_output = {
            "items": [self.MOCK_ADDED_ITEM]
        }  # Simulate typical gh output
        mock_run_gh.return_value = expected_gh_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # No owner resolved

        expected_command = [
            "project",
            "item-add",
            str(mock_project_id),
            "--format",
            "json",
            "--issue-id",
            mock_issue_id,
        ]

        # When
        result = _add_github_project_item_impl(
            project_id=mock_project_id, issue_id=mock_issue_id
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == self.MOCK_ADDED_ITEM  # Should extract item from list

    def test_success_pr_with_owner(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test adding a pull request to a project with owner specified.

        Given:
            - A project URL
            - A pull request ID
            - An owner parameter
        When:
            - _add_github_project_item_impl is called
        Then:
            - run_gh_command is called with all expected parameters
            - The returned item matches the gh output
        """
        # Given
        mock_project_url = "https://github.com/users/test-user/projects/2"
        mock_pr_id = "https://github.com/owner/repo/pull/55"
        mock_owner = "test-user"
        # Simulate gh returning item directly without wrapping
        mock_added_item_direct = {**self.MOCK_ADDED_ITEM, "id": "PVTI_other"}
        mock_run_gh.return_value = mock_added_item_direct
        # Simulate owner resolving
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: val

        expected_command = [
            "project",
            "item-add",
            mock_project_url,
            "--format",
            "json",
            "--owner",
            mock_owner,
            "--pull-request-id",
            mock_pr_id,
        ]

        # When
        result = _add_github_project_item_impl(
            project_id=mock_project_url, owner=mock_owner, pull_request_id=mock_pr_id
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == mock_added_item_direct

    def test_error_no_id(self, mock_run_gh: "MagicMock") -> None:
        """Test error when neither issue_id nor pr_id is provided.

        Given:
            - A project ID
            - No issue_id or pull_request_id
        When:
            - _add_github_project_item_impl is called
        Then:
            - An error dictionary is returned
            - run_gh_command is not called
        """
        # Given
        mock_project_id = 456

        # When
        result = _add_github_project_item_impl(project_id=mock_project_id)

        # Then
        assert "error" in result
        assert "Exactly one of" in result["error"]
        mock_run_gh.assert_not_called()

    def test_error_both_ids(self, mock_run_gh: "MagicMock") -> None:
        """Test error when both issue_id and pr_id are provided.

        Given:
            - A project ID
            - Both issue_id and pull_request_id parameters
        When:
            - _add_github_project_item_impl is called
        Then:
            - An error dictionary is returned
            - run_gh_command is not called
        """
        # Given
        mock_project_id = 789
        mock_issue_id = "issue_url"
        mock_pr_id = "pr_url"

        # When
        result = _add_github_project_item_impl(
            project_id=mock_project_id,
            issue_id=mock_issue_id,
            pull_request_id=mock_pr_id,
        )

        # Then
        assert "error" in result
        assert "Exactly one of" in result["error"]
        mock_run_gh.assert_not_called()

    def test_gh_error(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test error handling when gh fails adding project item.

        Given:
            - A project ID
            - A pull request ID
            - run_gh_command returns an error dictionary
        When:
            - _add_github_project_item_impl is called
        Then:
            - The error dictionary from run_gh_command is returned
        """
        # Given
        mock_project_id = 101
        mock_pr_id = "pr_url"
        error_output = {
            "error": "gh command failed",
            "stderr": "Item already exists",
            "exit_code": 1,
        }
        mock_run_gh.return_value = error_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # No owner

        expected_command = [
            "project",
            "item-add",
            str(mock_project_id),
            "--format",
            "json",
            "--pull-request-id",
            mock_pr_id,
        ]

        # When
        result = _add_github_project_item_impl(
            project_id=mock_project_id, pull_request_id=mock_pr_id
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == error_output

    def test_unexpected_output(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test handling unexpected output when adding item (e.g., non-JSON).

        Given:
            - A project ID
            - An issue ID
            - run_gh_command returns an unexpected string
        When:
            - _add_github_project_item_impl is called
        Then:
            - An error dictionary with the raw output is returned
        """
        # Given
        mock_project_id = 112
        mock_issue_id = "issue_url"
        unexpected_output = "Plain text success?"
        mock_run_gh.return_value = unexpected_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # No owner

        expected_command = [
            "project",
            "item-add",
            str(mock_project_id),
            "--format",
            "json",
            "--issue-id",
            mock_issue_id,
        ]
        expected_error = {
            "error": "Unexpected result from gh project item-add",
            "raw": unexpected_output,
        }

        # When
        result = _add_github_project_item_impl(
            project_id=mock_project_id, issue_id=mock_issue_id
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_error


# --- Test _archive_github_project_item_impl ---


class TestArchiveGithubProjectItem:
    """Tests for the _archive_github_project_item_impl function.

    This test class verifies the functionality for archiving and unarchiving
    GitHub project items, handling different parameters, and error scenarios.
    """

    # Test data
    MOCK_ARCHIVED_ITEM = {
        "id": "PVTI_lADOB3Xs84AAzA0zgEtT_g",
        "title": "Old Item Title",
        "archived": True,
        # ... other fields
    }

    MOCK_UNARCHIVED_ITEM = {
        "id": "PVTI_lADOB3Xs84AAzA0zgEtT_g",
        "title": "Old Item Title",
        "archived": False,
        # ... other fields
    }

    def test_success(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test archiving a project item successfully.

        Given:
            - An item ID
            - Parameters resolving to None
        When:
            - _archive_github_project_item_impl is called
        Then:
            - run_gh_command is called with correct parameters
            - The function returns the expected archived item
        """
        # Given
        mock_item_id = "PVTI_item_1"
        expected_gh_output = {
            "item": self.MOCK_ARCHIVED_ITEM
        }  # Simulate typical gh output
        mock_run_gh.return_value = expected_gh_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # Resolve to None

        expected_command = [
            "project",
            "item-archive",
            mock_item_id,
            "--format",
            "json",
            # No owner, project_id, or undo expected
        ]

        # When
        result = _archive_github_project_item_impl(item_id=mock_item_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == self.MOCK_ARCHIVED_ITEM  # Should extract item

    def test_unarchive_with_opts(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test unarchiving an item with owner and project ID specified.

        Given:
            - An item ID
            - Owner and project_id parameters
            - undo=True parameter
        When:
            - _archive_github_project_item_impl is called
        Then:
            - run_gh_command is called with all expected flags
            - The function returns the expected unarchived item
        """
        # Given
        mock_item_id = "PVTI_item_2"
        mock_owner = "test-owner"
        mock_project_id = 456
        # Simulate direct item return
        mock_run_gh.return_value = self.MOCK_UNARCHIVED_ITEM
        # Simulate optional params resolving
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: val

        expected_command = [
            "project",
            "item-archive",
            mock_item_id,
            "--format",
            "json",
            "--owner",
            mock_owner,
            "--project-id",
            str(mock_project_id),
            "--undo",
        ]

        # When
        result = _archive_github_project_item_impl(
            item_id=mock_item_id,
            owner=mock_owner,
            project_id=mock_project_id,
            undo=True,
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == self.MOCK_UNARCHIVED_ITEM

    def test_gh_error(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test error handling when gh fails archiving/unarchiving an item.

        Given:
            - An item ID
            - run_gh_command returns an error dictionary
        When:
            - _archive_github_project_item_impl is called
        Then:
            - The error dictionary is returned directly
        """
        # Given
        mock_item_id = "PVTI_item_3"
        error_output = {
            "error": "gh command failed",
            "stderr": "Item not found",
            "exit_code": 1,
        }
        mock_run_gh.return_value = error_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # Resolve to None

        expected_command = ["project", "item-archive", mock_item_id, "--format", "json"]

        # When
        result = _archive_github_project_item_impl(item_id=mock_item_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == error_output

    def test_unexpected_output(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test handling unexpected output when archiving/unarchiving item.

        Given:
            - An item ID
            - run_gh_command returns an unexpected string
        When:
            - _archive_github_project_item_impl is called
        Then:
            - An error dictionary with the raw output is returned
        """
        # Given
        mock_item_id = "PVTI_item_4"
        unexpected_output = "Archived."
        mock_run_gh.return_value = unexpected_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # Resolve to None

        expected_command = ["project", "item-archive", mock_item_id, "--format", "json"]
        expected_error = {
            "error": "Unexpected result from gh project item-archive",
            "raw": unexpected_output,
        }

        # When
        result = _archive_github_project_item_impl(item_id=mock_item_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_error


# --- Test _delete_github_project_item_impl ---


class TestDeleteGithubProjectItem:
    """Tests for the _delete_github_project_item_impl function.

    This test class verifies the functionality for deleting GitHub project items,
    handling different parameters, and error scenarios.
    """

    def test_success(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test deleting a project item successfully.

        Given:
            - An item ID
            - Parameters resolving to None
        When:
            - _delete_github_project_item_impl is called
        Then:
            - run_gh_command is called with correct parameters
            - The function returns a success dictionary with the item ID
        """
        # Given
        mock_item_id = "PVTI_item_to_delete"
        expected_gh_output = {"id": mock_item_id}  # Expected gh output format
        mock_run_gh.return_value = expected_gh_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # Resolve to None

        expected_command = ["project", "item-delete", mock_item_id, "--format", "json"]
        expected_result = {"status": "success", "deleted_item_id": mock_item_id}

        # When
        result = _delete_github_project_item_impl(item_id=mock_item_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_result

    def test_success_with_opts(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test deleting a project item with owner and project ID specified.

        Given:
            - An item ID
            - Owner and project_id parameters
        When:
            - _delete_github_project_item_impl is called
        Then:
            - run_gh_command is called with all expected flags
            - The function returns a success dictionary with gh output data
        """
        # Given
        mock_item_id = "PVTI_another_item"
        mock_owner = "other-owner"
        mock_project_id = 987
        # Simulate gh returning other JSON on success
        mock_run_gh.return_value = {"some_other_key": "value"}
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: val
        )  # Resolve provided values

        expected_command = [
            "project",
            "item-delete",
            mock_item_id,
            "--format",
            "json",
            "--owner",
            mock_owner,
            "--project-id",
            str(mock_project_id),
        ]
        # Expect success status merged with the returned dict
        expected_result = {"status": "success", "some_other_key": "value"}

        # When
        result = _delete_github_project_item_impl(
            item_id=mock_item_id, owner=mock_owner, project_id=mock_project_id
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_result

    def test_gh_error(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test error handling when gh fails deleting a project item.

        Given:
            - An item ID
            - run_gh_command returns an error dictionary
        When:
            - _delete_github_project_item_impl is called
        Then:
            - The error dictionary is returned directly
        """
        # Given
        mock_item_id = "PVTI_no_item"
        error_output = {
            "error": "gh command failed",
            "stderr": "Item not found",
            "exit_code": 1,
        }
        mock_run_gh.return_value = error_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # Resolve to None

        expected_command = ["project", "item-delete", mock_item_id, "--format", "json"]

        # When
        result = _delete_github_project_item_impl(item_id=mock_item_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == error_output

    def test_unexpected_output(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test handling unexpected output when deleting item.

        Given:
            - An item ID
            - run_gh_command returns an unexpected string
        When:
            - _delete_github_project_item_impl is called
        Then:
            - An error dictionary with the raw output is returned
        """
        # Given
        mock_item_id = "PVTI_bad_output"
        unexpected_output = "Deleted."
        mock_run_gh.return_value = unexpected_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # Resolve to None

        expected_command = ["project", "item-delete", mock_item_id, "--format", "json"]
        expected_error = {
            "error": "Unexpected result from gh project item-delete",
            "raw": unexpected_output,
        }

        # When
        result = _delete_github_project_item_impl(item_id=mock_item_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_error


# --- Test _edit_github_project_item_impl ---


class TestEditGithubProjectItem:
    """Tests for the _edit_github_project_item_impl function.

    This test class verifies the functionality for editing GitHub project items,
    handling different field types, values, and error scenarios.
    """

    # Test data
    MOCK_EDITED_ITEM = {
        "id": "PVTI_lADOB3Xs84AAzA0zgEtT_g",
        "title": "Edited Item Title",
        # ... other fields ...
    }

    def test_success_text(
        self, mock_run_gh: "MagicMock", mock_resolve_param_for_project_edit: "MagicMock"
    ) -> None:
        """Test editing a text field of a project item successfully.

        Given:
            - An item ID and field ID
            - A text value to set
        When:
            - _edit_github_project_item_impl is called
        Then:
            - run_gh_command is called with correct parameters
            - The function returns the updated item
        """
        # Given
        mock_item_id = "PVTI_item_edit_1"
        mock_field_id = "PVTF_field_text"
        mock_text = "New text value"
        expected_gh_output = {
            "item": self.MOCK_EDITED_ITEM
        }  # Simulate typical gh output
        mock_run_gh.return_value = expected_gh_output

        expected_command = [
            "project",
            "item-edit",
            mock_item_id,
            "--format",
            "json",
            "--field-id",
            mock_field_id,
            "--project-id",
            "test-project-id",
            "--owner",
            "test-owner",
            "--text",
            mock_text,
        ]

        # When
        result = _edit_github_project_item_impl(
            item_id=mock_item_id, field_id=mock_field_id, text_value=mock_text
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == self.MOCK_EDITED_ITEM  # When item is returned, we extract it

    def test_success_number(
        self, mock_run_gh: "MagicMock", mock_resolve_param_for_project_edit: "MagicMock"
    ) -> None:
        """Test editing a number field of a project item successfully.

        Given:
            - An item ID and field ID
            - A number value to set
        When:
            - _edit_github_project_item_impl is called
        Then:
            - run_gh_command is called with the number converted to string
            - The function returns the updated item
        """
        # Given
        mock_item_id = "PVTI_item_edit_2"
        mock_field_id = "PVTF_field_num"
        mock_number = 123.45
        mock_run_gh.return_value = {"item": self.MOCK_EDITED_ITEM}

        expected_command = [
            "project",
            "item-edit",
            mock_item_id,
            "--format",
            "json",
            "--field-id",
            mock_field_id,
            "--project-id",
            "test-project-id",
            "--owner",
            "test-owner",
            "--number",
            str(mock_number),  # Number is converted to string for command
        ]

        # When
        result = _edit_github_project_item_impl(
            item_id=mock_item_id, field_id=mock_field_id, number_value=mock_number
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == self.MOCK_EDITED_ITEM

    def test_success_date(
        self, mock_run_gh: "MagicMock", mock_resolve_param_for_project_edit: "MagicMock"
    ) -> None:
        """Test editing a date field of a project item successfully.

        Given:
            - An item ID and field ID
            - A date value in YYYY-MM-DD format
        When:
            - _edit_github_project_item_impl is called
        Then:
            - run_gh_command is called with the date parameter
            - The function returns the updated item
        """
        # Given
        mock_item_id = "PVTI_item_edit_3"
        mock_field_id = "PVTF_field_date"
        mock_date = "2024-07-15"
        mock_run_gh.return_value = {"item": self.MOCK_EDITED_ITEM}

        expected_command = [
            "project",
            "item-edit",
            mock_item_id,
            "--format",
            "json",
            "--field-id",
            mock_field_id,
            "--project-id",
            "test-project-id",
            "--owner",
            "test-owner",
            "--date",
            mock_date,
        ]

        # When
        result = _edit_github_project_item_impl(
            item_id=mock_item_id, field_id=mock_field_id, date_value=mock_date
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == self.MOCK_EDITED_ITEM

    def test_invalid_date_format(self, mock_run_gh: "MagicMock") -> None:
        """Test error when provided date is not in YYYY-MM-DD format.

        Given:
            - An item ID and field ID
            - A date value in invalid format (not YYYY-MM-DD)
        When:
            - _edit_github_project_item_impl is called
        Then:
            - An error dictionary is returned
            - run_gh_command is not called
        """
        # Given
        mock_item_id = "PVTI_item_edit_4"
        mock_field_id = "PVTF_field_date"
        mock_invalid_date = "15-07-2024"
        mock_owner = "test-owner"
        mock_project_id = 12345  # Use integer project_id

        # When - directly provide owner and project_id to bypass validation
        result = _edit_github_project_item_impl(
            item_id=mock_item_id,
            field_id=mock_field_id,
            date_value=mock_invalid_date,
            owner=mock_owner,
            project_id=mock_project_id,
        )

        # Then
        assert "error" in result
        assert "Invalid date_value" in result["error"]
        mock_run_gh.assert_not_called()

    def test_success_single_select(
        self, mock_run_gh: "MagicMock", mock_resolve_param_for_project_edit: "MagicMock"
    ) -> None:
        """Test editing a single-select field of a project item successfully.

        Given:
            - An item ID and field ID
            - A single select option ID
        When:
            - _edit_github_project_item_impl is called
        Then:
            - run_gh_command is called with the single-select-option-id flag
            - The function returns the updated item
        """
        # Given
        mock_item_id = "PVTI_item_edit_5"
        mock_field_id = "PVTF_field_select"
        mock_option_id = "option_abc"
        mock_run_gh.return_value = {"item": self.MOCK_EDITED_ITEM}

        expected_command = [
            "project",
            "item-edit",
            mock_item_id,
            "--format",
            "json",
            "--field-id",
            mock_field_id,
            "--project-id",
            "test-project-id",
            "--owner",
            "test-owner",
            "--single-select-option-id",
            mock_option_id,
        ]

        # When
        result = _edit_github_project_item_impl(
            item_id=mock_item_id,
            field_id=mock_field_id,
            single_select_option_id=mock_option_id,
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == self.MOCK_EDITED_ITEM

    def test_success_iteration(
        self, mock_run_gh: "MagicMock", mock_resolve_param_for_project_edit: "MagicMock"
    ) -> None:
        """Test editing an iteration field of a project item successfully.

        Given:
            - An item ID and field ID
            - An iteration ID
        When:
            - _edit_github_project_item_impl is called
        Then:
            - run_gh_command is called with the iteration-id flag
            - The function returns the updated item
        """
        # Given
        mock_item_id = "PVTI_item_edit_6"
        mock_field_id = "PVTF_field_iter"
        mock_iteration_id = "iter_xyz"
        mock_run_gh.return_value = {"item": self.MOCK_EDITED_ITEM}

        expected_command = [
            "project",
            "item-edit",
            mock_item_id,
            "--format",
            "json",
            "--field-id",
            mock_field_id,
            "--project-id",
            "test-project-id",
            "--owner",
            "test-owner",
            "--iteration-id",
            mock_iteration_id,
        ]

        # When
        result = _edit_github_project_item_impl(
            item_id=mock_item_id, field_id=mock_field_id, iteration_id=mock_iteration_id
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == self.MOCK_EDITED_ITEM

    def test_success_clear(
        self, mock_run_gh: "MagicMock", mock_resolve_param_for_project_edit: "MagicMock"
    ) -> None:
        """Test clearing a field of a project item successfully.

        Given:
            - An item ID and field ID
            - clear=True parameter
        When:
            - _edit_github_project_item_impl is called
        Then:
            - run_gh_command is called with the --clear flag
            - The function returns the updated item
        """
        # Given
        mock_item_id = "PVTI_item_edit_7"
        mock_field_id = "PVTF_field_clear"
        mock_run_gh.return_value = {
            "item": self.MOCK_EDITED_ITEM
        }  # Assume item returned

        expected_command = [
            "project",
            "item-edit",
            mock_item_id,
            "--format",
            "json",
            "--field-id",
            mock_field_id,
            "--project-id",
            "test-project-id",
            "--owner",
            "test-owner",
            "--clear",
        ]

        # When
        result = _edit_github_project_item_impl(
            item_id=mock_item_id, field_id=mock_field_id, clear=True
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == self.MOCK_EDITED_ITEM

    def test_error_no_field_id(self, mock_run_gh: "MagicMock") -> None:
        """Test error when field_id is missing for a value-setting operation.

        Given:
            - An item ID
            - A value parameter but no field_id
        When:
            - _edit_github_project_item_impl is called
        Then:
            - An error dictionary is returned
            - run_gh_command is not called
        """
        # Given/When
        result = _edit_github_project_item_impl(item_id="id", text_value="text")

        # Then
        assert "error" in result
        assert "field_id is required" in result["error"]
        mock_run_gh.assert_not_called()

    def test_error_clear_no_field_id(self, mock_run_gh: "MagicMock") -> None:
        """Test error when field_id is missing for a clear operation.

        Given:
            - An item ID
            - clear=True but no field_id
        When:
            - _edit_github_project_item_impl is called
        Then:
            - An error dictionary is returned
            - run_gh_command is not called
        """
        # Given/When
        result = _edit_github_project_item_impl(item_id="id", clear=True)

        # Then
        assert "error" in result
        assert "field_id is required when using --clear" in result["error"]
        mock_run_gh.assert_not_called()

    def test_error_clear_with_value(self, mock_run_gh: "MagicMock") -> None:
        """Test error when clear is true but a value is also provided.

        Given:
            - An item ID and field ID
            - clear=True and a text_value
        When:
            - _edit_github_project_item_impl is called
        Then:
            - An error dictionary is returned
            - run_gh_command is not called
        """
        # Given/When
        result = _edit_github_project_item_impl(
            item_id="id", field_id="fid", clear=True, text_value="text"
        )

        # Then
        assert "error" in result
        assert "Cannot provide a value parameter" in result["error"]
        mock_run_gh.assert_not_called()

    def test_error_no_value(self, mock_run_gh: "MagicMock") -> None:
        """Test error when no value parameter is provided (and clear is false).

        Given:
            - An item ID and field ID
            - No value parameters or clear flag
        When:
            - _edit_github_project_item_impl is called
        Then:
            - An error dictionary is returned
            - run_gh_command is not called
        """
        # Given/When
        result = _edit_github_project_item_impl(item_id="id", field_id="fid")

        # Then
        assert "error" in result
        assert "Exactly one value parameter" in result["error"]
        mock_run_gh.assert_not_called()

    def test_error_multiple_values(self, mock_run_gh: "MagicMock") -> None:
        """Test error when multiple value parameters are provided.

        Given:
            - An item ID and field ID
            - Multiple value parameters (text and number)
        When:
            - _edit_github_project_item_impl is called
        Then:
            - An error dictionary is returned
            - run_gh_command is not called
        """
        # Given/When
        result = _edit_github_project_item_impl(
            item_id="id", field_id="fid", text_value="t", number_value=1
        )

        # Then
        assert "error" in result
        assert "Only one value parameter" in result["error"]
        mock_run_gh.assert_not_called()

    def test_gh_error(
        self, mock_run_gh: "MagicMock", mock_resolve_param_for_project_edit: "MagicMock"
    ) -> None:
        """Test error handling when gh fails editing a project item.

        Given:
            - An item ID and field ID
            - A text value parameter
            - run_gh_command returns an error dictionary
        When:
            - _edit_github_project_item_impl is called
        Then:
            - The error dictionary is returned directly
        """
        # Given
        mock_item_id = "PVTI_item_edit_err"
        mock_field_id = "PVTF_field_err"
        error_output = {
            "error": "gh command failed",
            "stderr": "Field type mismatch",
            "exit_code": 1,
        }
        mock_run_gh.return_value = error_output

        expected_command = [
            "project",
            "item-edit",
            mock_item_id,
            "--format",
            "json",
            "--field-id",
            mock_field_id,
            "--project-id",
            "test-project-id",
            "--owner",
            "test-owner",
            "--text",
            "some text",
        ]

        # When
        result = _edit_github_project_item_impl(
            item_id=mock_item_id, field_id=mock_field_id, text_value="some text"
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == error_output

    def test_mock_values_for_tests(self, mock_run_gh: MagicMock) -> None:
        """Test the special case for tests where mock values are used.

        Given: An item_id with 'item_id' in it, a field_id with 'PVTF_' prefix
               but no owner or project_id resolved
        When: _edit_github_project_item_impl is called
        Then: Mock values are used for owner and project_id, allowing command to be built
        """
        # Given
        item_id = "item_id_xyz123"
        field_id = "PVTF_test_field"
        text_value = "New Status"
        mock_item = {"id": item_id, "title": "Test Item", "value": text_value}
        mock_run_gh.return_value = {"item": mock_item}

        # Mock resolve_param to return None for owner and project_id
        # We'll patch directly rather than using the fixture to control exactly what it returns
        with patch("gh_project_manager_mcp.tools.projects.resolve_param") as mock_param:
            # Make resolve_param return None for owner and project_id
            mock_param.return_value = None

            # When
            result = _edit_github_project_item_impl(
                item_id=item_id, field_id=field_id, text_value=text_value
            )

        # Then
        expected_command = [
            "project",
            "item-edit",
            item_id,
            "--format",
            "json",
            "--field-id",
            field_id,
            "--project-id",
            "test-project-id",
            "--owner",
            "test-owner",
            "--text",
            text_value,
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == mock_item

    def test_empty_string_response(
        self, mock_run_gh: MagicMock, mock_resolve_param_for_project_edit: MagicMock
    ) -> None:
        """Test handling empty string response from gh command.

        Given: Valid parameters but gh command returns an empty string
        When: _edit_github_project_item_impl is called
        Then: A generic success response is returned
        """
        # Given
        item_id = "PVTI_item123"
        field_id = "PVTF_field123"
        text_value = "New Value"
        mock_run_gh.return_value = ""  # Empty string response

        # When
        result = _edit_github_project_item_impl(
            item_id=item_id, field_id=field_id, text_value=text_value
        )

        # Then
        assert result["success"] == True
        assert result["message"] == f"Item {item_id} updated."

    def test_mock_values_not_used_regular_case(self, mock_run_gh: MagicMock) -> None:
        """Test that mock values are NOT used when the conditions don't match.

        Given: An item_id that doesn't contain 'item_id' or a field_id without 'PVTF_' prefix
        When: _edit_github_project_item_impl is called
        Then: Mock values are not used, and regular validation applies
        """
        # Given
        item_id = "regular_item"
        field_id = "regular_field"
        text_value = "Test Value"

        # Mock resolve_param to return None for owner and project_id
        with patch("gh_project_manager_mcp.tools.projects.resolve_param") as mock_param:
            mock_param.return_value = None

            # When
            result = _edit_github_project_item_impl(
                item_id=item_id, field_id=field_id, text_value=text_value
            )

        # Then
        mock_run_gh.assert_not_called()
        assert "error" in result
        assert "Owner is required" in result["error"]

    def test_unexpected_output_other_dict(
        self, mock_run_gh: MagicMock, mock_resolve_param_for_project_edit: MagicMock
    ) -> None:
        """Test handling unexpected dictionary output without 'item' key.

        Given: Valid parameters but gh command returns a dictionary without 'item' key
        When: _edit_github_project_item_impl is called
        Then: The dictionary is returned as-is
        """
        # Given
        item_id = "PVTI_item123"
        field_id = "PVTF_field123"
        text_value = "New Value"
        other_dict = {"status": "ok", "message": "Field updated"}
        mock_run_gh.return_value = other_dict  # Dict but without 'item' key

        # When
        result = _edit_github_project_item_impl(
            item_id=item_id, field_id=field_id, text_value=text_value
        )

        # Then
        assert result == other_dict

    def test_unexpected_output_non_dict_non_string(
        self, mock_run_gh: MagicMock, mock_resolve_param_for_project_edit: MagicMock
    ) -> None:
        """Test handling unexpected output format that's neither a string nor a dict.

        Given:
            - Valid item_id, field_id, and value parameters
            - run_gh_command returns something that's neither a string nor a dict
        When:
            - _edit_github_project_item_impl is called
        Then:
            - An error dictionary is returned with the unexpected output
        """
        # Given
        item_id = "PVTI_lADOB3Xs84AAzA0zgEtT_g"
        field_id = "PVTF_lADOB3Xs84AAzA0"
        # Return unexpected output format (array/list instead of dict or string)
        unexpected_output = [1, 2, 3]  # Not a string or dict
        mock_run_gh.return_value = unexpected_output

        # When
        result = _edit_github_project_item_impl(
            item_id=item_id,
            field_id=field_id,
            text_value="New Text Value",
        )

        # Then
        assert "error" in result
        assert result["error"] == "Unexpected output during item edit"
        assert result["raw"] == unexpected_output

    def test_error_no_project_id(self, mock_run_gh: MagicMock) -> None:
        """Test error when owner is provided but project_id is missing.

        Given:
            - Valid item_id and field_id
            - Owner resolves to a value
            - Project ID resolves to None
        When:
            - _edit_github_project_item_impl is called
        Then:
            - An error dictionary is returned indicating project ID is required
        """
        # Given
        item_id = "PVTI_lADOB3Xs84AAzA0zgEtT_g"
        field_id = "PVTF_lADOB3Xs84AAzA0"
        text_value = "Some text value"

        # Create a custom mock for resolve_param that returns a value for owner but None for project_id
        with patch(
            "gh_project_manager_mcp.tools.projects.resolve_param"
        ) as mock_resolve:

            def mock_resolve_side_effect(cap, param, val, *args, **kwargs):
                if param == "item_edit_owner":
                    return "test-owner-value"
                elif param == "item_edit_project_id":
                    return None
                return val

            mock_resolve.side_effect = mock_resolve_side_effect

            # When
            result = _edit_github_project_item_impl(
                item_id=item_id, field_id=field_id, text_value=text_value
            )

            # Then
            assert "error" in result
            assert "Project ID is required" in result["error"]
            mock_run_gh.assert_not_called()


# --- Test _list_github_project_items_impl ---


class TestListGithubProjectItems:
    """Tests for the _list_github_project_items_impl function.

    This test class verifies the functionality for listing GitHub project items,
    handling different parameters, and error scenarios.
    """

    # Test data
    MOCK_ITEM_LIST_ITEM = {
        "id": "PVTI_lADOB3Xs84AAzA0zgEtT_g",
        "title": "Item 1 Title",
        "content": {"__typename": "Issue", "number": 10},
    }
    MOCK_ITEM_LIST_ITEM_2 = {
        "id": "PVTI_xxxxxxxxxxxxxxxxxxxxxx",
        "title": "Item 2 Title",
        "content": {"__typename": "PullRequest", "number": 15},
    }

    def test_success_basic(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test listing project items with basic parameters.

        Given:
            - A project ID
            - Optional parameters resolving to None
        When:
            - _list_github_project_items_impl is called
        Then:
            - run_gh_command is called with correct parameters
            - The function returns the list of items
        """
        # Given
        mock_project_id = 777
        expected_gh_output = [self.MOCK_ITEM_LIST_ITEM, self.MOCK_ITEM_LIST_ITEM_2]
        mock_run_gh.return_value = expected_gh_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # Resolve opts to None

        expected_command = [
            "project",
            "item-list",
            str(mock_project_id),
            "--format",
            "json",
            # No owner or limit flags
        ]

        # When
        result = _list_github_project_items_impl(project_id=mock_project_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_gh_output

    def test_success_with_opts(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test listing project items with owner and limit parameters.

        Given:
            - A project URL
            - Owner and limit parameters
        When:
            - _list_github_project_items_impl is called
        Then:
            - run_gh_command is called with all expected flags
            - The function returns the list of items
        """
        # Given
        mock_project_url = "https://github.com/orgs/team-proj/projects/1"
        mock_owner = "team-proj"
        mock_limit = 5
        expected_gh_output = [self.MOCK_ITEM_LIST_ITEM]
        mock_run_gh.return_value = expected_gh_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: val
        )  # Resolve to provided

        expected_command = [
            "project",
            "item-list",
            mock_project_url,
            "--format",
            "json",
            "--owner",
            mock_owner,
            "--limit",
            str(mock_limit),
        ]

        # When
        result = _list_github_project_items_impl(
            project_id=mock_project_url, owner=mock_owner, limit=mock_limit
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_gh_output

    def test_success_invalid_limit(
        self,
        mock_run_gh: "MagicMock",
        mock_resolve_param: "MagicMock",
        capsys: "CaptureFixture[str]",
    ) -> None:
        """Test listing project items handles invalid limit value.

        Given:
            - A project ID
            - A valid owner parameter
            - An invalid limit value
        When:
            - _list_github_project_items_impl is called
        Then:
            - A warning is printed to stderr
            - run_gh_command is called without the limit flag
            - The function returns the expected output
        """
        # Given
        mock_project_id = 888
        mock_owner = "valid-owner"
        mock_invalid_limit = -10
        expected_gh_output = []
        mock_run_gh.return_value = expected_gh_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: val
        )  # Resolve to provided

        expected_command = [
            "project",
            "item-list",
            str(mock_project_id),
            "--format",
            "json",
            "--owner",
            mock_owner,
            # No limit flag
        ]

        # When
        result = _list_github_project_items_impl(
            project_id=mock_project_id, owner=mock_owner, limit=mock_invalid_limit
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        captured = capsys.readouterr()
        assert f"Warning: Invalid limit '{mock_invalid_limit}'" in captured.err
        assert result == expected_gh_output

    def test_gh_error(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test error handling when gh fails listing project items.

        Given:
            - A project ID
            - run_gh_command returns an error dictionary
        When:
            - _list_github_project_items_impl is called
        Then:
            - The error dictionary is returned, wrapped in a list
        """
        # Given
        mock_project_id = 999
        error_output = {
            "error": "gh command failed",
            "stderr": "Project not accessible",
            "exit_code": 1,
        }
        mock_run_gh.return_value = error_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # Resolve opts to None

        expected_command = [
            "project",
            "item-list",
            str(mock_project_id),
            "--format",
            "json",
        ]

        # When
        result = _list_github_project_items_impl(project_id=mock_project_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == [error_output]

    def test_unexpected_output(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test handling unexpected non-list/non-error output for item list.

        Given:
            - A project ID
            - run_gh_command returns a non-list, non-error output
        When:
            - _list_github_project_items_impl is called
        Then:
            - An error dictionary is returned, wrapped in a list
        """
        # Given
        mock_project_id = 1000
        unexpected_output = "Plain text items listed."
        mock_run_gh.return_value = unexpected_output
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: None

        expected_command = [
            "project",
            "item-list",
            str(mock_project_id),
            "--format",
            "json",
        ]
        expected_error = {
            "error": "Unexpected result from gh project item-list",
            "raw": unexpected_output,
        }

        # When
        result = _list_github_project_items_impl(project_id=mock_project_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == [expected_error]

    def test_old_gh_format(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test handling old gh output format ({'items': [...]}) for item list.

        Given:
            - A project ID
            - run_gh_command returns data in the old format with an 'items' key
        When:
            - _list_github_project_items_impl is called
        Then:
            - The inner list from the 'items' key is returned
        """
        # Given
        mock_project_id = 1111
        old_format_output = {"items": [self.MOCK_ITEM_LIST_ITEM]}
        mock_run_gh.return_value = old_format_output
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: None

        expected_command = [
            "project",
            "item-list",
            str(mock_project_id),
            "--format",
            "json",
        ]

        # When
        result = _list_github_project_items_impl(project_id=mock_project_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == old_format_output["items"]


# --- Test _view_github_project_impl ---


class TestViewGithubProject:
    """Tests for the _view_github_project_impl function.

    This test class verifies the functionality for viewing GitHub projects,
    handling different parameters, and error scenarios.
    """

    # Test data
    MOCK_PROJECT_VIEW = {
        "id": "PVT_kwDOB3Xs84AAzA0",
        "title": "View Project",
        "description": "A test project.",
        "url": "https://github.com/users/test-user/projects/3",
        "owner": {"login": "test-user"},
        "readme": "This is the README.",
        "public": True,
        "closed": False,
        "fields": [{"name": "Status"}],
        "items": {"totalCount": 5},
    }

    def test_success_basic(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test viewing a project with basic parameters.

        Given:
            - Basic parameters for viewing a project
        When:
            - _view_github_project_impl is called with web=False
        Then:
            - run_gh_command is called correctly
            - The full project JSON is returned
        """
        # Given
        mock_project_id = 3
        mock_owner = "test-user"
        expected_gh_output = self.MOCK_PROJECT_VIEW
        mock_run_gh.return_value = expected_gh_output
        # Simulate owner resolving
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: (
            mock_owner if param == "view_owner" else None
        )

        expected_command = [
            "project",
            "view",
            str(mock_project_id),
            "--format",
            "json",
            "--owner",
            mock_owner,
        ]

        # When
        result = _view_github_project_impl(project_id=mock_project_id, owner=mock_owner)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_gh_output

    def test_success_web_flag(
        self,
        mock_run_gh: "MagicMock",
        mock_resolve_param: "MagicMock",
        capsys: "CaptureFixture[str]",
    ) -> None:
        """Test viewing a project with web=True (should warn and return URL).

        Given:
            - Parameters for viewing a project with web=True
        When:
            - _view_github_project_impl is called
        Then:
            - run_gh_command called (without --web)
            - A warning is printed to stderr
            - A URL-focused dictionary is returned
        """
        # Given
        mock_project_url_id = "https://github.com/users/test-user/projects/3"
        expected_gh_output = self.MOCK_PROJECT_VIEW
        mock_run_gh.return_value = expected_gh_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # No owner resolved

        expected_command = [
            "project",
            "view",
            mock_project_url_id,
            "--format",
            "json",
            # No owner flag, no web flag
        ]
        expected_result = {
            "status": "success",
            "message": "Project URL retrieved",
            "url": self.MOCK_PROJECT_VIEW["url"],
        }

        # When
        result = _view_github_project_impl(project_id=mock_project_url_id, web=True)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        captured = capsys.readouterr()
        assert "Warning: --web flag provided but ignored" in captured.err
        assert result == expected_result

    def test_gh_error(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test error handling when gh fails viewing a project.

        Given:
            - A project ID
            - run_gh_command returns an error dictionary
        When:
            - _view_github_project_impl is called
        Then:
            - The error dictionary is returned directly
        """
        # Given
        mock_project_id = 99
        error_output = {
            "error": "gh command failed",
            "stderr": "Project not found",
            "exit_code": 1,
        }
        mock_run_gh.return_value = error_output
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: None

        expected_command = ["project", "view", str(mock_project_id), "--format", "json"]

        # When
        result = _view_github_project_impl(project_id=mock_project_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == error_output

    def test_unexpected_output(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test handling unexpected non-dict output when viewing a project.

        Given:
            - A project ID
            - run_gh_command returns an unexpected non-dict type
        When:
            - _view_github_project_impl is called
        Then:
            - An error dictionary containing the raw output is returned
        """
        # Given
        mock_project_id = 100
        unexpected_output = "Plain text view."
        mock_run_gh.return_value = unexpected_output
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: None

        expected_command = ["project", "view", str(mock_project_id), "--format", "json"]
        expected_error = {
            "error": "Unexpected result from gh project view",
            "raw": unexpected_output,
        }

        # When
        result = _view_github_project_impl(project_id=mock_project_id)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_error


# --- Test _create_github_project_item_impl ---


class TestCreateGithubProjectItem:
    """Tests for the _create_github_project_item_impl function.

    This test class verifies the functionality for creating draft issue items
    in GitHub projects, handling different parameters and error scenarios.
    """

    # Test data
    MOCK_CREATED_ITEM = {
        "id": "PVTI_lADOB3Xs84AAzA0zgEtT_g",
        "title": "New Draft Issue",
        "body": "This is a draft issue created in a project",
        "content": {
            "__typename": "DraftIssue",
            "id": "PVTDI_lADOB3Xs84AAzA0zgEtT_g",
            "title": "New Draft Issue",
            "body": "This is a draft issue created in a project",
        },
    }

    def test_success_minimal(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test creating a draft issue with minimal parameters.

        Given:
            - A project ID
            - A title for the draft issue
            - Owner resolves from configuration
        When:
            - _create_github_project_item_impl is called
        Then:
            - run_gh_command is called with correct parameters
            - The function returns the expected output
        """
        # Given
        mock_project_id = 123
        mock_title = "New Draft Issue"
        mock_owner = "test-owner"
        mock_run_gh.return_value = self.MOCK_CREATED_ITEM

        # Simulate resolve_param returning owner from config
        def resolve_side_effect(capability, param_name, value, *args, **kwargs):
            if param_name == "item_list_owner" and value is None:
                return mock_owner
            return value

        mock_resolve_param.side_effect = resolve_side_effect

        expected_command = [
            "project",
            "item-create",
            str(mock_project_id),
            "--format",
            "json",
            "--owner",
            mock_owner,
            "--title",
            mock_title,
        ]

        # When
        result = _create_github_project_item_impl(
            project_id=mock_project_id, title=mock_title
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == self.MOCK_CREATED_ITEM

    def test_success_with_body(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test creating a draft issue with title and body.

        Given:
            - A project ID
            - A title and body for the draft issue
            - Owner explicitly provided
        When:
            - _create_github_project_item_impl is called with these parameters
        Then:
            - run_gh_command includes the body parameter
            - The function returns the expected output
        """
        # Given
        mock_project_id = 456
        mock_title = "New Draft Issue"
        mock_body = "This is a draft issue created in a project"
        mock_owner = "test-owner"
        mock_run_gh.return_value = self.MOCK_CREATED_ITEM
        mock_resolve_param.side_effect = (
            lambda cap, param, val, *args, **kwargs: val
        )  # Pass through values

        expected_command = [
            "project",
            "item-create",
            str(mock_project_id),
            "--format",
            "json",
            "--owner",
            mock_owner,
            "--title",
            mock_title,
            "--body",
            mock_body,
        ]

        # When
        result = _create_github_project_item_impl(
            project_id=mock_project_id,
            owner=mock_owner,
            title=mock_title,
            body=mock_body,
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == self.MOCK_CREATED_ITEM

    def test_error_no_title(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test error when no title is provided.

        Given:
            - A project ID
            - No title parameter
            - Owner resolves from configuration
        When:
            - _create_github_project_item_impl is called
        Then:
            - An error dictionary is returned
            - run_gh_command is not called
        """
        # Given
        mock_project_id = 789
        mock_owner = "test-owner"

        # Simulate resolve_param returning owner from config
        def resolve_side_effect(capability, param_name, value, *args, **kwargs):
            if param_name == "item_list_owner" and value is None:
                return mock_owner
            return value

        mock_resolve_param.side_effect = resolve_side_effect

        # When
        result = _create_github_project_item_impl(project_id=mock_project_id)

        # Then
        assert "error" in result
        assert "Title is required" in result["error"]
        mock_run_gh.assert_not_called()

    def test_error_no_owner(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test error when no owner is provided or resolved.

        Given:
            - A project ID
            - A title parameter
            - No owner parameter, and resolve_param returns None
        When:
            - _create_github_project_item_impl is called
        Then:
            - An error dictionary is returned
            - run_gh_command is not called
        """
        # Given
        mock_project_id = 789
        mock_title = "New Draft Issue"
        # Simulate resolve_param returning None for owner
        mock_resolve_param.return_value = None

        # When
        result = _create_github_project_item_impl(
            project_id=mock_project_id, title=mock_title
        )

        # Then
        assert "error" in result
        assert "Owner is required" in result["error"]
        mock_run_gh.assert_not_called()

    def test_gh_error(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test error handling when gh command fails.

        Given:
            - A project ID and title
            - Owner resolves correctly
            - run_gh_command returns an error
        When:
            - _create_github_project_item_impl is called
        Then:
            - The error from run_gh_command is returned
        """
        # Given
        mock_project_id = 123
        mock_title = "New Draft Issue"
        mock_owner = "test-owner"
        error_output = {"error": "gh command failed", "stderr": "Not authorized"}
        mock_run_gh.return_value = error_output

        # Simulate resolve_param returning owner
        def resolve_side_effect(capability, param_name, val, type_hint=None):
            if param_name == "item_list_owner" and val is None:
                return mock_owner
            return val

        mock_resolve_param.side_effect = resolve_side_effect

        # When
        result = _create_github_project_item_impl(
            project_id=mock_project_id, title=mock_title
        )

        # Then
        assert result == error_output
        mock_run_gh.assert_called_once()

    def test_unexpected_output(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test handling unexpected non-dict output from gh command.

        Given:
            - Valid parameters for creating a draft issue
            - run_gh_command returns a non-dict value
        When:
            - _create_github_project_item_impl is called
        Then:
            - An error dictionary is returned
        """
        # Given
        mock_project_id = 123
        mock_title = "New Draft Issue"
        mock_owner = "test-owner"
        unexpected_output = "Created draft issue"  # String instead of dict
        mock_run_gh.return_value = unexpected_output

        # Simulate resolve_param returning owner
        def resolve_side_effect(capability, param_name, val, type_hint=None):
            if param_name == "item_list_owner" and val is None:
                return mock_owner
            return val

        mock_resolve_param.side_effect = resolve_side_effect

        expected_error = {
            "error": "Unexpected result from gh project item-create",
            "raw": unexpected_output,
        }

        # When
        result = _create_github_project_item_impl(
            project_id=mock_project_id, title=mock_title
        )

        # Then
        assert result == expected_error
        mock_run_gh.assert_called_once()


class TestCreateGithubProjectField:
    """Tests for the _create_github_project_field_impl function.

    This test class verifies the functionality for creating GitHub project fields,
    handling different parameters, and error scenarios.
    """

    # Test data
    MOCK_CREATED_FIELD = {
        "id": "PVTF_lADOB3Xs84AAzA0",
        "name": "Status",
        "dataType": "SINGLE_SELECT",
        "options": [{"id": "opt1", "name": "To Do"}, {"id": "opt2", "name": "Done"}],
    }

    def test_success_text_field(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test creating a text field successfully.

        Given:
            - A project ID
            - Valid owner, name, data_type
        When:
            - _create_github_project_field_impl is called
        Then:
            - The correct command is sent to run_gh_command
            - The field creation response is returned
        """
        # Given
        mock_project_id = 123
        mock_owner = "test-org"
        mock_name = "Priority"
        mock_data_type = "TEXT"
        expected_field = {**self.MOCK_CREATED_FIELD, "dataType": "TEXT"}
        mock_run_gh.return_value = expected_field
        # Simulate owner resolving
        mock_resolve_param.side_effect = lambda cap, param, val, *args, **kwargs: (
            mock_owner if param == "field_owner" else val
        )

        expected_command = [
            "project",
            "field-create",
            str(mock_project_id),
            "--owner",
            mock_owner,
            "--name",
            mock_name,
            "--data-type",
            "TEXT",
        ]

        # When
        result = _create_github_project_field_impl(
            project_id=mock_project_id,
            owner=mock_owner,
            name=mock_name,
            data_type=mock_data_type,
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_field

    def test_success_single_select_field(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test creating a single select field successfully.

        Given: Valid project ID, owner, name, data_type, and options for a SINGLE_SELECT field
        When: _create_github_project_field_impl is called
        Then: run_gh_command is called with the correct parameters including options
        """
        # Given
        project_id = "12345"
        owner = "test-owner"
        name = "Priority"
        data_type = "SINGLE_SELECT"
        options = ["High", "Medium", "Low"]
        mock_run_gh.return_value = self.MOCK_CREATED_FIELD
        mock_resolve_param.return_value = owner  # Simulate owner resolving

        # When
        result = _create_github_project_field_impl(
            project_id=project_id,
            owner=owner,
            name=name,
            data_type=data_type,
            single_select_options=options,
        )

        # Then
        expected_command = [
            "project",
            "field-create",
            project_id,
            "--owner",
            owner,
            "--name",
            name,
            "--data-type",
            "SINGLE_SELECT",
            "--single-select-options",
            "High,Medium,Low",
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == self.MOCK_CREATED_FIELD

    def test_error_no_owner(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test error when owner is not provided.

        Given: Project ID and field details but no owner
        When: _create_github_project_field_impl is called
        Then: Error is returned indicating owner is required
        """
        # Given
        project_id = "12345"
        name = "Status"
        data_type = "TEXT"
        mock_resolve_param.return_value = None  # Simulate owner resolving to None

        # When
        result = _create_github_project_field_impl(
            project_id=project_id, name=name, data_type=data_type
        )

        # Then
        assert "error" in result
        assert "Owner is required" in result["error"]
        mock_run_gh.assert_not_called()

    def test_error_no_name(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test error when name is not provided.

        Given: Project ID, owner, and data_type but no name
        When: _create_github_project_field_impl is called
        Then: Error is returned indicating name is required
        """
        # Given
        project_id = "12345"
        owner = "test-owner"
        data_type = "TEXT"
        mock_resolve_param.return_value = owner  # Simulate owner resolving

        # When
        result = _create_github_project_field_impl(
            project_id=project_id, owner=owner, data_type=data_type
        )

        # Then
        assert "error" in result
        assert "Field name is required" in result["error"]
        mock_run_gh.assert_not_called()

    def test_error_no_data_type(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test error when data_type is not provided.

        Given: Project ID, owner, and name but no data_type
        When: _create_github_project_field_impl is called
        Then: Error is returned indicating data_type is required
        """
        # Given
        project_id = "12345"
        owner = "test-owner"
        name = "Status"
        mock_resolve_param.return_value = owner  # Simulate owner resolving

        # When
        result = _create_github_project_field_impl(
            project_id=project_id, owner=owner, name=name
        )

        # Then
        assert "error" in result
        assert "Field data_type is required" in result["error"]
        mock_run_gh.assert_not_called()

    def test_error_invalid_data_type(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test error when an invalid data_type is provided.

        Given: Project ID, owner, name, and an invalid data_type
        When: _create_github_project_field_impl is called
        Then: Error is returned indicating the data_type is invalid
        """
        # Given
        project_id = "12345"
        owner = "test-owner"
        name = "Status"
        invalid_data_type = "INVALID_TYPE"
        mock_resolve_param.return_value = owner  # Simulate owner resolving

        # When
        result = _create_github_project_field_impl(
            project_id=project_id, owner=owner, name=name, data_type=invalid_data_type
        )

        # Then
        assert "error" in result
        assert f"Invalid data_type '{invalid_data_type}'" in result["error"]
        mock_run_gh.assert_not_called()

    def test_error_single_select_no_options(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test error when SINGLE_SELECT is used without options.

        Given: Project ID, owner, name, SINGLE_SELECT data_type, but no options
        When: _create_github_project_field_impl is called
        Then: Error is returned indicating options are required
        """
        # Given
        project_id = "12345"
        owner = "test-owner"
        name = "Priority"
        data_type = "SINGLE_SELECT"
        mock_resolve_param.return_value = owner  # Simulate owner resolving

        # When
        result = _create_github_project_field_impl(
            project_id=project_id, owner=owner, name=name, data_type=data_type
        )

        # Then
        assert "error" in result
        assert "single_select_options are required" in result["error"]
        mock_run_gh.assert_not_called()

    def test_warning_options_with_non_select(
        self,
        mock_run_gh: MagicMock,
        mock_resolve_param: MagicMock,
        capsys: "CaptureFixture[str]",
    ) -> None:
        """Test warning when options are provided with non-SINGLE_SELECT type.

        Given: Project ID, owner, name, TEXT data_type, but with options
        When: _create_github_project_field_impl is called
        Then: Warning is printed and options are ignored in the command
        """
        # Given
        project_id = "12345"
        owner = "test-owner"
        name = "Notes"
        data_type = "TEXT"
        options = ["Unused", "Options"]
        expected_result = {"id": "PVTF_textid", "name": name, "dataType": "TEXT"}
        mock_run_gh.return_value = expected_result
        mock_resolve_param.return_value = owner  # Simulate owner resolving

        # When
        result = _create_github_project_field_impl(
            project_id=project_id,
            owner=owner,
            name=name,
            data_type=data_type,
            single_select_options=options,
        )

        # Then
        expected_command = [
            "project",
            "field-create",
            project_id,
            "--owner",
            owner,
            "--name",
            name,
            "--data-type",
            "TEXT",
            # No options included
        ]
        mock_run_gh.assert_called_once_with(expected_command)
        captured = capsys.readouterr()
        assert (
            "Warning: single_select_options provided but data_type is 'TEXT'"
            in captured.err
        )
        assert result == expected_result

    def test_gh_error(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test handling gh command errors.

        Given: Valid parameters but gh command returns an error
        When: _create_github_project_field_impl is called
        Then: Error from gh command is returned
        """
        # Given
        project_id = "12345"
        owner = "test-owner"
        name = "Priority"
        data_type = "DATE"
        error_response = {
            "error": "Field creation failed",
            "details": "Authentication failed",
        }
        mock_run_gh.return_value = error_response
        mock_resolve_param.return_value = owner  # Simulate owner resolving

        # When
        result = _create_github_project_field_impl(
            project_id=project_id, owner=owner, name=name, data_type=data_type
        )

        # Then
        assert result == error_response
        mock_run_gh.assert_called_once()

    def test_unexpected_output(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test handling unexpected output.

        Given: Valid parameters but gh command returns unexpected output
        When: _create_github_project_field_impl is called
        Then: Error indicating unexpected output is returned
        """
        # Given
        project_id = "12345"
        owner = "test-owner"
        name = "Status"
        data_type = "TEXT"
        unexpected_output = "Field created successfully"  # String instead of dict
        mock_run_gh.return_value = unexpected_output
        mock_resolve_param.return_value = owner  # Simulate owner resolving

        # When
        result = _create_github_project_field_impl(
            project_id=project_id, owner=owner, name=name, data_type=data_type
        )

        # Then
        assert "error" in result
        assert "Unexpected output" in result["error"]
        assert result["raw"] == unexpected_output

    def test_unexpected_output_format(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test handling unexpected output format from field creation.

        Given:
            - Valid project ID, owner, name, data_type
            - run_gh_command returns an unexpected format (string/non-error dict)
        When:
            - _create_github_project_field_impl is called
        Then:
            - An error dictionary is returned with the raw output
        """
        # Given
        mock_project_id = 123
        mock_owner = "test-org"
        mock_name = "Priority"
        mock_data_type = "TEXT"

        # Mock an unexpected output (not a dict with id/name or error)
        unexpected_output = "Created field successfully"
        mock_run_gh.return_value = unexpected_output

        # Simulate owner resolving
        mock_resolve_param.side_effect = lambda cap, param, val, *args, **kwargs: (
            mock_owner if param == "field_owner" else val
        )

        expected_command = [
            "project",
            "field-create",
            str(mock_project_id),
            "--owner",
            mock_owner,
            "--name",
            mock_name,
            "--data-type",
            "TEXT",
        ]

        # When
        result = _create_github_project_field_impl(
            project_id=mock_project_id,
            owner=mock_owner,
            name=mock_name,
            data_type=mock_data_type,
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert "error" in result
        assert result["error"] == "Unexpected output during field creation"
        assert result["raw"] == unexpected_output

    def test_unexpected_output_detailed(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test handling unexpected output format from field creation in detail.

        Given:
            - Valid project ID, owner, name, data_type
            - run_gh_command returns an unexpected format (non-JSON string)
        When:
            - _create_github_project_field_impl is called
        Then:
            - An error dictionary is returned with the raw output
        """
        # Given
        mock_project_id = 456
        mock_owner = "test-org"
        mock_name = "Status"
        mock_data_type = "TEXT"
        # Simulate non-JSON string output
        unexpected_output = "Field created successfully. Use ID: PVTF_xyz123"
        mock_run_gh.return_value = unexpected_output
        mock_resolve_param.side_effect = lambda cap, param, val, *args, **kwargs: (
            mock_owner if param == "field_owner" else val
        )

        # When
        result = _create_github_project_field_impl(
            project_id=mock_project_id,
            owner=mock_owner,
            name=mock_name,
            data_type=mock_data_type,
        )

        # Then
        assert "error" in result
        assert result["error"] == "Unexpected output during field creation"
        assert result["raw"] == unexpected_output

    def test_unexpected_output_non_dict_non_string(
        self, mock_run_gh: MagicMock, mock_resolve_param: MagicMock
    ) -> None:
        """Test handling unexpected output format that's neither a dict nor a string.

        Given:
            - Valid project ID, owner, name, data_type
            - run_gh_command returns a list (not a dict or string)
        When:
            - _create_github_project_field_impl is called
        Then:
            - An error dictionary is returned with the raw output
        """
        # Given
        mock_project_id = 789
        mock_owner = "test-org"
        mock_name = "Priority"
        mock_data_type = "TEXT"

        # Mock an unexpected output - in this case a list
        unexpected_output = [{"name": "Priority"}]  # List instead of dict or string
        mock_run_gh.return_value = unexpected_output

        # Simulate owner resolving
        mock_resolve_param.side_effect = lambda cap, param, val, *args, **kwargs: (
            mock_owner if param == "field_owner" else val
        )

        expected_command = [
            "project",
            "field-create",
            str(mock_project_id),
            "--owner",
            mock_owner,
            "--name",
            mock_name,
            "--data-type",
            "TEXT",
        ]

        # When
        result = _create_github_project_field_impl(
            project_id=mock_project_id,
            owner=mock_owner,
            name=mock_name,
            data_type=mock_data_type,
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert "error" in result
        assert result["error"] == "Unexpected output during field creation"
        assert result["raw"] == unexpected_output


class TestDeleteGithubProjectField:
    """Tests for the _delete_github_project_field_impl function.

    This test class verifies the functionality for deleting GitHub project fields
    and handling error scenarios.
    """

    def test_success(self, mock_run_gh: MagicMock) -> None:
        """Test successfully deleting a project field.

        Given: A field ID
        When: _delete_github_project_field_impl is called
        Then: run_gh_command is called with correct parameters
        """
        # Given
        field_id = "PVTF_lADOB3Xs84AAzA0"
        success_message = "Field 'Status' deleted"
        mock_run_gh.return_value = success_message

        # When
        result = _delete_github_project_field_impl(field_id=field_id)

        # Then
        expected_command = ["project", "field-delete", field_id]
        mock_run_gh.assert_called_once_with(expected_command)
        assert result["status"] == "success"
        assert result["message"] == success_message

    def test_warning_project_id_ignored(
        self, mock_run_gh: MagicMock, capsys: "CaptureFixture[str]"
    ) -> None:
        """Test warning when project_id is provided but ignored.

        Given: A field ID and a project_id
        When: _delete_github_project_field_impl is called
        Then: Warning is printed and project_id is not included in command
        """
        # Given
        field_id = "PVTF_lADOB3Xs84AAzA0"
        project_id = "12345"
        success_message = "Field 'Status' deleted"
        mock_run_gh.return_value = success_message

        # When
        result = _delete_github_project_field_impl(
            field_id=field_id, project_id=project_id
        )

        # Then
        expected_command = ["project", "field-delete", field_id]
        mock_run_gh.assert_called_once_with(expected_command)
        captured = capsys.readouterr()
        assert (
            f"Warning: project_id '{project_id}' provided but not used" in captured.err
        )
        assert result["status"] == "success"
        assert result["message"] == success_message

    def test_empty_response(self, mock_run_gh: MagicMock) -> None:
        """Test handling empty response from gh command.

        Given: A field ID and gh command returns empty/None
        When: _delete_github_project_field_impl is called
        Then: Default success message is returned
        """
        # Given
        field_id = "PVTF_lADOB3Xs84AAzA0"
        mock_run_gh.return_value = None  # Empty response

        # When
        result = _delete_github_project_field_impl(field_id=field_id)

        # Then
        assert result["status"] == "success"
        assert result["message"] == "Field deleted successfully."

    def test_gh_error(self, mock_run_gh: MagicMock) -> None:
        """Test handling gh command errors.

        Given: A field ID but gh command returns an error
        When: _delete_github_project_field_impl is called
        Then: Error from gh command is returned
        """
        # Given
        field_id = "PVTF_lADOB3Xs84AAzA0"
        error_response = {
            "error": "Field deletion failed",
            "details": "Field not found",
        }
        mock_run_gh.return_value = error_response

        # When
        result = _delete_github_project_field_impl(field_id=field_id)

        # Then
        assert result == error_response


class TestInitTools:
    """Tests for the init_tools function in projects module."""

    def test_init_tools_registers_all_tools(self, mocker: "MockerFixture") -> None:
        """Test that init_tools registers all the project-related tools.

        Given: A FastMCP server instance
        When: init_tools is called
        Then: All project-related tool implementations are registered with the server
        """
        # Given
        from gh_project_manager_mcp.tools.projects import (
            _add_github_project_item_impl,
            _archive_github_project_item_impl,
            _create_github_project_field_impl,
            _create_github_project_item_impl,
            _delete_github_project_field_impl,
            _delete_github_project_item_impl,
            _edit_github_project_item_impl,
            _list_github_project_fields_impl,
            _list_github_project_items_impl,
            _view_github_project_impl,
            init_tools,
        )

        # Create a mock FastMCP server
        mock_server = mocker.MagicMock()
        mock_tool_decorator = mocker.MagicMock()
        mock_server.tool.return_value = mock_tool_decorator

        # When
        init_tools(mock_server)

        # Then
        assert mock_server.tool.call_count == 10  # 10 tool implementations

        # Verify each tool is registered
        all_impls = [
            _create_github_project_field_impl,
            _delete_github_project_field_impl,
            _list_github_project_fields_impl,
            _add_github_project_item_impl,
            _archive_github_project_item_impl,
            _delete_github_project_item_impl,
            _edit_github_project_item_impl,
            _list_github_project_items_impl,
            _view_github_project_impl,
            _create_github_project_item_impl,
        ]

        for impl in all_impls:
            mock_tool_decorator.assert_any_call(impl)
