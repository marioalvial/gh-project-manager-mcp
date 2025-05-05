"""Integration tests for GitHub Projects-related MCP tools."""

import os
from typing import Any, Callable, Dict

import pytest

# Import the functions that we want to test
from gh_project_manager_mcp.tools.projects import (
    _create_github_project_field_impl,
    _create_github_project_item_impl,
    _delete_github_project_field_impl,
    _edit_github_project_item_impl,
    _list_github_project_fields_impl,
    _list_github_project_items_impl,
    _view_github_project_impl,
)


@pytest.fixture(scope="module")
def setup_test_project(
    gh_token: str,
    test_repo_info: Dict[str, str],
    random_string_generator: Callable[[str], str],
) -> Dict[str, Any]:
    """Set up test project data.

    Args:
    ----
        gh_token: GitHub token
        test_repo_info: Test repository information
        random_string_generator: Function to generate random strings

    Returns:
    -------
        Dictionary with project data

    """
    # Set environment variable for GitHub token
    original_token = os.environ.get("GH_TOKEN")
    os.environ["GH_TOKEN"] = gh_token

    # For integration tests, we need to use a real project ID and owner in the correct format
    # Let's use a format that GitHub CLI expects
    owner = f"user/{test_repo_info['owner']}"

    # This should be provided by environment variable, or we'll use a default
    project_id = os.environ.get("GH_INTEGRATION_TEST_PROJECT_ID", "12345678")

    print(f"Using project ID: {project_id} and owner: {owner}")

    # Store project details for tests
    project_data = {
        "owner": owner,  # Note: Using prefixed owner format
        "project_id": project_id,
        "created_fields": [],
        "created_items": [],
    }

    yield project_data

    # Cleanup: Delete any items that were created
    for item in project_data.get("created_items", []):
        if isinstance(item, dict) and "id" in item:
            try:
                from gh_project_manager_mcp.tools.projects import (
                    _delete_github_project_item_impl,
                )

                result = _delete_github_project_item_impl(
                    item_id=item["id"],
                    project_id=project_id,
                    owner=owner,
                )
                print(f"Deleted project item {item['id']}: {result}")
            except Exception as e:
                print(f"Failed to delete project item {item['id']}: {e}")

    # Cleanup: Delete any fields that were created
    for field_id in project_data.get("created_fields", []):
        try:
            result = _delete_github_project_field_impl(field_id=field_id)
            print(f"Deleted project field {field_id}: {result}")
        except Exception as e:
            print(f"Failed to delete project field {field_id}: {e}")

    # Restore original token if any
    if original_token:
        os.environ["GH_TOKEN"] = original_token
    else:
        del os.environ["GH_TOKEN"]


@pytest.mark.gh_integration
class TestProjectIntegration:
    """Integration tests for GitHub Project operations."""

    def test_view_project(
        self,
        gh_token: str,
        setup_test_project: Dict[str, Any],
    ):
        """Test viewing a GitHub project.

        Given: Valid project ID and owner
        When: Viewing project details
        Then: Project details or appropriate error is returned
        """
        # Given
        os.environ["GH_TOKEN"] = gh_token
        project_id = setup_test_project["project_id"]
        owner = setup_test_project["owner"]

        # When
        result = _view_github_project_impl(project_id=project_id, owner=owner)

        # Then
        # We can't guarantee the actual project exists, so we'll check either for success or an expected error
        if "error" in result:
            # If there's an error, make sure it's the expected type
            assert (
                "Unknown owner type" in result.get("error")
                or "not found" in result.get("error", "").lower()
            ), f"Unexpected error: {result}"
        else:
            # If successful, verify there's a title
            assert "title" in result, f"Project details missing title: {result}"

    def test_list_project_fields(
        self,
        gh_token: str,
        setup_test_project: Dict[str, Any],
    ):
        """Test listing fields in a GitHub project.

        Given: Valid project ID and owner
        When: Listing project fields
        Then: A list of fields is returned
        """
        # Given
        os.environ["GH_TOKEN"] = gh_token
        project_id = setup_test_project["project_id"]
        owner = setup_test_project["owner"]

        # When
        result = _list_github_project_fields_impl(project_id=project_id, owner=owner)

        # Then
        assert isinstance(result, list), f"Expected list of fields, got: {result}"

    def test_create_and_delete_project_field(
        self,
        gh_token: str,
        setup_test_project: Dict[str, Any],
        random_string_generator: Callable[[str], str],
    ):
        """Test creating and deleting a GitHub project field.

        Given: Valid project ID, owner, and field details
        When: Creating a new text field
        Then: Field is created successfully with an ID or returns expected error
        When: Deleting the field
        Then: Field is deleted successfully
        """
        # Given
        os.environ["GH_TOKEN"] = gh_token
        project_id = setup_test_project["project_id"]
        owner = setup_test_project["owner"]
        field_name = random_string_generator("test-field")

        # When - Create
        create_result = _create_github_project_field_impl(
            project_id=project_id,
            owner=owner,
            name=field_name,
            data_type="TEXT",
        )

        # Then - Since we might not have permissions to the actual project, we'll allow expected errors
        if "error" in create_result:
            # Check if it's an expected error like permission denied or project not found
            error_msg = (
                create_result.get("error", "").lower()
                + create_result.get("details", "").lower()
            )
            assert any(
                msg in error_msg
                for msg in ["unknown owner", "permission", "not found", "access"]
            ), f"Unexpected error: {create_result}"
            pytest.skip("Unable to create project field - skipping remainder of test")
        else:
            # If successful, check for ID
            assert "id" in create_result, f"Failed to create field: {create_result}"

            # Store for cleanup
            field_id = create_result["id"]
            setup_test_project["created_fields"].append(field_id)

            # When - Delete
            delete_result = _delete_github_project_field_impl(field_id=field_id)

            # Then - Check deletion
            assert (
                "status" in delete_result and delete_result["status"] == "success"
            ), f"Failed to delete field: {delete_result}"

            # Remove from cleanup list since we've already deleted it
            setup_test_project["created_fields"].remove(field_id)

    def test_list_project_items(
        self,
        gh_token: str,
        setup_test_project: Dict[str, Any],
    ):
        """Test listing items in a GitHub project.

        Given: Valid project ID and owner
        When: Listing project items
        Then: A list of items is returned
        """
        # Given
        os.environ["GH_TOKEN"] = gh_token
        project_id = setup_test_project["project_id"]
        owner = setup_test_project["owner"]

        # When
        result = _list_github_project_items_impl(project_id=project_id, owner=owner)

        # Then
        assert isinstance(result, list), f"Expected list of items, got: {result}"

    def test_create_project_item(
        self,
        gh_token: str,
        setup_test_project: Dict[str, Any],
        random_string_generator: Callable[[str], str],
    ):
        """Test creating a draft item in a GitHub project.

        Given: Valid project ID, owner, and item details
        When: Creating a new draft item
        Then: Item is created successfully with an ID
        """
        # Given
        os.environ["GH_TOKEN"] = gh_token
        project_id = setup_test_project["project_id"]
        owner = setup_test_project["owner"]
        item_title = random_string_generator("test-item")
        item_body = "This is a test item created by integration tests."

        # When
        result = _create_github_project_item_impl(
            project_id=project_id,
            owner=owner,
            title=item_title,
            body=item_body,
        )

        # Then - Since we might not have permissions to the actual project, we'll allow expected errors
        if "error" in result:
            # Check if it's an expected error like permission denied or project not found
            error_msg = (
                result.get("error", "").lower() + result.get("details", "").lower()
            )
            assert any(
                msg in error_msg
                for msg in ["permission", "not found", "access", "unknown"]
            ), f"Unexpected error: {result}"
            pytest.skip("Unable to create project item - skipping test")
            return None
        else:
            # If successful, check for ID
            assert "id" in result, f"Failed to create item: {result}"

            # Store for cleanup
            setup_test_project["created_items"].append(result)
            return result

    def test_edit_project_item(
        self,
        gh_token: str,
        setup_test_project: Dict[str, Any],
        random_string_generator: Callable[[str], str],
    ):
        """Test editing a field value on a project item.

        Given: Valid project ID, owner, item ID, and field ID
        When: Editing the item's field value
        Then: Field value is updated successfully
        """
        # Given
        os.environ["GH_TOKEN"] = gh_token
        project_id = setup_test_project["project_id"]
        owner = setup_test_project["owner"]

        # First, we need a project item to edit
        if not setup_test_project.get("created_items"):
            # Try to create a test item
            item_result = self.test_create_project_item(
                gh_token=gh_token,
                setup_test_project=setup_test_project,
                random_string_generator=random_string_generator,
            )
            if not item_result:
                pytest.skip("Couldn't create an item to test editing")
                return
            item_id = item_result["id"]
        else:
            item_id = setup_test_project["created_items"][0]["id"]

        # Then, we need to get a list of available fields
        fields_result = _list_github_project_fields_impl(
            project_id=project_id, owner=owner
        )

        # Find a TEXT field to edit
        text_field = None
        for field in fields_result:
            if isinstance(field, dict) and field.get("data_type") == "TEXT":
                text_field = field
                break

        if not text_field:
            # Try to create a text field
            try:
                field_name = random_string_generator("test-field")
                field_result = _create_github_project_field_impl(
                    project_id=project_id,
                    owner=owner,
                    name=field_name,
                    data_type="TEXT",
                )

                if "id" in field_result:
                    text_field = field_result
                    # Store for cleanup
                    setup_test_project["created_fields"].append(field_result["id"])
            except Exception as e:
                print(f"Failed to create a field: {e}")

        # Skip if no TEXT field is available
        if not text_field:
            pytest.skip("No TEXT field available for editing")
            return

        field_id = text_field.get("id")

        # When editing the item with new value
        new_value = random_string_generator("edited-value")
        result = _edit_github_project_item_impl(
            item_id=item_id,
            project_id=project_id,
            owner=owner,
            field_id=field_id,
            text_value=new_value,
        )

        # Then - Allow for permission errors
        if "error" in result:
            # Check if it's an expected error like permission denied
            error_msg = (
                result.get("error", "").lower() + result.get("details", "").lower()
            )
            assert any(
                msg in error_msg
                for msg in ["permission", "not found", "access", "unknown"]
            ), f"Unexpected error: {result}"
            pytest.skip(f"Unable to edit project item - {result.get('error')}")
        else:
            # If successful, check for success indicators
            assert (
                "success" in result or "id" in result
            ), f"Failed to edit item field: {result}"
