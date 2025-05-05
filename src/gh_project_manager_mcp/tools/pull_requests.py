"""Implementations for GitHub pull request-related MCP tools."""

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
)
from gh_project_manager_mcp.utils.response_handler import handle_result

# --- Tool Implementation (with decorator) ---


@handle_result
def create_pull_request(
    base_branch: str,
    head: str,
    title: str,
    owner: str = None,
    repo: str = None,
    body: str = None,
    draft: bool = False,
    labels: List[str] = None,
    project_title: str = None,
    reviewers: List[str] = None,
    assignee: str = None,
) -> Dict[str, Any]:
    """Create a GitHub pull request.

    Args:
    ----
        base_branch: Base branch to create PR against
        head: Head branch containing changes
        title: Title of the pull request
        owner: Repository owner (username or organization)
        repo: Repository name
        body: Description of the pull request
        draft: Whether to create as a draft PR
        labels: Labels to add to the PR
        project_title: Project to add the PR to
        reviewers: Reviewers to request for the PR
        assignee: User to assign the PR to

    Returns:
    -------
        Result containing the command output on success or Error on failure

    """
    # Resolve parameters
    resolved_owner = resolve_param("global", "owner", owner)
    resolved_repo = resolve_param("global", "repo", repo)
    resolved_body = resolve_param("pull_request", "body", body)
    resolved_assignee = resolve_param("pull_request", "assignee", assignee)

    # Validate required parameters
    if not base_branch:
        return Err(Error.required_param_missing(param="base_branch"))

    if not head:
        return Err(Error.required_param_missing(param="head"))

    if not title:
        return Err(Error.required_param_missing(param="title"))

    if not resolved_owner:
        return Err(Error.required_param_missing(param="owner"))

    if not resolved_repo:
        return Err(Error.required_param_missing(param="repo"))

    # Create the base command
    command = [
        "pr",
        "create",
        "--repo",
        f"{resolved_owner}/{resolved_repo}",
        "--base",
        base_branch,
        "--head",
        head,
        "--title",
        title,
    ]

    # Add optional parameters if provided
    if resolved_body:
        command.extend(["--body", resolved_body])
    else:
        command.extend(["--body", "Created via GitHub MCP Server"])

    # Add draft flag if provided
    if draft:
        command.append("--draft")

    # Add labels if provided
    if labels:
        for label in labels:
            command.extend(["--label", label])

    # Add project if provided
    if project_title:
        command.extend(["--project", project_title])

    # Add assignee if provided
    if resolved_assignee:
        command.extend(["--assignee", resolved_assignee])

    # Add reviewers if provided
    if reviewers:
        for reviewer in reviewers:
            command.extend(["--reviewer", reviewer])

    # Execute the command
    return execute_gh_command(command)


@handle_result
def list_pull_requests(
    limit: int,
    owner: str = None,
    repo: str = None,
    state: str = None,
    labels: List[str] = None,
    assignee: str = None,
    author: str = None,
    base_branch: str = None,
    head: str = None,
) -> Dict[str, Any]:
    """List pull requests in a repository.

    Args:
    ----
        limit: Maximum number of PRs to return
        owner: Repository owner (username or organization)
        repo: Repository name
        state: Filter by state (open, closed, merged, all)
        labels: Filter by labels
        assignee: Filter by assignee
        author: Filter by PR author
        base_branch: Filter by base branch
        head: Filter by head branch

    Returns:
    -------
        Result containing the command output on success or Error on failure

    """
    # Resolve parameters
    resolved_owner = resolve_param("global", "owner", owner)
    resolved_repo = resolve_param("global", "repo", repo)

    # Validate required parameters
    if not resolved_owner:
        return Err(Error.required_param_missing(param="owner"))

    if not resolved_repo:
        return Err(Error.required_param_missing(param="repo"))

    # Build the command
    command = [
        "pr",
        "list",
        "--repo",
        f"{resolved_owner}/{resolved_repo}",
        "--limit",
        str(limit),
        "--json",
        "number,title,state,url,labels,assignees,author,baseRefName,headRefName",
    ]

    if state:
        command.extend(["--state", str(state)])
    if assignee:
        command.extend(["--assignee", str(assignee)])
    if author:
        command.extend(["--author", str(author)])
    if base_branch:
        command.extend(["--base", str(base_branch)])
    if head:
        command.extend(["--head", str(head)])
    if isinstance(labels, list) and labels:
        command.extend(["--label", ",".join(labels)])

    # Execute the command
    return execute_gh_command(command)


@handle_result
def checkout_pull_request(
    pr_identifier: str,
    owner: str = None,
    repo: str = None,
    checkout_branch_name: str = None,
    detach: bool = False,
    recurse_submodules: bool = False,
    force: bool = False,
) -> Dict[str, Any]:
    """Check out a pull request branch locally.

    Args:
    ----
        pr_identifier: Pull request number or URL
        owner: Repository owner (username or organization)
        repo: Repository name
        checkout_branch_name: Name for the local branch (default is PR head ref)
        detach: Checkout PR in detached HEAD state
        recurse_submodules: Update all submodules
        force: Force checkout even if there are local changes

    Returns:
    -------
        Result containing the command output on success or Error on failure

    """
    # Resolve parameters
    resolved_owner = resolve_param("global", "owner", owner)
    resolved_repo = resolve_param("global", "repo", repo)

    # Validate required parameters
    if not resolved_owner:
        return Err(Error.required_param_missing(param="owner"))

    if not resolved_repo:
        return Err(Error.required_param_missing(param="repo"))

    if not pr_identifier:
        return Err(Error.required_param_missing(param="pr_identifier"))

    # Build the command
    command = [
        "pr",
        "checkout",
        str(pr_identifier),
        "--repo",
        f"{resolved_owner}/{resolved_repo}",
    ]

    if checkout_branch_name:
        command.extend(["--branch", checkout_branch_name])
    if detach:
        command.append("--detach")
    if recurse_submodules:
        command.append("--recurse-submodules")
    if force:
        command.append("--force")

    # Execute the command
    return execute_gh_command(command)


@handle_result
def close_pull_request(
    pr_identifier: str,
    owner: str = None,
    repo: str = None,
    comment: str = None,
    delete_branch: bool = False,
) -> Dict[str, Any]:
    """Close a GitHub pull request.

    Args:
    ----
        pr_identifier: Pull request number or URL
        owner: Repository owner (username or organization)
        repo: Repository name
        comment: Comment to add when closing
        delete_branch: Whether to delete the head branch

    Returns:
    -------
        Result containing the command output on success or Error on failure

    """
    # Resolve parameters
    resolved_owner = resolve_param("global", "owner", owner)
    resolved_repo = resolve_param("global", "repo", repo)

    # Validate required parameters
    if not resolved_owner:
        return Err(Error.required_param_missing(param="owner"))

    if not resolved_repo:
        return Err(Error.required_param_missing(param="repo"))

    if not pr_identifier:
        return Err(Error.required_param_missing(param="pr_identifier"))

    # Build the command
    command = [
        "pr",
        "close",
        str(pr_identifier),
        "--repo",
        f"{resolved_owner}/{resolved_repo}",
    ]

    if comment:
        command.extend(["--comment", comment])
    if delete_branch:
        command.append("--delete-branch")

    # Execute the command
    return execute_gh_command(command)


@handle_result
def comment_pull_request(
    pr_identifier: str,
    owner: str = None,
    repo: str = None,
    body: str = None,
    body_file: str = None,
) -> Dict[str, Any]:
    """Add a comment to a pull request.

    Args:
    ----
        pr_identifier: Pull request number or URL
        owner: Repository owner (username or organization)
        repo: Repository name
        body: Text content of the comment
        body_file: Path to file containing comment text

    Returns:
    -------
        Result containing the command output on success or Error on failure

    """
    # Resolve parameters
    resolved_owner = resolve_param("global", "owner", owner)
    resolved_repo = resolve_param("global", "repo", repo)

    # Validate required parameters
    if not resolved_owner:
        return Err(Error.required_param_missing(param="owner"))

    if not resolved_repo:
        return Err(Error.required_param_missing(param="repo"))

    if not pr_identifier:
        return Err(Error.required_param_missing(param="pr_identifier"))

    # Validate that either body or body_file is provided, but not both
    if not body and not body_file:
        return Err(Error.required_params_missing(["body", "body_file"]))

    if body and body_file:
        return Err(Error.invalid_param("body and body_file", ["body", "body_file"]))

    # Build the command
    command = [
        "pr",
        "comment",
        str(pr_identifier),
        "--repo",
        f"{resolved_owner}/{resolved_repo}",
    ]

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
def diff_pull_request(
    owner: str = None,
    repo: str = None,
    pr_identifier: str = None,
    color: str = None,
    patch: bool = False,
    name_only: bool = False,
) -> Dict[str, Any]:
    """View the diff of a pull request.

    Args:
    ----
        owner: Repository owner (username or organization)
        repo: Repository name
        pr_identifier: Pull request number or URL (if None, uses current branch)
        color: Color output option (auto, always, never)
        patch: Format diff as a patch
        name_only: Show only names of changed files

    Returns:
    -------
        Result containing the command output on success or Error on failure

    """
    # Resolve parameters
    resolved_owner = resolve_param("global", "owner", owner)
    resolved_repo = resolve_param("global", "repo", repo)

    if not resolved_owner:
        return Err(Error.required_param_missing(param="owner"))

    if not resolved_repo:
        return Err(Error.required_param_missing(param="repo"))

    # Validate color parameter if provided
    valid_color_options = ["auto", "always", "never"]
    if color and color.lower() not in valid_color_options:
        return Err(
            Error.invalid_param(color, valid_color_options, "Invalid color option.")
        )

    # Build the command
    command = ["pr", "diff"]

    if pr_identifier is not None:
        command.append(str(pr_identifier))

    command.extend(["--repo", f"{resolved_owner}/{resolved_repo}"])

    if color:
        command.extend(["--color", color.lower()])
    if patch:
        command.append("--patch")
    if name_only:
        command.append("--name-only")

    # Execute the command
    return execute_gh_command(command)


@handle_result
def edit_pull_request(
    pr_identifier: str,
    owner: str = None,
    repo: str = None,
    title: str = None,
    body: str = None,
    base_branch: str = None,
    add_assignees: List[str] = None,
    remove_assignees: List[str] = None,
    add_reviewers: List[str] = None,
    remove_reviewers: List[str] = None,
    add_labels: List[str] = None,
    remove_labels: List[str] = None,
    add_projects: List[str] = None,
    remove_projects: List[str] = None,
    milestone: str = None,
) -> Dict[str, Any]:
    """Edit fields of a pull request.

    Args:
    ----
        pr_identifier: Pull request number or URL
        owner: Repository owner (username or organization)
        repo: Repository name
        title: New title for the PR
        body: New description for the PR
        base_branch: Change the base branch
        add_assignees: Add assignees
        remove_assignees: Remove assignees
        add_reviewers: Add reviewers
        remove_reviewers: Remove reviewers
        add_labels: Add labels
        remove_labels: Remove labels
        add_projects: Add to projects
        remove_projects: Remove from projects
        milestone: Set the milestone

    Returns:
    -------
        Result containing the command output on success or Error on failure

    """
    # Resolve parameters
    resolved_owner = resolve_param("global", "owner", owner)
    resolved_repo = resolve_param("global", "repo", repo)
    resolved_body = resolve_param("pull_request", "body", body)
    resolved_base = resolve_param("pull_request", "base", base_branch)

    # Validate required parameters
    if not resolved_owner:
        return Err(Error.required_param_missing(param="owner"))

    if not resolved_repo:
        return Err(Error.required_param_missing(param="repo"))

    if not pr_identifier:
        return Err(Error.required_param_missing(param="pr_identifier"))

    # Validate that at least one change parameter is provided
    has_changes = any(
        [
            title,
            resolved_body,
            resolved_base,
            add_assignees,
            remove_assignees,
            add_reviewers,
            remove_reviewers,
            add_labels,
            remove_labels,
            add_projects,
            remove_projects,
            milestone,
        ]
    )

    if not has_changes:
        return Err(
            Error(
                ErrorCode.REQUIRED_PARAM_MISSING,
                exception=Exception("At least one change parameter must be provided."),
                format_args={"param": "change parameter (title, body, etc.)"},
            )
        )

    # For assignees, if add_assignees is empty but we're making changes,
    # use the default assignee
    if not add_assignees and has_changes and not remove_assignees:
        default_assignee = resolve_param("pull_request", "assignee", None)
        if default_assignee:
            add_assignees = [default_assignee]

    # Build the command
    command = [
        "pr",
        "edit",
        str(pr_identifier),
        "--repo",
        f"{resolved_owner}/{resolved_repo}",
    ]

    # Add fields to command
    if title:
        command.extend(["--title", title])
    if resolved_body:
        command.extend(["--body", resolved_body])
    if resolved_base:
        command.extend(["--base", resolved_base])
    if milestone:
        command.extend(["--milestone", milestone])

    # Add assignees
    if add_assignees:
        for assignee in add_assignees:
            command.extend(["--add-assignee", assignee])
    if remove_assignees:
        for assignee in remove_assignees:
            command.extend(["--remove-assignee", assignee])

    # Add reviewers
    if add_reviewers:
        for reviewer in add_reviewers:
            command.extend(["--add-reviewer", reviewer])
    if remove_reviewers:
        for reviewer in remove_reviewers:
            command.extend(["--remove-reviewer", reviewer])

    # Add labels
    if add_labels:
        for label in add_labels:
            command.extend(["--add-label", label])
    if remove_labels:
        for label in remove_labels:
            command.extend(["--remove-label", label])

    # Add projects
    if add_projects:
        for project in add_projects:
            command.extend(["--add-project", project])
    if remove_projects:
        for project in remove_projects:
            command.extend(["--remove-project", project])

    # Execute the command
    return execute_gh_command(command)


@handle_result
def ready_pull_request(
    pr_identifier: str,
    owner: str = None,
    repo: str = None,
) -> Dict[str, Any]:
    """Mark a draft PR as ready for review.

    Args:
    ----
        pr_identifier: Pull request number or URL
        owner: Repository owner (username or organization)
        repo: Repository name

    Returns:
    -------
        Result containing the command output on success or Error on failure

    """
    # Resolve parameters
    resolved_owner = resolve_param("global", "owner", owner)
    resolved_repo = resolve_param("global", "repo", repo)

    # Validate required parameters
    if not resolved_owner:
        return Err(Error.required_param_missing(param="owner"))

    if not resolved_repo:
        return Err(Error.required_param_missing(param="repo"))

    if not pr_identifier:
        return Err(Error.required_param_missing(param="pr_identifier"))

    # Build the command
    command = [
        "pr",
        "ready",
        str(pr_identifier),
        "--repo",
        f"{resolved_owner}/{resolved_repo}",
    ]

    # Execute the command
    return execute_gh_command(command)


@handle_result
def reopen_pull_request(
    pr_identifier: str,
    owner: str = None,
    repo: str = None,
    comment: str = None,
) -> Dict[str, Any]:
    """Reopen a closed GitHub pull request.

    Args:
    ----
        pr_identifier: Pull request number or URL
        owner: Repository owner (username or organization)
        repo: Repository name
        comment: Comment to add when reopening

    Returns:
    -------
        Result containing the command output on success or Error on failure

    """
    # Resolve parameters
    resolved_owner = resolve_param("global", "owner", owner)
    resolved_repo = resolve_param("global", "repo", repo)

    # Validate required parameters
    if not resolved_owner:
        return Err(Error.required_param_missing(param="owner"))

    if not resolved_repo:
        return Err(Error.required_param_missing(param="repo"))

    if not pr_identifier:
        return Err(Error.required_param_missing(param="pr_identifier"))

    # Build the command
    command = [
        "pr",
        "reopen",
        str(pr_identifier),
        "--repo",
        f"{resolved_owner}/{resolved_repo}",
    ]

    if comment:
        command.extend(["--comment", comment])

    # Execute the command
    return execute_gh_command(command)


@handle_result
def review_pull_request(
    pr_identifier: str,
    action: str,  # approve, request_changes, comment
    owner: str = None,
    repo: str = None,
    body: str = None,
    body_file: str = None,
) -> Dict[str, Any]:
    """Submit a review on a GitHub pull request.

    Args:
    ----
        pr_identifier: Pull request number or URL
        action: Review action (approve, request_changes, comment)
        owner: Repository owner (username or organization)
        repo: Repository name
        body: Review comment text
        body_file: Path to file containing review text

    Returns:
    -------
        Result containing the command output on success or Error on failure

    """
    # Resolve parameters
    resolved_owner = resolve_param("global", "owner", owner)
    resolved_repo = resolve_param("global", "repo", repo)

    # Validate required parameters
    if not resolved_owner:
        return Err(Error.required_param_missing(param="owner"))

    if not resolved_repo:
        return Err(Error.required_param_missing(param="repo"))

    if not pr_identifier:
        return Err(Error.required_param_missing(param="pr_identifier"))

    if not action:
        return Err(Error.required_param_missing(param="action"))

    # Validate action parameter
    action_lower = action.lower()
    valid_actions = {
        "approve": "--approve",
        "comment": "--comment",
        "request_changes": "--request-changes",
    }

    if action_lower not in valid_actions:
        return Err(
            Error.invalid_param(action, list(valid_actions.keys()), "Invalid action.")
        )

    # Validate action-specific requirements
    if (body or body_file) and action_lower == "approve":
        return Err(
            Error(
                ErrorCode.INVALID_PARAM,
                exception=Exception(
                    "Review body/body_file cannot be used with 'approve' action."
                ),
                format_args={
                    "param": "body with approve action",
                    "valid_params": "No body allowed for approve",
                },
            )
        )

    if not (body or body_file) and action_lower == "comment":
        return Err(Error.required_params_missing(["body", "body_file"]))

    # Validate that body and body_file are not provided together
    if body and body_file:
        return Err(Error.invalid_param("body and body_file", ["body", "body_file"]))

    # Build the command
    command = [
        "pr",
        "review",
        str(pr_identifier),
        "--repo",
        f"{resolved_owner}/{resolved_repo}",
    ]

    command.append(valid_actions[action_lower])

    if body:
        command.extend(["--body", body])
    elif body_file:
        # Handle special stdin case
        if body_file == "-":
            return Err(
                Error(
                    ErrorCode.INVALID_PARAM,
                    exception=Exception(
                        "Reading review body from stdin ('-') is not "
                        "supported via this tool."
                    ),
                    format_args={"param": "body_file"},
                )
            )
        command.extend(["--body-file", body_file])

    # Execute the command
    return execute_gh_command(command)


@handle_result
def status_pull_request(random_string: str = "") -> Dict[str, Any]:
    """Get PR status relevant to the current user/branch.

    Args:
    ----
        random_string: Dummy parameter for no-parameter tools

    Returns:
    -------
        Result containing the command output on success or Error on failure

    """
    # Build the command
    command = [
        "pr",
        "status",
        "--json",
        "createdBy,mentioned,reviewRequested",
    ]

    # Execute the command
    return execute_gh_command(command)


@handle_result
def view_pull_request(
    pr_identifier: str,
    owner: str = None,
    repo: str = None,
    comments: bool = False,
) -> Dict[str, Any]:
    """View details of a GitHub pull request.

    Args:
    ----
        pr_identifier: Pull request number or URL
        owner: Repository owner (username or organization)
        repo: Repository name
        comments: Whether to include comments in the output

    Returns:
    -------
        Result containing the command output on success or Error on failure

    """
    # Resolve parameters
    resolved_owner = resolve_param("global", "owner", owner)
    resolved_repo = resolve_param("global", "repo", repo)

    # Validate required parameters
    if not resolved_owner:
        return Err(Error.required_param_missing(param="owner"))

    if not resolved_repo:
        return Err(Error.required_param_missing(param="repo"))

    if not pr_identifier:
        return Err(Error.required_param_missing(param="pr_identifier"))

    # Build the command
    command = [
        "pr",
        "view",
        str(pr_identifier),
        "--repo",
        f"{resolved_owner}/{resolved_repo}",
        "--json",
        (
            "number,title,state,url,body,createdAt,updatedAt,labels,"
            "assignees,author,baseRefName,headRefName,comments,reviews"
        ),
    ]

    # Add comments flag if requested
    if comments:
        command.append("--comments")

    # Execute the command
    return execute_gh_command(command)


@handle_result
def update_branch_pull_request(
    pr_identifier: str,
    owner: str = None,
    repo: str = None,
    rebase: bool = False,
) -> Dict[str, Any]:
    """Update a pull request branch with latest changes from the base branch.

    Args:
    ----
        pr_identifier: Pull request number or URL
        owner: Repository owner (username or organization)
        repo: Repository name
        rebase: Whether to rebase instead of merge

    Returns:
    -------
        Result containing the command output on success or Error on failure

    """
    # Resolve parameters
    resolved_owner = resolve_param("global", "owner", owner)
    resolved_repo = resolve_param("global", "repo", repo)

    # Validate required parameters
    if not resolved_owner:
        return Err(Error.required_param_missing(param="owner"))

    if not resolved_repo:
        return Err(Error.required_param_missing(param="repo"))

    if not pr_identifier:
        return Err(Error.required_param_missing(param="pr_identifier"))

    # Build the command
    command = ["pr", "update-branch"]

    # Add PR identifier
    command.append(str(pr_identifier))

    # Add repo information
    command.extend(["--repo", f"{resolved_owner}/{resolved_repo}"])

    # Add rebase flag if specified
    if rebase:
        command.append("--rebase")

    # Execute the command
    return execute_gh_command(command)


# --- Tool Registration ---
def init_tools(server: FastMCP):
    """Register pull request-related tools with the MCP server."""
    # server.tool()(create_pull_request)
    # server.tool()(list_pull_requests)
    # server.tool()(checkout_pull_request)
    # server.tool()(close_pull_request)
    # server.tool()(comment_pull_request)
    # server.tool()(diff_pull_request)
    # server.tool()(edit_pull_request)
    # server.tool()(ready_pull_request)
    # server.tool()(reopen_pull_request)
    # server.tool()(review_pull_request)
    # server.tool()(status_pull_request)
    # server.tool()(view_pull_request)
    # server.tool()(update_branch_pull_request)
