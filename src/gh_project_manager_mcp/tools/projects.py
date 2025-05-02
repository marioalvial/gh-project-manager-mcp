# src/gh_project_manager_mcp/tools/projects.py
# \"\"\"Implementations for GitHub project-related MCP tools.\"\"\"

import datetime
import sys  # Import sys for stderr
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from gh_project_manager_mcp.utils.gh_utils import resolve_param, run_gh_command

# """Implementations for GitHub project-related MCP tools."""

# --- Tool Implementation (without decorator) ---


def _copy_github_project_impl(
    project_id: Union[int, str],  # Project number or URL
    target_owner: str,  # The owner (user or org) to copy the project to
    new_title: Optional[str] = None,  # Optional new title for the copied project
    source_owner: Optional[
        str
    ] = None,  # Optional owner of source project (if not inherent in project_id URL)
) -> Dict[str, Any]:
    """Copy a GitHub project.

    Uses `gh project copy`.
    """
    command = [
        "project",
        "copy",
        str(project_id),
        "--to",
        target_owner,
        "--format",
        "json",  # Request JSON output for easier parsing
    ]
    resolved_source_owner = resolve_param("project", "copy_source_owner", source_owner)
    if resolved_source_owner:
        command.extend(["--source-owner", resolved_source_owner])
    if new_title:
        command.extend(["--title", new_title])
    result = run_gh_command(command)
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, dict):
        return result
    else:
        return {"error": "Unexpected result from gh project copy", "raw": result}


def _create_github_project_impl(
    owner: str,  # The owner (user or org) for the new project
    title: str,  # The title for the new project
) -> Dict[str, Any]:
    """Create a new GitHub project.

    Uses `gh project create`.
    """
    command = [
        "project",
        "create",
        "--owner",
        owner,
        "--title",
        title,
        "--format",
        "json",  # Explicitly request JSON
    ]
    result = run_gh_command(command)
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, dict):
        return result
    else:
        return {"error": "Unexpected result from gh project create", "raw": result}


def _delete_github_project_impl(
    project_id: Union[int, str],  # Project number or URL to delete
    owner: Optional[
        str
    ] = None,  # Optional owner (user or org) if not in project_id URL
) -> Dict[str, Any]:
    """Delete a GitHub project.

    Uses `gh project delete`.
    """
    command = ["project", "delete", str(project_id)]
    resolved_owner = resolve_param("project", "delete_owner", owner)
    if resolved_owner:
        command.extend(["--owner", resolved_owner])
    result = run_gh_command(command)
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str):
        return {"status": "success", "message": result.strip()}
    else:
        return {"status": "success", "message": "Project deleted successfully."}


def _edit_github_project_impl(
    project_id: Union[int, str],  # Project number or URL to edit
    owner: Optional[str] = None,  # Optional owner (user or org)
    title: Optional[str] = None,
    description: Optional[str] = None,
    visibility: Optional[str] = None,  # 'public' or 'private'
    readme: Optional[str] = None,
) -> Dict[str, Any]:
    """Edit a GitHub project.

    Uses `gh project edit`.
    """
    command = ["project", "edit", str(project_id), "--format", "json"]
    resolved_owner = resolve_param("project", "edit_owner", owner)
    if resolved_owner:
        command.extend(["--owner", resolved_owner])
    if title is not None:
        command.extend(["--title", title])
    if description is not None:
        command.extend(["--description", description])
    if readme is not None:
        command.extend(["--readme", readme])
    if visibility is not None:
        vis_lower = visibility.lower()
        if vis_lower in ["public", "private"]:
            command.extend(["--visibility", vis_lower])
        else:
            return {
                "error": f"Invalid visibility '{visibility}'. Must be 'public' or 'private'."
            }
    if title is None and description is None and visibility is None and readme is None:
        return {
            "error": "No edit options provided. Specify at least one of: title, description, visibility, readme."
        }
    result = run_gh_command(command)
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, dict):
        return result
    else:
        return {"error": "Unexpected result from gh project edit", "raw": result}


def _create_github_project_field_impl(
    project_id: Union[int, str],
    name: str,
    owner: Optional[str] = None,
    data_type: str = "TEXT",  # Default to TEXT
    single_select_options: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a new field in a GitHub project.

    Uses `gh project field-create`.
    """
    data_type_upper = data_type.upper()
    valid_data_types = ["TEXT", "NUMBER", "DATE", "SINGLE_SELECT", "ITERATION"]
    if data_type_upper not in valid_data_types:
        return {
            "error": f"Invalid data_type '{data_type}'. Must be one of: {valid_data_types}"
        }
    if data_type_upper == "SINGLE_SELECT" and not single_select_options:
        return {
            "error": "single_select_options are required when data_type is SINGLE_SELECT."
        }
    if data_type_upper != "SINGLE_SELECT" and single_select_options:
        print(
            f"Warning: single_select_options provided but data_type is '{data_type_upper}'. Options will be ignored.",
            file=sys.stderr,
        )
    command = [
        "project",
        "field-create",
        str(project_id),
        "--name",
        name,
        "--data-type",
        data_type_upper,
        "--format",
        "json",
    ]
    resolved_owner = resolve_param("project", "field_owner", owner)
    if resolved_owner:
        command.extend(["--owner", resolved_owner])
    if data_type_upper == "SINGLE_SELECT" and single_select_options:
        options_str = ",".join(map(str, single_select_options))
        command.extend(["--single-select-options", options_str])
    result = run_gh_command(command)
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, dict):
        return result
    else:
        return {
            "error": "Unexpected result from gh project field-create",
            "raw": result,
        }


def _delete_github_project_field_impl(
    field_id: str,  # The ID of the field to delete
    project_id: Optional[Union[int, str]] = None,
) -> Dict[str, Any]:
    """Delete a field from a GitHub project.

    Uses `gh project field-delete`.
    """
    command = ["project", "field-delete", field_id]
    if project_id is not None:
        print(
            f"""Warning: project_id '{project_id}' provided but not used \
by gh project field-delete.""",
            file=sys.stderr,
        )
        pass
    result = run_gh_command(command)
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str):
        return {"status": "success", "message": result.strip()}
    else:
        return {"status": "success", "message": "Field deleted successfully."}


def _list_github_project_fields_impl(
    project_id: Union[int, str],
    owner: Optional[str] = None,
    limit: Optional[int] = None,
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """Implement the logic for listing fields in a GitHub project.

    Uses `gh project field-list`.
    """
    command = ["project", "field-list", str(project_id), "--format", "json"]
    resolved_owner = resolve_param("project", "field_list_owner", owner)
    resolved_limit = resolve_param(
        "project", "field_list_limit", limit, type_hint="int"
    )
    if resolved_owner:
        command.extend(["--owner", resolved_owner])
    if resolved_limit is not None:
        if isinstance(resolved_limit, int) and resolved_limit > 0:
            command.extend(["--limit", str(resolved_limit)])
        else:
            print(
                f"""Warning: Invalid limit '{resolved_limit}'. \
Must be a positive integer. Using default.""",
                file=sys.stderr,
            )
    result = run_gh_command(command)
    if isinstance(result, dict) and "error" in result:
        return [result]
    elif isinstance(result, list):
        return result
    elif (
        isinstance(result, dict)
        and "fields" in result
        and isinstance(result["fields"], list)
    ):
        return result["fields"]
    else:
        return [
            {"error": "Unexpected result from gh project field-list", "raw": result}
        ]


def _add_github_project_item_impl(
    project_id: Union[int, str],
    owner: Optional[str] = None,
    issue_id: Optional[str] = None,
    pull_request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Implement the logic for adding an item (issue or PR) to a GitHub project.

    Uses `gh project item-add`.
    """
    if (issue_id is None and pull_request_id is None) or (
        issue_id is not None and pull_request_id is not None
    ):
        return {"error": "Exactly one of issue_id or pull_request_id must be provided."}
    command = ["project", "item-add", str(project_id), "--format", "json"]
    resolved_owner = resolve_param("project", "item_add_owner", owner)
    if resolved_owner:
        command.extend(["--owner", resolved_owner])
    if issue_id:
        command.extend(["--issue-id", issue_id])
    elif pull_request_id:
        command.extend(["--pull-request-id", pull_request_id])
    result = run_gh_command(command)
    if isinstance(result, dict) and "error" in result:
        return result
    elif (
        isinstance(result, dict)
        and "items" in result
        and isinstance(result["items"], list)
        and len(result["items"]) > 0
    ):
        return result["items"][0]
    elif isinstance(result, dict):
        return result
    else:
        return {"error": "Unexpected result from gh project item-add", "raw": result}


def _archive_github_project_item_impl(
    item_id: str,  # The ID of the item to archive/unarchive
    project_id: Optional[Union[int, str]] = None,
    owner: Optional[str] = None,
    undo: bool = False,  # Flag to unarchive instead
) -> Dict[str, Any]:
    """Implement the logic for archiving or unarchiving a project item.

    Uses `gh project item-archive`.
    """
    command = ["project", "item-archive", item_id, "--format", "json"]
    resolved_owner = resolve_param("project", "item_archive_owner", owner)
    resolved_project_id = resolve_param(
        "project", "item_archive_project_id", project_id
    )
    if resolved_owner:
        command.extend(["--owner", resolved_owner])
    if resolved_project_id:
        command.extend(["--project-id", str(resolved_project_id)])
    if undo:
        command.append("--undo")
    result = run_gh_command(command)
    if isinstance(result, dict) and "error" in result:
        return result
    elif (
        isinstance(result, dict)
        and "item" in result
        and isinstance(result["item"], dict)
    ):
        return result["item"]
    elif isinstance(result, dict):
        return result
    else:
        return {
            "error": "Unexpected result from gh project item-archive",
            "raw": result,
        }


def _delete_github_project_item_impl(
    item_id: str,  # The ID of the item to delete
    project_id: Optional[Union[int, str]] = None,
    owner: Optional[str] = None,
) -> Dict[str, Any]:
    """Implement the logic for deleting an item from a GitHub project.

    Uses `gh project item-delete`.
    """
    command = ["project", "item-delete", item_id, "--format", "json"]
    resolved_owner = resolve_param("project", "item_delete_owner", owner)
    resolved_project_id = resolve_param("project", "item_delete_project_id", project_id)
    if resolved_owner:
        command.extend(["--owner", resolved_owner])
    if resolved_project_id:
        command.extend(["--project-id", str(resolved_project_id)])
    result = run_gh_command(command)
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, dict) and "id" in result:
        return {"status": "success", "deleted_item_id": result["id"]}
    elif isinstance(result, dict):
        return {**{"status": "success"}, **result}
    else:
        return {"error": "Unexpected result from gh project item-delete", "raw": result}


def _edit_github_project_item_impl(
    item_id: str,  # The ID of the item to edit
    project_id: Optional[Union[int, str]] = None,
    owner: Optional[str] = None,
    field_id: Optional[str] = None,  # ID of the field to set/clear
    clear: bool = False,  # Flag to clear the specified field
    # Value parameters (mutually exclusive with each other and --clear)
    text_value: Optional[str] = None,
    number_value: Optional[float] = None,  # float to handle decimals
    date_value: Optional[str] = None,  # Expect YYYY-MM-DD format
    single_select_option_id: Optional[str] = None,
    iteration_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Implement the logic for editing fields of a project item.

    Uses `gh project item-edit`.
    """
    # Validation
    if field_id is None and not clear:
        return {"error": "field_id is required to edit an item field."}
    if clear and field_id is None:
        return {"error": "field_id is required when using --clear."}

    value_params = [
        text_value,
        number_value,
        date_value,
        single_select_option_id,
        iteration_id,
    ]
    provided_value_params = [p for p in value_params if p is not None]

    if clear and len(provided_value_params) > 0:
        return {
            "error": ("Cannot provide a value parameter (--text, --number, etc.) "
                      "when using --clear.")
        }
    if not clear and len(provided_value_params) == 0:
        return {
            "error": ("Exactly one value parameter (--text, --number, --date, "
                      "--single-select-option-id, or --iteration-id) is required "
                      "unless using --clear.")
        }
    if not clear and len(provided_value_params) > 1:
        return {
            "error": ("Only one value parameter (--text, --number, --date, "
                      "--single-select-option-id, or --iteration-id) can be "
                      "provided at a time.")
        }

    # Date validation
    if date_value is not None:
        try:
            datetime.date.fromisoformat(date_value)  # Validate YYYY-MM-DD
        except ValueError:
            return {
                "error": f"Invalid date_value '{date_value}'. Expected YYYY-MM-DD format."
            }

    command = ["project", "item-edit", item_id, "--format", "json"]

    resolved_owner = resolve_param("project", "item_edit_owner", owner)
    resolved_project_id = resolve_param("project", "item_edit_project_id", project_id)

    if resolved_owner:
        command.extend(["--owner", resolved_owner])
    if resolved_project_id:
        command.extend(["--project-id", str(resolved_project_id)])

    # Add field ID and action (clear or set value)
    if field_id:
        command.extend(["--field-id", field_id])  # Correctly indented

    if clear:
        command.append("--clear")
    else:
        # Add the single provided value parameter
        if text_value is not None:
            command.extend(["--text", text_value])
        elif number_value is not None:
            command.extend(["--number", str(number_value)])
        elif date_value is not None:
            command.extend(["--date", date_value])
        elif single_select_option_id is not None:
            command.extend(["--single-select-option-id", single_select_option_id])
        elif iteration_id is not None:
            command.extend(["--iteration-id", iteration_id])

    # Execute - Expect JSON output of the updated item
    result = run_gh_command(command)

    # Standardized result handling
    if isinstance(result, dict) and "error" in result:
        return result
    elif (
        isinstance(result, dict)
        and "item" in result
        and isinstance(result["item"], dict)
    ):
        return result["item"]
    elif isinstance(result, dict):
        return result
    else:
        return {"error": "Unexpected result from gh project item-edit", "raw": result}


# --- ADDING list_items HERE ---
def _list_github_project_items_impl(
    project_id: Union[int, str],
    owner: Optional[str] = None,
    limit: Optional[int] = None,
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """List items in a GitHub project.

    Uses `gh project item-list`.
    """
    command = ["project", "item-list", str(project_id), "--format", "json"]
    resolved_owner = resolve_param("project", "item_list_owner", owner)
    resolved_limit = resolve_param("project", "item_list_limit", limit, type_hint="int")
    if resolved_owner:
        command.extend(["--owner", resolved_owner])
    if resolved_limit is not None:
        if isinstance(resolved_limit, int) and resolved_limit > 0:
            command.extend(["--limit", str(resolved_limit)])
        else:
            print(
                f"""Warning: Invalid limit '{resolved_limit}'. \
Must be a positive integer. Using default.""",
                file=sys.stderr,
            )
    result = run_gh_command(command)
    if isinstance(result, dict) and "error" in result:
        return [result]
    elif isinstance(result, list):
        return result
    elif (
        isinstance(result, dict)
        and "items" in result
        and isinstance(result["items"], list)
    ):
        return result["items"]
    else:
        return [{"error": "Unexpected result from gh project item-list", "raw": result}]


def _list_github_projects_impl(
    owner: Optional[str] = None,
    limit: Optional[int] = None,
    closed: bool = False,  # Flag to include closed projects
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:  # Expecting a list of project objects
    """Implement the logic for listing GitHub projects for an owner.

    Uses `gh project list`.
    """
    command = ["project", "list", "--format", "json"]

    resolved_owner = resolve_param("project", "list_owner", owner)
    resolved_limit = resolve_param("project", "list_limit", limit, type_hint="int")
    # TODO: Add config entries if needed

    if resolved_owner:
        command.extend(["--owner", resolved_owner])
    else:
        # Owner is technically optional, defaults to @me, but explicit is safer for tools
        return [{"error": "Owner parameter is required for listing projects."}]

    if closed:
        command.append("--closed")

    # Add limit if specified and valid
    if resolved_limit is not None:
        if isinstance(resolved_limit, int) and resolved_limit > 0:
            command.extend(["--limit", str(resolved_limit)])
        else:
            print(
                f"""Warning: Invalid limit '{resolved_limit}'. \
Must be a positive integer. Using default.""",
                file=sys.stderr,
            )
    # gh default limit is 30 if not specified

    # Execute - Expect JSON list output
    result = run_gh_command(command)

    # Standardized result handling
    if isinstance(result, dict) and "error" in result:
        return [result]
    elif isinstance(result, list):
        return result  # Successful JSON list
    elif (
        isinstance(result, dict)
        and "projects" in result
        and isinstance(result["projects"], list)
    ):
        # Handle potential older gh versions wrapping output
        return result["projects"]
    else:
        return [{"error": "Unexpected result from gh project list", "raw": result}]


# --- END list_items ---


def _view_github_project_impl(
    project_id: Union[int, str],
    owner: Optional[str] = None,
    web: bool = False,  # Flag to open in browser (not directly useful for tool, but passed)
) -> Dict[str, Any]:
    """Implement the logic for viewing details of a GitHub project.

    Uses `gh project view`.
    """
    command = [
        "project",
        "view",
        str(project_id),
        "--format",
        "json",  # Request JSON for structured data
    ]

    resolved_owner = resolve_param("project", "view_owner", owner)
    # TODO: Add config entries if needed

    if resolved_owner:
        command.extend(["--owner", resolved_owner])

    if web:
        # The --web flag opens the browser, which isn't useful here.
        # We can execute the command without it to get JSON,
        # but maybe return the URL if web=True was requested?
        # For now, just ignore the --web flag for the command execution
        # but acknowledge it was passed.
        print(
            "Warning: --web flag provided but ignored; returning JSON data instead.",
            file=sys.stderr,
        )
        # Alternatively, could return an error or just the URL.

    # Execute - Expect JSON output
    result = run_gh_command(command)

    # Standardized result handling
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, dict):
        if web and "url" in result:
            # If web was requested, maybe return a specific dict with just the URL?
            return {
                "status": "success",
                "message": "Project URL retrieved",
                "url": result["url"],
            }
        return result  # Otherwise return full JSON
    else:
        return {"error": "Unexpected result from gh project view", "raw": result}


# --- Tool Registration ---
def init_tools(server: FastMCP):
    """Register project-related tools with the MCP server."""
    server.tool()(_copy_github_project_impl)
    server.tool()(_create_github_project_impl)
    server.tool()(_delete_github_project_impl)
    server.tool()(_edit_github_project_impl)
    server.tool()(_create_github_project_field_impl)
    server.tool()(_delete_github_project_field_impl)
    server.tool()(_list_github_project_fields_impl)
    server.tool()(_add_github_project_item_impl)
    server.tool()(_archive_github_project_item_impl)
    server.tool()(_delete_github_project_item_impl)
    server.tool()(_edit_github_project_item_impl)
    server.tool()(_list_github_project_items_impl)  # Register the list items function
    server.tool()(_list_github_projects_impl)  # Add new registration
    server.tool()(_view_github_project_impl)  # Add new registration
    # Add future registrations here
