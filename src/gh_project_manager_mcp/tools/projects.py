# src/gh_project_manager_mcp/tools/projects.py
"""Tools for interacting with GitHub Projects via the gh CLI."""

import datetime
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from result import Err

from gh_project_manager_mcp.utils.config import resolve_param
from gh_project_manager_mcp.utils.error import (
    Error,
    ErrorCode,
)
from gh_project_manager_mcp.utils.gh_utils import (
    execute_gh_command,
    print_stderr,
)
from gh_project_manager_mcp.utils.response_handler import handle_result

# Replace the global print function
print = print_stderr

# Implementations of gh project commands

# --- Tool Implementations ---


@handle_result
def create_project_field(
    project_id: str,
    name: str = None,
    data_type: str = None,
    owner: str = None,
    single_select_options: List[str] = None,
) -> Dict[str, Any]:
    """Create a custom field in a GitHub project.

    Args:
    ----
        project_id: The ID of the project to add a field to
        name: The name of the field to create
        data_type: The type of field (TEXT, SINGLE_SELECT, DATE, NUMBER, ITERATION)
        owner: The owner of the project (user or organization)
        single_select_options: Options for SINGLE_SELECT type fields

    Returns:
    -------
        Result containing either the created field info or Error

    """
    # Resolve parameters from config or runtime values
    resolved_owner = resolve_param("global", "owner", owner)

    # Validate required parameters
    if not name:
        return Err(Error.required_param_missing(param="name"))

    if not data_type:
        return Err(Error.required_param_missing(param="data_type"))

    if not resolved_owner:
        return Err(Error.required_param_missing(param="owner"))

    # Build the command
    command = [
        "project",
        "field-create",
        project_id,
        "--owner",
        resolved_owner,
        "--name",
        name,
    ]

    # Validate data_type
    valid_data_types = ["TEXT", "SINGLE_SELECT", "DATE", "NUMBER", "ITERATION"]
    data_type_upper = data_type.upper() if data_type else ""
    if data_type_upper not in valid_data_types:
        return Err(
            Error.invalid_param(
                data_type,
                valid_data_types,
                "Invalid data_type. Must be one of the specified values.",
            )
        )

    command.extend(["--data-type", data_type_upper])

    # Handle single select options
    if data_type_upper == "SINGLE_SELECT" and not single_select_options:
        return Err(
            Error(
                ErrorCode.CONFIG_PARAM_NOT_FOUND,
                exception=Exception(
                    "single_select_options are required when data_type is "
                    "SINGLE_SELECT."
                ),
                format_args={"param": "single_select_options"},
            )
        )

    if data_type_upper != "SINGLE_SELECT" and single_select_options:
        print(
            f"Warning: single_select_options provided but data_type is "
            f"'{data_type_upper}'. Options will be ignored."
        )

    if data_type_upper == "SINGLE_SELECT" and single_select_options:
        command.extend(["--single-select-options", ",".join(single_select_options)])

    # Execute the command
    return execute_gh_command(command)


@handle_result
def delete_project_field(field_id: str) -> Dict[str, Any]:
    """Delete a field from a GitHub project.

    Args:
    ----
        field_id: The ID of the field to delete

    Returns:
    -------
        Result containing either success information or Error

    """
    # Build the command
    command = ["project", "field-delete", field_id]

    # Execute the command
    return execute_gh_command(command)


@handle_result
def list_project_fields(
    project_id: str,
    owner: str = None,
    limit: int = None,
) -> Dict[str, Any]:
    """List fields in a GitHub project.

    Args:
    ----
        project_id: The ID of the project
        owner: The owner of the project (user or organization)
        limit: Maximum number of fields to return

    Returns:
    -------
        Result containing either the list of fields as JSON or Error

    """
    # Resolve parameters from config or runtime values
    resolved_owner = resolve_param("global", "owner", owner)
    resolved_limit = resolve_param("project", "field_list_limit", limit)

    # Build the command
    command = ["project", "field-list", project_id, "--format", "json"]

    # Enhanced owner validation
    if resolved_owner:
        command.extend(["--owner", resolved_owner])

    # Add limit if provided
    if resolved_limit is not None:
        if isinstance(resolved_limit, int) and resolved_limit > 0:
            command.extend(["--limit", str(resolved_limit)])
        else:
            print_stderr(
                "Warning: Invalid limit '{}'. Must be a positive integer. "
                "Using default.".format(resolved_limit)
            )

    # Execute the command
    return execute_gh_command(command)


@handle_result
def add_project_item(
    project_id: str,
    owner: str = None,
    issue_id: str = None,
    pull_request_id: str = None,
) -> Dict[str, Any]:
    """Add an item (issue or PR) to a GitHub project.

    Args:
    ----
        project_id: The ID of the project
        owner: The owner of the project (user or organization)
        issue_id: The ID of the issue to add (exclusive with pull_request_id)
        pull_request_id: The ID of the pull request to add (exclusive with issue_id)

    Returns:
    -------
        Result containing either the added item as JSON or Error

    """
    # Resolve parameters from config or runtime values
    resolved_owner = resolve_param("global", "owner", owner)

    # Build the command
    command = ["project", "item-add", project_id, "--format", "json"]

    # Add owner if provided
    if resolved_owner:
        command.extend(["--owner", resolved_owner])

    # Check for missing parameters
    if issue_id is None and pull_request_id is None:
        return Err(
            Error(
                ErrorCode.REQUIRED_PARAM_MISSING,
                exception=Exception(
                    "Either issue_id or pull_request_id must be provided."
                ),
                format_args={"param": "issue_id or pull_request_id"},
            )
        )

    # Check for too many parameters
    if issue_id is not None and pull_request_id is not None:
        return Err(
            Error(
                ErrorCode.INVALID_PARAM,
                exception=Exception(
                    "Only one of issue_id or pull_request_id can be provided, not both."
                ),
                format_args={"param": "issue_id and pull_request_id"},
            )
        )

    # Add the appropriate parameter
    if issue_id is not None:
        command.extend(["--issue-id", issue_id])
    else:
        command.extend(["--pull-request-id", pull_request_id])

    # Execute the command
    return execute_gh_command(command)


@handle_result
def archive_project_item(
    item_id: str,
    project_id: str = None,
    owner: str = None,
    undo: bool = False,
) -> Dict[str, Any]:
    """Archive or unarchive a project item.

    Args:
    ----
        item_id: The ID of the item to archive/unarchive
        project_id: The ID of the project containing the item
        owner: The owner of the project (user or organization)
        undo: Flag to unarchive instead of archive

    Returns:
    -------
        Result containing either the archived/unarchived item as JSON or Error

    """
    # Resolve parameters from config or runtime values
    resolved_project_id = resolve_param("project", "project_id", project_id)
    resolved_owner = resolve_param("global", "owner", owner)

    # Build the command
    command = ["project", "item-archive", item_id, "--format", "json"]

    # Add owner if provided
    if resolved_owner:
        command.extend(["--owner", resolved_owner])

    # Add project_id if provided - FIXED to use resolved_project_id in condition
    if resolved_project_id:
        command.extend(["--project-id", resolved_project_id])

    # Add undo flag if requested
    if undo:
        command.append("--undo")

    # Execute the command
    return execute_gh_command(command)


@handle_result
def delete_project_item(
    item_id: str,
    project_id: str = None,
    owner: str = None,
) -> Dict[str, Any]:
    """Delete an item from a GitHub project.

    Args:
    ----
        item_id: The ID of the item to delete
        project_id: The ID of the project containing the item
        owner: The owner of the project (user or organization)

    Returns:
    -------
        Result containing either success information or Error

    """
    # Resolve parameters from config or runtime values
    resolved_project_id = resolve_param("project", "project_id", project_id)
    resolved_owner = resolve_param("global", "owner", owner)

    # Build the command
    command = ["project", "item-delete", item_id, "--format", "json"]

    # Add owner if provided
    if resolved_owner:
        command.extend(["--owner", resolved_owner])

    # Add project_id if provided
    if resolved_project_id:
        command.extend(["--project-id", resolved_project_id])

    # Execute the command
    return execute_gh_command(command)


@handle_result
def edit_project_item(
    item_id: str,
    field_id: str,
    project_node_id: str = None,
    text_value: str = None,
    number_value: float = None,
    date_value: str = None,
    single_select_option_id: str = None,
    iteration_id: str = None,
    clear: bool = False,
) -> Dict[str, Any]:
    """Edit a project item's field value.

    Args:
    ----
        item_id: The ID of the item to edit
        field_id: The ID of the field to edit
        project_node_id: The node ID of the project eg: PVT_kwHOARERcs4A4K2N
        text_value: Text value to set for the field
        number_value: Number value to set for the field
        date_value: Date value to set for the field (YYYY-MM-DD format)
        single_select_option_id: Single select option ID to set for the field
        iteration_id: Iteration ID to set for the field
        clear: Whether to clear the field value

    Returns:
    -------
        Result containing either the edited item as JSON or Error

    """
    # Validate clear vs value params
    value_provided = any(
        [
            text_value is not None,
            number_value is not None,
            date_value is not None,
            single_select_option_id is not None,
            iteration_id is not None,
        ]
    )

    if clear and value_provided:
        return Err(
            Error(
                ErrorCode.INVALID_PARAM,
                exception=Exception(
                    "Cannot provide a value parameter when using --clear."
                ),
                format_args={"param": "clear with value"},
            )
        )

    # Count provided value params
    value_count = sum(
        [
            text_value is not None,
            number_value is not None,
            date_value is not None,
            single_select_option_id is not None,
            iteration_id is not None,
        ]
    )

    if not clear and value_count == 0:
        return Err(
            Error(
                ErrorCode.REQUIRED_PARAM_MISSING,
                exception=Exception(
                    "Exactly one value parameter (text_value, number_value, etc.) "
                    "is required when not using clear=True."
                ),
                format_args={"param": "value parameter"},
            )
        )

    if value_count > 1:
        return Err(
            Error(
                ErrorCode.INVALID_PARAM,
                exception=Exception(
                    "Only one value parameter (text_value, number_value, etc.) "
                    "can be provided."
                ),
                format_args={"param": "multiple values"},
            )
        )

    # Resolve parameters from config or runtime values
    resolved_project_node_id = resolve_param(
        "project", "project_node_id", project_node_id
    )

    # Build the command
    command = [
        "project",
        "item-edit",
        "--id",
        item_id,
        "--format",
        "json",
        "--field-id",
        field_id,
    ]

    # Add project ID
    if resolved_project_node_id:
        command.extend(["--project-id", resolved_project_node_id])

    # Handle date validation separately since we need to parse it
    if date_value is not None:
        try:
            datetime.date.fromisoformat(date_value)
        except ValueError:
            return Err(
                Error(
                    ErrorCode.INVALID_PARAM,
                    exception=Exception(
                        f"Invalid date_value '{date_value}'. "
                        f"Expected YYYY-MM-DD format."
                    ),
                    format_args={
                        "param": "date_value",
                        "valid_params": "YYYY-MM-DD format",
                    },
                )
            )

    # Add clear or value parameter
    if clear:
        command.append("--clear")
    elif text_value is not None:
        command.extend(["--text", text_value])
    elif number_value is not None:
        command.extend(["--number", str(number_value)])
    elif date_value is not None:
        command.extend(["--date", date_value])
    elif single_select_option_id is not None:
        command.extend(["--single-select-option-id", single_select_option_id])
    elif iteration_id is not None:
        command.extend(["--iteration-id", iteration_id])

    # Execute the command
    return execute_gh_command(command)


@handle_result
def list_project_items(
    project_id: str,
    owner: str = None,
    limit: int = None,
) -> Dict[str, Any]:
    """List items in a GitHub project.

    Args:
    ----
        project_id: The ID of the project
        owner: The owner of the project (user or organization)
        limit: Maximum number of items to return

    Returns:
    -------
        Result containing either the list of items as JSON or Error

    """
    # Resolve parameters from config or runtime values
    resolved_owner = resolve_param("global", "owner", owner)
    resolved_limit = resolve_param("project", "item_list_limit", limit)

    # Build the command
    command = ["project", "item-list", project_id, "--format", "json"]

    # Enhanced owner validation
    if resolved_owner:
        command.extend(["--owner", resolved_owner])

    # Add limit if provided
    if resolved_limit is not None:
        if isinstance(resolved_limit, int) and resolved_limit > 0:
            command.extend(["--limit", str(resolved_limit)])
        else:
            print_stderr(
                "Warning: Invalid limit '{}'. Must be a positive integer. "
                "Using default.".format(resolved_limit)
            )

    # Execute the command
    return execute_gh_command(command)


@handle_result
def view_project(project_id: str, owner: str = None) -> Dict[str, Any]:
    """View details of a GitHub project.

    Args:
    ----
        project_id: The ID of the project to view
        owner: The owner of the project (user or organization)

    Returns:
    -------
        Result containing either the project details as JSON or Error

    """
    # Resolve parameters from config or runtime values
    resolved_owner = resolve_param("global", "owner", owner)

    # Build the command with proper order of arguments
    command = ["project", "view", project_id]

    # Format should be added before owner to match test expectations
    command.extend(["--format", "json"])

    if resolved_owner:
        command.extend(["--owner", resolved_owner])

    # Execute the command
    return execute_gh_command(command)


@handle_result
def create_project_item(
    project_id: str,
    title: str,
    body: str,
    owner: str = None,
) -> Dict[str, Any]:
    """Create a draft issue item in a project.

    Args:
    ----
        project_id: The ID of the project
        owner: The owner of the project (user or organization)
        title: The title of the draft issue
        body: The body content of the draft issue

    Returns:
    -------
        Result containing either the created item as JSON or Error

    """
    # Resolve parameters from config or runtime values
    resolved_owner = resolve_param("global", "owner", owner)

    if not resolved_owner:
        return Err(Error.required_param_missing(param="owner"))

    # Build the command
    command = ["project", "item-create", project_id, "--format", "json"]

    # Add owner
    command.extend(["--owner", resolved_owner])

    # Add title
    command.extend(["--title", title])

    # Add body if provided
    if body:
        command.extend(["--body", body])

    # Execute the command
    return execute_gh_command(command)


# --- Tool Registration ---
def init_tools(server: FastMCP):
    """Register project-related tools, resources, and prompts with the MCP server."""
    print_stderr("\n=== Registering Project Tools ===")  # pragma: no cover

    # Print the function names for logging
    print_stderr(
        f"Create project field function name: {create_project_field.__name__}"
    )  # pragma: no cover
    print_stderr(
        f"Delete project field function name: {delete_project_field.__name__}"
    )  # pragma: no cover
    print_stderr(
        f"List project fields function name: {list_project_fields.__name__}"
    )  # pragma: no cover
    print_stderr(
        f"Add project item function name: {add_project_item.__name__}"
    )  # pragma: no cover
    print_stderr(
        f"Archive project item function name: {archive_project_item.__name__}"
    )  # pragma: no cover
    print_stderr(
        f"Delete project item function name: {delete_project_item.__name__}"
    )  # pragma: no cover
    print_stderr(
        f"Edit project item function name: {edit_project_item.__name__}"
    )  # pragma: no cover
    print_stderr(
        f"List project items function name: {list_project_items.__name__}"
    )  # pragma: no cover
    print_stderr(
        f"View project function name: {view_project.__name__}"
    )  # pragma: no cover
    print_stderr(
        f"Create project item function name: {create_project_item.__name__}"
    )  # pragma: no cover

    # Register the tools
    server.tool()(create_project_field)
    server.tool()(delete_project_field)
    server.tool()(list_project_fields)
    server.tool()(add_project_item)
    server.tool()(archive_project_item)
    server.tool()(delete_project_item)
    server.tool()(edit_project_item)
    server.tool()(list_project_items)
    server.tool()(view_project)
    server.tool()(create_project_item)

    print_stderr("=== Project Tools Registered ===\n")  # pragma: no cover

    # Register resources
    print_stderr("\n=== Registering Project Resources ===")  # pragma: no cover

    # Register the item details resource
    server.resource("project-item://{project_id}/{item_id}")(item_details)
    print_stderr(
        "Registered resource: project-item://{project_id}/{item_id}"
    )  # pragma: no cover

    # Register the field options resource
    server.resource("field://{project_id}/{field_id}/options")(field_options)
    print_stderr(
        "Registered resource: field://{project_id}/{field_id}/options"
    )  # pragma: no cover

    # Register the project fields resource
    server.resource("project://{project_id}/fields")(project_fields)
    print_stderr(
        "Registered resource: project://{project_id}/fields"
    )  # pragma: no cover

    print_stderr("=== Project Resources Registered ===\n")  # pragma: no cover

    # Register prompts
    print_stderr("\n=== Registering Project Prompts ===")  # pragma: no cover

    # Register the status update prompt
    server.prompt()(update_status_prompt)
    print_stderr("Registered prompt: update_status_prompt")  # pragma: no cover

    # Register the due date prompt
    server.prompt()(set_due_date_prompt)
    print_stderr("Registered prompt: set_due_date_prompt")  # pragma: no cover

    # Register the priority change prompt
    server.prompt()(change_priority_prompt)
    print_stderr("Registered prompt: change_priority_prompt")  # pragma: no cover

    # Register the generic field value prompt
    server.prompt()(set_field_value_prompt)
    print_stderr("Registered prompt: set_field_value_prompt")  # pragma: no cover

    # Register the clear field prompt
    server.prompt()(clear_field_prompt)
    print_stderr("Registered prompt: clear_field_prompt")  # pragma: no cover

    # Register the bulk status update prompt
    server.prompt()(bulk_status_update_prompt)
    print_stderr("Registered prompt: bulk_status_update_prompt")  # pragma: no cover

    print_stderr("=== Project Prompts Registered ===\n")  # pragma: no cover


# -- RESOURCES --


def item_details(project_id: str, item_id: str) -> Dict[str, Any]:
    """Resource providing detailed information about a specific project item."""
    try:
        # Use our existing function to get all items
        resolved_owner = resolve_param("global", "owner", None)

        # Set a high limit to ensure we get all items
        command = ["project", "item-list", project_id, "--format", "json"]
        if resolved_owner:
            command.extend(["--owner", resolved_owner])
        command.extend(["--limit", "100"])  # Use a reasonable limit

        # Execute command to get all items
        all_items = execute_gh_command(command)

        # Filter to find our specific item
        target_item = None
        for item in all_items:
            if item.get("id") == item_id:
                target_item = item
                break

        if not target_item:
            return {
                "error": f"Item {item_id} not found in project {project_id}",
                "available_items": len(all_items),
            }

        # Get the item's field values
        field_values = target_item.get("fieldValues", [])

        # Format the response with enhanced context
        return {
            "item_id": item_id,
            "title": target_item.get("title", "Unknown"),
            "type": target_item.get("type", "Unknown"),
            "url": target_item.get("url", ""),
            "content": target_item.get("content", ""),
            "current_field_values": field_values,
            "last_updated": target_item.get("updatedAt", ""),
            "created_at": target_item.get("createdAt", ""),
            "is_archived": target_item.get("isArchived", False),
            "all_fields_count": len(field_values),
        }
    except Exception as e:
        return {
            "error": str(e),
            "item_id": item_id,
            "project_id": project_id,
            "available": False,
            "reason": "Failed to fetch item details",
        }


def field_options(project_id: str, field_id: str) -> Dict[str, Any]:
    """Resource providing available options for a single-select field."""
    try:
        resolved_owner = resolve_param("global", "owner", None)

        # Get all fields for the project
        command = ["project", "field-list", project_id, "--format", "json"]
        if resolved_owner:
            command.extend(["--owner", resolved_owner])
        command.extend(["--limit", "500"])  # High limit to get all fields

        all_fields = execute_gh_command(command)

        # Find the specific field
        target_field = None
        for field in all_fields:
            if field.get("id") == field_id:
                target_field = field
                break

        if not target_field:
            return {
                "error": f"Field {field_id} not found in project {project_id}",
                "available_fields": len(all_fields),
            }

        # Check if this is a single select field and extract options
        field_type = target_field.get("dataType", "")
        if field_type != "SINGLE_SELECT":
            return {
                "field_id": field_id,
                "field_name": target_field.get("name", ""),
                "field_type": field_type,
                "error": "This field is not a SINGLE_SELECT field and does not have options",
            }

        # Extract options
        options = target_field.get("options", [])

        return {
            "field_id": field_id,
            "field_name": target_field.get("name", ""),
            "field_type": field_type,
            "options": options,
            "option_count": len(options),
            "default_option": options[0] if options else None,
            "usage_tip": "Use the 'id' value from the options array for the single_select_option_id parameter",
        }
    except Exception as e:
        return {
            "error": str(e),
            "field_id": field_id,
            "project_id": project_id,
            "available": False,
            "reason": "Failed to fetch field options",
        }


def project_fields(project_id: str) -> Dict[str, Any]:
    """Resource providing information about all fields in a project."""
    try:
        resolved_owner = resolve_param("global", "owner", None)

        # Get all fields for the project
        command = ["project", "field-list", project_id, "--format", "json"]
        if resolved_owner:
            command.extend(["--owner", resolved_owner])
        command.extend(["--limit", "500"])  # High limit to get all fields

        all_fields = execute_gh_command(command)

        # Organize fields by type for easier access
        field_types = {}
        for field in all_fields:
            field_type = field.get("dataType", "UNKNOWN")
            if field_type not in field_types:
                field_types[field_type] = []
            field_types[field_type].append(field)

        # Create a field map for easy lookup
        field_map = {field.get("id"): field for field in all_fields}

        # Extract field names for easy reference
        field_names = {field.get("id"): field.get("name") for field in all_fields}

        return {
            "project_id": project_id,
            "fields": all_fields,
            "field_count": len(all_fields),
            "fields_by_type": field_types,
            "field_map": field_map,
            "field_names": field_names,
            # Add contextual recommendations
            "common_operations": {
                "status_update": "Use SINGLE_SELECT fields for status updates",
                "prioritization": "Use SINGLE_SELECT fields for priority or NUMBER fields for scoring",
                "scheduling": "Use DATE fields for planning and deadlines",
                "documentation": "Use TEXT fields for notes and context",
            },
        }
    except Exception as e:
        return {
            "error": str(e),
            "project_id": project_id,
            "available": False,
            "reason": "Failed to fetch project fields",
        }


# -- PROMPTS --


def update_status_prompt(item_id: str, project_id: str, new_status: str) -> str:
    """Prompt template for updating an item's status."""
    return (
        f"Update the status of item {item_id} in project {project_id} to '{new_status}'. "
        f"If this exact status doesn't exist, choose the closest matching option."
    )


def set_due_date_prompt(item_id: str, project_id: str, due_date: str) -> str:
    """Prompt template for setting a due date for an item."""
    return (
        f"Set the due date for item {item_id} in project {project_id} to {due_date}. "
        f"Please ensure this is a business day. If it falls on a weekend, "
        f"adjust to the following Monday."
    )


def change_priority_prompt(item_id: str, project_id: str, priority: str) -> str:
    """Prompt template for changing an item's priority."""
    return (
        f"Change the priority of item {item_id} in project {project_id} to {priority}. "
        f"Also, if this item has a due date coming up in less than a week, "
        f"make sure to notify the assignee about this priority change."
    )


def set_field_value_prompt(
    item_id: str, project_id: str, field_name: str, value: str
) -> str:
    """Prompt template for setting any field value by field name."""
    return (
        f"Set the '{field_name}' field for item {item_id} in project {project_id} to '{value}'. "
        f"This will identify the correct field ID and value format automatically."
    )


def clear_field_prompt(item_id: str, project_id: str, field_name: str) -> str:
    """Prompt template for clearing a field value."""
    return f"Clear the '{field_name}' field value for item {item_id} in project {project_id}."


def bulk_status_update_prompt(status_from: str, status_to: str, project_id: str) -> str:
    """Prompt template for bulk updating statuses across a project."""
    return (
        f"Find all items in project {project_id} with status '{status_from}' "
        f"and update them to '{status_to}'. This is part of our end-of-sprint cleanup."
    )
