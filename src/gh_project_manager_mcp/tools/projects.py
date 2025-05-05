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
    """Register project-related tools with the MCP server."""
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
