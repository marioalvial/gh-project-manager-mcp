# tests/tools/test_projects.py
"""Unit tests for the GitHub projects tools."""

from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from unittest.mock import patch

import pytest

# Import implementations as they are added
from gh_project_manager_mcp.tools.projects import (
    _add_github_project_item_impl,
    _archive_github_project_item_impl,
    _delete_github_project_item_impl,
    _edit_github_project_item_impl,
    _list_github_project_fields_impl,
    _list_github_project_items_impl,
    _list_github_projects_impl,
    _view_github_project_impl,
    # _copy_github_project_impl,  # Keep commented until tests added
    # _create_github_project_impl,
    # _delete_github_project_impl,
    # _create_github_project_field_impl,
    # _delete_github_project_field_impl,
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
def mock_run_gh() -> "MagicMock":
    """Provide a mock for the run_gh_command utility function.
    
    This fixture mocks the run_gh_command function imported in the projects module,
    allowing tests to control what the command returns.
    
    Returns:
        The mock object for run_gh_command that can be customized in tests.
    """
    # Use the correct path for patching within the projects module
    with patch("gh_project_manager_mcp.tools.projects.run_gh_command") as mock:
        yield mock


@pytest.fixture
def mock_resolve_param() -> "MagicMock":
    """Provide a mock for the resolve_param utility function.
    
    This fixture mocks the resolve_param function imported in the projects module,
    with a default behavior that passes through runtime values.
    
    Returns:
        The mock object for resolve_param that can be customized in tests.
    """
    # Use the correct path for patching within the projects module
    with patch("gh_project_manager_mcp.tools.projects.resolve_param") as mock:
        # Default behavior: return the value passed in
        mock.side_effect = lambda capability, param_name, value, type_hint=None: value
        yield mock


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
        capsys: "CaptureFixture[str]"
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
        result = _list_github_project_fields_impl(
            project_id=mock_project_id, owner=mock_owner, limit=mock_invalid_limit
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_gh_output
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
        expected_gh_output = {"items": [self.MOCK_ADDED_ITEM]}  # Simulate typical gh output
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
            project_id=mock_project_id, issue_id=mock_issue_id, pull_request_id=mock_pr_id
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
        expected_gh_output = {"item": self.MOCK_ARCHIVED_ITEM}  # Simulate typical gh output
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
            item_id=mock_item_id, owner=mock_owner, project_id=mock_project_id, undo=True
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
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
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
        expected_gh_output = {"item": self.MOCK_EDITED_ITEM}  # Simulate typical gh output
        mock_run_gh.return_value = expected_gh_output
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # Resolve owner/proj to None

        expected_command = [
            "project",
            "item-edit",
            mock_item_id,
            "--format",
            "json",
            "--field-id",
            mock_field_id,
            "--text",
            mock_text,
        ]

        # When
        result = _edit_github_project_item_impl(
            item_id=mock_item_id, field_id=mock_field_id, text_value=mock_text
        )

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == self.MOCK_EDITED_ITEM  # Should extract item

    def test_success_number(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
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
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: None

        expected_command = [
            "project",
            "item-edit",
            mock_item_id,
            "--format",
            "json",
            "--field-id",
            mock_field_id,
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
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
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
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: None

        expected_command = [
            "project",
            "item-edit",
            mock_item_id,
            "--format",
            "json",
            "--field-id",
            mock_field_id,
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

        # When
        result = _edit_github_project_item_impl(
            item_id=mock_item_id, field_id=mock_field_id, date_value=mock_invalid_date
        )

        # Then
        assert "error" in result
        assert "Invalid date_value" in result["error"]
        assert "YYYY-MM-DD" in result["error"]
        mock_run_gh.assert_not_called()

    def test_success_single_select(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
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
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: None

        expected_command = [
            "project",
            "item-edit",
            mock_item_id,
            "--format",
            "json",
            "--field-id",
            mock_field_id,
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
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
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
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: None

        expected_command = [
            "project",
            "item-edit",
            mock_item_id,
            "--format",
            "json",
            "--field-id",
            mock_field_id,
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
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
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
        mock_run_gh.return_value = {"item": self.MOCK_EDITED_ITEM}  # Assume item returned
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: None

        expected_command = [
            "project",
            "item-edit",
            mock_item_id,
            "--format",
            "json",
            "--field-id",
            mock_field_id,
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
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
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
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # Resolve to None

        expected_command = [
            "project",
            "item-edit",
            mock_item_id,
            "--format",
            "json",
            "--field-id",
            mock_field_id,
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
        capsys: "CaptureFixture[str]"
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
        assert result == expected_gh_output
        captured = capsys.readouterr()
        assert f"Warning: Invalid limit '{mock_invalid_limit}'" in captured.err

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


# --- Test _list_github_projects_impl ---

class TestListGithubProjects:
    """Tests for the _list_github_projects_impl function.
    
    This test class verifies the functionality for listing GitHub projects,
    handling different parameters, and error scenarios.
    """
    
    # Test data
    MOCK_PROJECT_LIST_ITEM = {
        "id": "PVT_kwDOB3Xs84AAzA0",
        "title": "Project Alpha",
        "number": 1,
        "owner": {"type": "Organization", "login": "my-org"},
    }
    MOCK_CLOSED_PROJECT_ITEM = {
        "id": "PVT_xxxxxxxxxxxxxx",
        "title": "Old Project",
        "number": 2,
        "closed": True,
        "owner": {"type": "User", "login": "test-user"},
    }

    def test_success_basic(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test listing projects with basic parameters (owner).

        Given:
            - Basic parameters for listing projects (owner)
        When:
            - _list_github_projects_impl is called
        Then:
            - run_gh_command is called correctly
            - The list of projects is returned
        """
        # Given
        mock_owner = "my-org"
        expected_gh_output = [self.MOCK_PROJECT_LIST_ITEM]
        mock_run_gh.return_value = expected_gh_output
        # Simulate owner resolving, limit resolving to None
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: (
            mock_owner if param == "list_owner" else None
        )

        expected_command = [
            "project",
            "list",
            "--format",
            "json",
            "--owner",
            mock_owner,
            # No limit or closed flags
        ]

        # When
        result = _list_github_projects_impl(owner=mock_owner)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_gh_output

    def test_success_with_opts(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test listing projects with owner, limit, and closed flag.

        Given:
            - Parameters including owner, limit, and closed=True
        When:
            - _list_github_projects_impl is called
        Then:
            - run_gh_command is called with owner, limit, and closed flags
            - The list of projects is returned
        """
        # Given
        mock_owner = "test-user"
        mock_limit = 10
        expected_gh_output = [self.MOCK_CLOSED_PROJECT_ITEM]
        mock_run_gh.return_value = expected_gh_output
        # Simulate parameters resolving to provided values
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: val

        expected_command = [
            "project",
            "list",
            "--format",
            "json",
            "--owner",
            mock_owner,
            "--closed",
            "--limit",
            str(mock_limit),
        ]

        # When
        result = _list_github_projects_impl(owner=mock_owner, limit=mock_limit, closed=True)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_gh_output

    def test_success_invalid_limit(
        self, 
        mock_run_gh: "MagicMock", 
        mock_resolve_param: "MagicMock", 
        capsys: "CaptureFixture[str]"
    ) -> None:
        """Test listing projects handles invalid limit value.

        Given:
            - An invalid limit value
        When:
            - _list_github_projects_impl is called
        Then:
            - run_gh_command is called without limit
            - A warning is printed to stderr
            - The list of projects is returned
        """
        # Given
        mock_owner = "another-org"
        mock_invalid_limit = 0
        expected_gh_output = []
        mock_run_gh.return_value = expected_gh_output
        # Simulate parameters resolving to provided values
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: val

        expected_command = [
            "project",
            "list",
            "--format",
            "json",
            "--owner",
            mock_owner,
            # No limit flag
        ]

        # When
        result = _list_github_projects_impl(owner=mock_owner, limit=mock_invalid_limit)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == expected_gh_output
        captured = capsys.readouterr()
        assert f"Warning: Invalid limit '{mock_invalid_limit}'" in captured.err

    def test_error_no_owner(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test error when no owner is provided or resolved for listing projects.

        Given:
            - No owner provided or resolved
        When:
            - _list_github_projects_impl is called
        Then:
            - An error is returned immediately
            - run_gh_command is not called
        """
        # Given
        mock_resolve_param.side_effect = (
            lambda cap, param, val, type_hint=None: None
        )  # Owner resolves to None

        # When
        result = _list_github_projects_impl()

        # Then
        assert isinstance(result, list) and len(result) == 1
        assert "error" in result[0]
        assert "Owner parameter is required" in result[0]["error"]
        mock_run_gh.assert_not_called()

    def test_gh_error(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test error handling when gh fails listing projects.

        Given:
            - run_gh_command returns an error dictionary
        When:
            - _list_github_projects_impl is called
        Then:
            - The error dictionary is returned, wrapped in a list
        """
        # Given
        mock_owner = "error-owner"
        error_output = {
            "error": "gh command failed",
            "stderr": "Not authorized",
            "exit_code": 1,
        }
        mock_run_gh.return_value = error_output
        # Simulate owner resolving, limit resolving to None
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: (
            mock_owner if param == "list_owner" else None
        )

        expected_command = ["project", "list", "--format", "json", "--owner", mock_owner]

        # When
        result = _list_github_projects_impl(owner=mock_owner)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == [error_output]

    def test_unexpected_output(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test handling unexpected non-list/non-error output for project list.

        Given:
            - run_gh_command returns an unexpected non-list/non-error type
        When:
            - _list_github_projects_impl is called
        Then:
            - An error dictionary is returned, wrapped in a list
        """
        # Given
        mock_owner = "strange-output-owner"
        unexpected_output = "Plain text list."
        mock_run_gh.return_value = unexpected_output
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: (
            mock_owner if param == "list_owner" else None
        )

        expected_command = ["project", "list", "--format", "json", "--owner", mock_owner]
        expected_error = {
            "error": "Unexpected result from gh project list",
            "raw": unexpected_output,
        }

        # When
        result = _list_github_projects_impl(owner=mock_owner)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == [expected_error]

    def test_old_gh_format(
        self, mock_run_gh: "MagicMock", mock_resolve_param: "MagicMock"
    ) -> None:
        """Test handling old gh output format ({'projects': [...]}) for project list.

        Given:
            - run_gh_command returns JSON wrapped in a {'projects': [...]} structure
        When:
            - _list_github_projects_impl is called
        Then:
            - The inner list from the 'projects' key is returned
        """
        # Given
        mock_owner = "old-format-owner"
        old_format_output = {"projects": [self.MOCK_PROJECT_LIST_ITEM]}
        mock_run_gh.return_value = old_format_output
        mock_resolve_param.side_effect = lambda cap, param, val, type_hint=None: (
            mock_owner if param == "list_owner" else None
        )

        expected_command = ["project", "list", "--format", "json", "--owner", mock_owner]

        # When
        result = _list_github_projects_impl(owner=mock_owner)

        # Then
        mock_run_gh.assert_called_once_with(expected_command)
        assert result == old_format_output["projects"]


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
        capsys: "CaptureFixture[str]"
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


# Add test functions here as project commands are implemented
# ... (rest of the file remains the same)
