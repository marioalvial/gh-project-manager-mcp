"""Implementations for GitHub issue-related MCP tools."""

from typing import Any, Dict, List, Union

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


@handle_result
def create_issue(
    title: str,
    owner: str = None,
    repo: str = None,
    body: str = None,
    assignee: str = None,
    labels: List[str] = None,
    project: str = None,
) -> Dict[str, Any]:
    """Create a GitHub issue.

    Args:
    ----
        title: Issue title
        owner: The repository owner (falls back to GH_REPO_OWNER env var)
        repo: The repository name (falls back to GH_REPO_NAME env var)
        body: Issue body (falls back to configured default)
        assignee: GitHub username to assign the issue to
        labels: List of labels to apply to the issue
        project: Project to add the issue to

    Returns:
    -------
        Result containing either Success or Error

    """
    # Resolve parameters from config or runtime values
    owner_val = resolve_param("global", "owner", owner)
    repo_val = resolve_param("global", "repo", repo).replace("_", "-")
    body_val = resolve_param("issue", "body", body)
    assignee_val = resolve_param("issue", "assignee", assignee)
    labels_val = resolve_param("issue", "labels", labels)
    project_val = resolve_param("issue", "project", project)

    # Validate required parameters
    if owner_val is None:
        error = Error.required_param_missing(param="owner")
        return Err(error)

    if repo_val is None:
        error = Error.required_param_missing(param="repo")
        return Err(error)

    # Build the command
    command = ["issue", "create"]

    # Add repo specification
    command.extend(["-R", f"{owner_val}/{repo_val}"])

    # Add title
    command.extend(["--title", title])

    # Add optional parameters
    if body_val:
        command.extend(["--body", body_val])

    if assignee_val:
        command.extend(["--assignee", assignee_val])

    if labels_val:
        if isinstance(labels_val, list):
            command.extend(["--label", ",".join(labels_val)])
        else:
            command.extend(["--label", labels_val])

    if project_val:
        command.extend(["--project", project_val])

    # Execute the command
    result = execute_gh_command(command)

    return result


@handle_result
def get_issue(
    issue_number: int,
    owner: str = None,
    repo: str = None,
) -> Dict[str, Any]:
    """Get details of a specific GitHub issue by number.

    Args:
    ----
        issue_number: The issue number to view
        owner: The repository owner (falls back to GH_REPO_OWNER env var)
        repo: The repository name (falls back to GH_REPO_NAME env var)

    Returns:
    -------
        Result containing either the issue details or Error

    """
    # Resolve parameters from config or runtime values
    owner_val = resolve_param("global", "owner", owner)
    repo_val = resolve_param("global", "repo", repo).replace("_", "-")

    # Validate required parameters
    if owner_val is None:
        return Err(Error.required_param_missing(param="owner"))

    if repo_val is None:
        return Err(Error.required_param_missing(param="repo"))

    # Build the command
    command = [
        "issue",
        "view",
        str(issue_number),
        "--json",
        "number,title,state,url,body,createdAt,updatedAt,labels,assignees,comments,author,closedAt",
    ]

    # Add repo specification
    command.extend(["--repo", f"{owner_val}/{repo_val}"])

    # Execute the command
    return execute_gh_command(command)


@handle_result
def list_issues(
    limit: int,
    owner: str = None,
    repo: str = None,
    state: str = None,
    assignee: str = None,
    creator: str = None,
    mentioned: str = None,
    labels: List[str] = None,
    milestone: str = None,
) -> Dict[str, Any]:
    """List GitHub issues with optional filtering.

    Args:
    ----
        limit: Maximum number of issues to return
        owner: The repository owner (falls back to GH_REPO_OWNER env var)
        repo: The repository name (falls back to GH_REPO_NAME env var)
        state: Issue state to filter by (open, closed, all)
        assignee: Filter by assignee username
        creator: Filter by creator username
        mentioned: Filter by mentioned username
        labels: List of labels to filter by
        milestone: Filter by milestone

    Returns:
    -------
        Result containing either the list of issues or Error

    """
    # Resolve parameters from config or runtime values
    owner_val = resolve_param("global", "owner", owner)
    repo_val = resolve_param("global", "repo", repo).replace("_", "-")

    # Validate required parameters
    if owner_val is None:
        return Err(Error.required_param_missing(param="owner"))

    if repo_val is None:
        return Err(Error.required_param_missing(param="repo"))

    # Build the command
    command = [
        "issue",
        "list",
        "--json",
        "number,title,state,url,createdAt,updatedAt,labels,assignees",
    ]

    # Add repo specification
    command.extend(["--repo", f"{owner_val}/{repo_val}"])

    # Add optional parameters
    if state:
        command.extend(["--state", state])
    if assignee:
        command.extend(["--assignee", assignee])
    if creator:
        command.extend(["--author", creator])
    if mentioned:
        command.extend(["--mention", mentioned])
    if milestone:
        command.extend(["--milestone", milestone])
    if labels:
        if isinstance(labels, list):
            for label in labels:
                command.extend(["--label", label])
        else:
            command.extend(["--label", labels])

    command.extend(["--limit", str(limit)])

    # Execute the command
    return execute_gh_command(command)


@handle_result
def close_issue(
    issue_identifier: str,
    owner: str = None,
    repo: str = None,
    comment: str = None,
    reason: str = None,
) -> Dict[str, Any]:
    """Close a GitHub issue.

    Args:
    ----
        issue_identifier: The issue number or URL to close
        owner: The repository owner (falls back to GH_REPO_OWNER env var)
        repo: The repository name (falls back to GH_REPO_NAME env var)
        comment: Optional comment to add while closing the issue
        reason: Reason for closing (completed, not planned, duplicate)

    Returns:
    -------
        Result containing either success information or Error

    """
    # Resolve parameters from config or runtime values
    owner_val = resolve_param("global", "owner", owner)
    repo_val = resolve_param("global", "repo", repo).replace("_", "-")

    # Validate required parameters
    if owner_val is None:
        return Err(Error.required_param_missing(param="owner"))

    if repo_val is None:
        return Err(Error.required_param_missing(param="repo"))

    # Build the command
    command = ["issue", "close", issue_identifier]

    # Add repo specification
    command.extend(["--repo", f"{owner_val}/{repo_val}"])

    # Add optional parameters
    if comment:
        command.extend(["--comment", comment])

    # Validate and add reason if provided
    if reason:
        valid_reasons = ["completed", "not planned", "duplicate"]
        if reason.lower() in valid_reasons:
            command.extend(["--reason", reason.lower()])
        else:
            return Err(Error.invalid_param(reason, valid_reasons))

    # Execute the command
    return execute_gh_command(command)


@handle_result
def comment_issue(
    issue_identifier: str,
    owner: str = None,
    repo: str = None,
    body: str = None,
    body_file: str = None,
) -> Dict[str, Any]:
    """Add a comment to a GitHub issue.

    Args:
    ----
        issue_identifier: The issue number or URL to comment on
        owner: The repository owner (falls back to GH_REPO_OWNER env var)
        repo: The repository name (falls back to GH_REPO_NAME env var)
        body: Text content of the comment
        body_file: Path to file containing comment text (mutually exclusive with body)

    Returns:
    -------
        Result containing either success information or Error

    """
    # Resolve parameters from config or runtime values
    owner_val = resolve_param("global", "owner", owner)
    repo_val = resolve_param("global", "repo", repo).replace("_", "-")

    # Validate required parameters
    if owner_val is None:
        return Err(Error.required_param_missing(param="owner"))

    if repo_val is None:
        return Err(Error.required_param_missing(param="repo"))

    # Validate that either body or body_file is provided, but not both
    if not body and not body_file:
        return Err(Error.required_params_missing(["body", "body_file"]))

    if body and body_file:
        return Err(Error.invalid_param("body and body_file", ["body", "body_file"]))

    # Build the command
    command = ["issue", "comment", issue_identifier]

    # Add repo specification
    command.extend(["--repo", f"{owner_val}/{repo_val}"])

    # Add either body or body_file to the command
    if body:
        command.extend(["--body", body])
    elif body_file:
        # Handle special stdin case
        if body_file == "-":
            return Err(
                Error(
                    ErrorCode.INVALID_PARAM,
                    exception=Exception(
                        "Reading comment body from stdin ('-') is not "
                        "supported via this tool."
                    ),
                    format_args={"param": "body_file"},
                )
            )
        command.extend(["--body-file", body_file])

    # Execute the command
    return execute_gh_command(command)


@handle_result
def delete_issue(
    issue_identifier: str,
    owner: str = None,
    repo: str = None,
    skip_confirmation: bool = False,
) -> Dict[str, Any]:
    """Delete a GitHub issue (requires admin rights).

    Args:
    ----
        issue_identifier: The issue number or URL to delete
        owner: The repository owner (falls back to GH_REPO_OWNER env var)
        repo: The repository name (falls back to GH_REPO_NAME env var)
        skip_confirmation: Whether to skip the confirmation prompt

    Returns:
    -------
        Result containing either success information or Error

    """
    # Resolve parameters from config or runtime values
    owner_val = resolve_param("global", "owner", owner)
    repo_val = resolve_param("global", "repo", repo).replace("_", "-")

    # Validate required parameters
    if owner_val is None:
        return Err(Error.required_param_missing(param="owner"))

    if repo_val is None:
        return Err(Error.required_param_missing(param="repo"))

    # Build the command
    command = ["issue", "delete", issue_identifier]

    # Add repo specification
    command.extend(["--repo", f"{owner_val}/{repo_val}"])

    # Add --yes flag to skip confirmation if requested
    if skip_confirmation:
        command.append("--yes")

    # Execute the command
    return execute_gh_command(command)


@handle_result
def edit_issue(
    issue_identifier: str,
    owner: str = None,
    repo: str = None,
    title: str = None,
    body: str = None,
    add_assignees: List[str] = None,
    remove_assignees: List[str] = None,
    add_labels: List[str] = None,
    remove_labels: List[str] = None,
    add_projects: List[str] = None,
    remove_projects: List[str] = None,
    milestone: Union[str, int] = None,
) -> Dict[str, Any]:
    """Edit issue metadata.

    Args:
    ----
        issue_identifier: The issue number or URL to edit
        owner: The repository owner (falls back to GH_REPO_OWNER env var)
        repo: The repository name (falls back to GH_REPO_NAME env var)
        title: New issue title
        body: New issue body
        add_assignees: List of assignees to add
        remove_assignees: List of assignees to remove
        add_labels: List of labels to add
        remove_labels: List of labels to remove
        add_projects: List of projects to add
        remove_projects: List of projects to remove
        milestone: Milestone to set (name or number)

    Returns:
    -------
        Result containing either success information or Error

    """
    # Resolve parameters from config or runtime values
    owner_val = resolve_param("global", "owner", owner)
    repo_val = resolve_param("global", "repo", repo).replace("_", "-")

    # Validate required parameters
    if owner_val is None:
        return Err(Error.required_param_missing(param="owner"))

    if repo_val is None:
        return Err(Error.required_param_missing(param="repo"))

    # Build the command
    command = ["issue", "edit", issue_identifier]

    # Add repo specification
    command.extend(["--repo", f"{owner_val}/{repo_val}"])

    # Add optional parameters
    if title:
        command.extend(["--title", title])

    if body:
        command.extend(["--body", body])

    if add_assignees:
        if isinstance(add_assignees, list):
            command.extend(["--add-assignee", ",".join(add_assignees)])
        else:
            command.extend(["--add-assignee", add_assignees])

    if remove_assignees:
        if isinstance(remove_assignees, list):
            command.extend(["--remove-assignee", ",".join(remove_assignees)])
        else:
            command.extend(["--remove-assignee", remove_assignees])

    if add_labels:
        if isinstance(add_labels, list):
            command.extend(["--add-label", ",".join(add_labels)])
        else:
            command.extend(["--add-label", add_labels])

    if remove_labels:
        if isinstance(remove_labels, list):
            command.extend(["--remove-label", ",".join(remove_labels)])
        else:
            command.extend(["--remove-label", remove_labels])

    if add_projects:
        if isinstance(add_projects, list):
            command.extend(["--add-project", ",".join(add_projects)])
        else:
            command.extend(["--add-project", add_projects])

    if remove_projects:
        if isinstance(remove_projects, list):
            command.extend(["--remove-project", ",".join(remove_projects)])
        else:
            command.extend(["--remove-project", remove_projects])

    if milestone:
        command.extend(["--milestone", str(milestone)])

    # Execute the command
    return execute_gh_command(command)


@handle_result
def reopen_issue(
    issue_identifier: str,
    owner: str = None,
    repo: str = None,
    comment: str = None,
) -> Dict[str, Any]:
    """Reopen a closed issue.

    Args:
    ----
        issue_identifier: The issue number or URL to reopen
        owner: The repository owner (falls back to GH_REPO_OWNER env var)
        repo: The repository name (falls back to GH_REPO_NAME env var)
        comment: Optional comment to add when reopening the issue

    Returns:
    -------
        Result containing either success information or Error

    """
    # Resolve parameters from config or runtime values
    owner_val = resolve_param("global", "owner", owner)
    repo_val = resolve_param("global", "repo", repo).replace("_", "-")

    # Validate required parameters
    if owner_val is None:
        return Err(Error.required_param_missing(param="owner"))

    if repo_val is None:
        return Err(Error.required_param_missing(param="repo"))

    # Build the command
    command = ["issue", "reopen", issue_identifier]

    # Add repo specification
    command.extend(["--repo", f"{owner_val}/{repo_val}"])

    # Add optional comment
    if comment:
        command.extend(["--comment", comment])

    # Execute the command
    return execute_gh_command(command)


# --- Tool Registration ---


def init_tools(server: FastMCP):
    """Register issue-related tools with the MCP server."""
    print_stderr("\n=== Registering Issue Tools ===")  # pragma: no cover

    # Print the function names for logging
    print_stderr(
        f"Create issue function name: {create_issue.__name__}"
    )  # pragma: no cover
    print_stderr(f"Get issue function name: {get_issue.__name__}")  # pragma: no cover
    print_stderr(
        f"List issues function name: {list_issues.__name__}"
    )  # pragma: no cover
    print_stderr(
        f"Delete issue function name: {delete_issue.__name__}"
    )  # pragma: no cover
    print_stderr(f"Edit issue function name: {edit_issue.__name__}")  # pragma: no cover
    print_stderr(
        f"Reopen issue function name: {reopen_issue.__name__}"
    )  # pragma: no cover

    # Register the tools
    server.tool()(create_issue)  # Register the new implementation
    server.tool()(get_issue)  # Register the new implementation
    server.tool()(list_issues)  # Register the new implementation
    server.tool()(close_issue)  # Register the new implementation
    server.tool()(comment_issue)  # Register the new implementation
    server.tool()(delete_issue)  # Register the new implementation
    server.tool()(edit_issue)  # Register the new implementation
    server.tool()(reopen_issue)  # Register the new implementation

    print_stderr("=== Issue Tools Registered ===\n")  # pragma: no cover
