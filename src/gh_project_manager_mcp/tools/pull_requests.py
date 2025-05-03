"""Implementations for GitHub pull request-related MCP tools."""

import sys  # Import sys for stderr
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from gh_project_manager_mcp.utils.gh_utils import resolve_param, run_gh_command

# --- Tool Implementation (without decorator) ---


def _create_pull_request_impl(
    owner: str,
    repo: str,
    base: str,
    head: str,
    title: str,
    body: Optional[str] = None,
    draft: Optional[bool] = None,
    reviewers: Optional[List[str]] = None,
    pr_labels: Optional[List[str]] = None,
    pr_project: Optional[str] = None,
) -> Dict[str, Any]:
    """Implement the logic for creating a GitHub pull request.

    Uses `gh pr create`.
    """
    # Parse optional parameters through resolve_param utility
    body_resolved = resolve_param("pull_request", "body", body)
    draft_resolved = resolve_param("pull_request", "draft", draft)
    reviewers_resolved = resolve_param("pull_request", "reviewers", reviewers)
    labels_resolved = resolve_param(
        "pull_request", "pr_labels", pr_labels
    )  # pragma: no cover

    # Start building the command with required parameters
    command = [
        "pr",
        "create",
        "--repo",
        f"{owner}/{repo}",
        "--base",
        base,
        "--head",
        head,
        "--title",
        title,
        "--body",
        body_resolved or "",  # Empty string if body is None/empty
        "--json",
        "url,number,title,body,state",  # Request structured JSON output
    ]

    # Add optional parameters if they were provided
    if draft_resolved:  # pragma: no cover
        command.append("--draft")

    # Add reviewers if provided
    if reviewers_resolved:  # pragma: no cover
        for reviewer in reviewers_resolved:
            command.extend(["--reviewer", reviewer])

    # Add labels if provided
    if labels_resolved:  # pragma: no cover
        for label in labels_resolved:
            command.extend(["--label", label])

    # Execute the command
    result = run_gh_command(command)

    # Handle the result
    if isinstance(result, dict) and "error" in result:
        return result  # Return error dictionary directly
    elif isinstance(result, dict) and "url" in result:
        return result  # Return successful JSON response
    elif isinstance(result, str):  # pragma: no cover
        # This should be rare if --json is used correctly
        return {
            "error": "Unexpected string result from gh pr create",
            "raw": result,
        }
    else:  # pragma: no cover
        # This can occur if gh returns something unexpected
        return {
            "error": "Unexpected result type from gh pr create",
        }


def _list_github_pull_requests_impl(
    owner: str,
    repo: str,
    state: Optional[str] = None,
    limit: Optional[int] = None,
    labels: Optional[List[str]] = None,
    assignee: Optional[str] = None,
    author: Optional[str] = None,
    base: Optional[str] = None,
    head: Optional[str] = None,
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """List pull requests in a repository.

    Uses `gh pr list`.
    """
    state_resolved = resolve_param("pull_request", "list_state", state)
    limit_resolved = resolve_param("pull_request", "list_limit", limit)
    labels_resolved = resolve_param("pull_request", "list_labels", labels)
    assignee_resolved = resolve_param("pull_request", "assignee", assignee)
    author_resolved = resolve_param("pull_request", "author", author)
    base_resolved = resolve_param("pull_request", "base", base)
    head_resolved = resolve_param("pull_request", "head", head)

    command = [
        "pr",
        "list",
        "--repo",
        f"{owner}/{repo}",
        "--limit",
        str(limit_resolved if limit_resolved is not None else 30),
        "--json",
        ("number,title,state,url,labels,assignees,author," "baseRefName,headRefName"),
    ]
    if state_resolved:  # pragma: no cover
        command.extend(["--state", str(state_resolved)])
    if assignee_resolved:  # pragma: no cover
        command.extend(["--assignee", str(assignee_resolved)])
    if author_resolved:  # pragma: no cover
        command.extend(["--author", str(author_resolved)])
    if base_resolved:  # pragma: no cover
        command.extend(["--base", str(base_resolved)])
    if head_resolved:  # pragma: no cover
        command.extend(["--head", str(head_resolved)])
    if isinstance(labels_resolved, list) and labels_resolved:  # pragma: no cover
        command.extend(["--label", ",".join(labels_resolved)])

    result = run_gh_command(command)

    if isinstance(result, dict) and "error" in result:  # pragma: no cover
        return [result]
    elif isinstance(result, list):
        return result
    elif isinstance(result, str):  # pragma: no cover
        print(f"Warning: gh pr list returned string: {result}", file=sys.stderr)
        return [
            {
                "error": (
                    "Expected list result from gh pr list but got "
                    "different JSON type"
                ),
                "raw": result,
            }
        ]
    else:  # pragma: no cover
        print(f"Error decoding JSON from gh pr list: {result}", file=sys.stderr)
        return [
            {"error": "Failed to decode JSON response from gh pr list", "raw": result}
        ]


def _checkout_github_pull_request_impl(
    owner: str,
    repo: str,
    pr_identifier: Union[int, str],
    checkout_branch_name: Optional[str] = None,
    detach: bool = False,
    recurse_submodules: bool = False,
    force: bool = False,
) -> Dict[str, Any]:
    """Implement the logic for checking out a pull request branch locally.

    Uses `gh pr checkout`.
    """
    command = ["pr", "checkout", str(pr_identifier), "--repo", f"{owner}/{repo}"]
    if checkout_branch_name:
        command.extend(["--branch", checkout_branch_name])
    if detach:
        command.append("--detach")
    if recurse_submodules:
        command.append("--recurse-submodules")
    if force:
        command.append("--force")
    result = run_gh_command(command)
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str):
        return {"status": "success", "message": result.strip()}
    else:
        return {"status": "success", "message": "Checkout successful"}


def _close_github_pull_request_impl(
    owner: str,
    repo: str,
    pr_identifier: Union[int, str],
    comment: Optional[str] = None,
    delete_branch: bool = False,
) -> Dict[str, Any]:
    """Implement the logic for closing a GitHub pull request.

    Uses `gh pr close`.
    """
    command = ["pr", "close", str(pr_identifier), "--repo", f"{owner}/{repo}"]
    comment_resolved = resolve_param("pull_request", "close_comment", comment)
    if comment_resolved:
        command.extend(["--comment", str(comment_resolved)])
    if delete_branch:
        command.append("--delete-branch")
    result = run_gh_command(command)
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str):
        return {"status": "success", "message": result.strip()}
    else:
        return {"status": "success", "message": "Closed successfully"}


def _comment_github_pull_request_impl(
    owner: str,
    repo: str,
    pr_identifier: Union[int, str],
    body: Optional[str] = None,
    body_file: Optional[str] = None,
) -> Dict[str, Any]:
    """Implement the logic for adding a comment to a pull request.

    Uses `gh pr comment`.
    """
    if not body and not body_file:
        return {
            "error": "Required parameter missing: provide either 'body' or 'body_file'."
        }
    if body and body_file:
        return {"error": "Parameters 'body' and 'body_file' are mutually exclusive."}
    body_resolved = resolve_param("pull_request", "comment_body", body)
    body_file_resolved = resolve_param("pull_request", "comment_body_file", body_file)
    command = ["pr", "comment", str(pr_identifier), "--repo", f"{owner}/{repo}"]
    if body_resolved:
        command.extend(["--body", str(body_resolved)])
    elif body_file_resolved:
        if str(body_file_resolved) == "-":
            return {
                "error": (
                    "Reading comment body from stdin ('-') is not supported "
                    "via this tool."
                )
            }
        command.extend(["--body-file", str(body_file_resolved)])
    result = run_gh_command(command)
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str) and result.startswith("https://github.com/"):
        return {"status": "success", "comment_url": result.strip()}
    else:
        return {"error": "Unexpected result from gh pr comment", "raw": result}


def _diff_github_pull_request_impl(
    owner: str,
    repo: str,
    pr_identifier: Union[int, str, None] = None,
    color: Optional[str] = None,
    patch: bool = False,
    name_only: bool = False,
) -> Dict[str, Any]:
    """Implement the logic for viewing the diff of a pull request.

    Uses `gh pr diff`.
    """
    command = ["pr", "diff"]
    if pr_identifier is not None:
        command.append(str(pr_identifier))
    command.extend(["--repo", f"{owner}/{repo}"])
    valid_color_options = ["auto", "always", "never"]
    if color:
        color_lower = color.lower()
        if color_lower in valid_color_options:
            command.extend(["--color", color_lower])
        else:
            print(  # pragma: no cover
                f"Warning: Invalid color option '{color}', ignoring.", file=sys.stderr
            )
    if patch:
        command.append("--patch")
    if name_only:
        command.append("--name-only")
    result = run_gh_command(command)
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str):
        return {"status": "success", "diff": result}
    else:
        return {"error": "Unexpected result from gh pr diff", "raw": result}


def _edit_github_pull_request_impl(
    owner: str,
    repo: str,
    pr_identifier: Union[int, str],
    title: Optional[str] = None,
    body: Optional[str] = None,
    base_branch: Optional[str] = None,
    milestone: Optional[str] = None,
    add_assignees: Optional[List[str]] = None,
    remove_assignees: Optional[List[str]] = None,
    add_labels: Optional[List[str]] = None,
    remove_labels: Optional[List[str]] = None,
    add_projects: Optional[List[str]] = None,
    remove_projects: Optional[List[str]] = None,
    add_reviewers: Optional[List[str]] = None,
    remove_reviewers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Implement the logic for editing fields of a pull request.

    Uses `gh pr edit`.
    """
    command = ["pr", "edit", str(pr_identifier), "--repo", f"{owner}/{repo}"]
    milestone_resolved = resolve_param("pull_request", "edit_milestone", milestone)
    body_resolved = resolve_param("pull_request", "body", body)
    if title is not None:
        command.extend(["--title", title])
    if body_resolved is not None:
        command.extend(["--body", str(body_resolved)])
    if base_branch is not None:
        command.extend(["--base", base_branch])
    if milestone_resolved is not None:
        command.extend(["--milestone", str(milestone_resolved)])
    if add_assignees:  # pragma: no cover
        for a in add_assignees:
            command.extend(["--add-assignee", a])
    if remove_assignees:  # pragma: no cover
        for a in remove_assignees:
            command.extend(["--remove-assignee", a])
    if add_labels:  # pragma: no cover
        for lbl in add_labels:
            command.extend(["--add-label", lbl])
    if remove_labels:  # pragma: no cover
        for lbl in remove_labels:
            command.extend(["--remove-label", lbl])
    if add_projects:  # pragma: no cover
        for proj in add_projects:
            command.extend(["--add-project", proj])
    if remove_projects:  # pragma: no cover
        for proj in remove_projects:
            command.extend(["--remove-project", proj])
    if add_reviewers:  # pragma: no cover
        for rvw in add_reviewers:
            command.extend(["--add-reviewer", rvw])
    if remove_reviewers:  # pragma: no cover
        for rvw in remove_reviewers:
            command.extend(["--remove-reviewer", rvw])
    result = run_gh_command(command)
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str) and result.startswith("https://github.com/"):
        return {"status": "success", "url": result.strip()}
    else:
        return {
            "error": "Unexpected result from gh pr edit",
            "raw": result,
        }  # pragma: no cover


def _ready_github_pull_request_impl(
    owner: str, repo: str, pr_identifier: Union[int, str]
) -> Dict[str, Any]:
    """Mark a draft PR as ready for review.

    Uses `gh pr ready`.
    """
    command = ["pr", "ready", str(pr_identifier), "--repo", f"{owner}/{repo}"]

    # Execute - Expects simple string confirmation or error
    result = run_gh_command(command)

    # Standardized result handling
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str):
        return {"status": "success", "message": result.strip()}
    else:
        return {"status": "success", "message": "Marked as ready successfully"}


def _reopen_github_pull_request_impl(
    owner: str, repo: str, pr_identifier: Union[int, str], comment: Optional[str] = None
) -> Dict[str, Any]:
    """Implement the logic for reopening a closed GitHub pull request.

    Uses `gh pr reopen`.
    """
    command = ["pr", "reopen", str(pr_identifier), "--repo", f"{owner}/{repo}"]

    # Resolve comment - reusing 'close_comment' config placeholder for now
    comment_resolved = resolve_param("pull_request", "close_comment", comment)
    if comment_resolved:
        command.extend(["--comment", str(comment_resolved)])

    # Execute - Expects simple string confirmation or error
    result = run_gh_command(command)

    # Standardized result handling
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str):
        return {"status": "success", "message": result.strip()}
    else:
        return {"status": "success", "message": "Reopened successfully"}


def _review_github_pull_request_impl(
    owner: str,
    repo: str,
    pr_identifier: Union[int, str],
    action: str,  # approve, request_changes, comment
    body: Optional[str] = None,
    body_file: Optional[str] = None,
) -> Dict[str, Any]:
    """Implement the logic for submitting a review on a GitHub pull request.

    Uses `gh pr review`.
    """
    action_lower = action.lower()
    valid_actions = {
        "approve": "--approve",
        "comment": "--comment",
        "request_changes": "--request-changes",
    }

    if action_lower not in valid_actions:
        return {
            "error": f"""Invalid action '{action}'. \
Must be one of: {list(valid_actions.keys())}"""
        }
    if (body or body_file) and action_lower == "approve":
        return {"error": "Review body/body_file cannot be used with 'approve' action."}
    if not (body or body_file) and action_lower == "comment":
        return {"error": "Review body/body_file is required for 'comment' action."}

    body_resolved = resolve_param("pull_request", "review_body", body)
    body_file_resolved = resolve_param("pull_request", "review_body_file", body_file)
    # TODO: Add 'review_body', 'review_body_file' to TOOL_PARAM_CONFIG if needed

    if body and body_file:
        return {"error": "Parameters 'body' and 'body_file' are mutually exclusive."}

    command = ["pr", "review", str(pr_identifier), "--repo", f"{owner}/{repo}"]

    command.append(valid_actions[action_lower])

    if body_resolved:  # pragma: no cover
        command.extend(["--body", str(body_resolved)])
    elif body_file_resolved:  # pragma: no cover
        if str(body_file_resolved) == "-":  # pragma: no cover
            return {
                "error": (
                    "Reading review body from stdin ('-') is not supported "
                    "via this tool."
                )
            }
        command.extend(["--body-file", str(body_file_resolved)])

    # Execute - Expects simple string confirmation or error
    result = run_gh_command(command)

    # Standardized result handling
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str):
        # Use the actual confirmation string from gh
        return {"status": "success", "message": result.strip()}
    else:  # pragma: no cover
        # Fallback only if gh returns non-string/non-error
        return {
            "status": "success",
            "message": f"Review submitted ({action}) successfully",
        }


def _status_github_pull_request_impl() -> Dict[str, Any]:
    """Get PR status relevant to the current user/branch.

    Uses `gh pr status`.
    """
    command = [
        "pr",
        "status",
        # Using default fields for now, can be customized if needed
        "--json",
        "createdBy,mentioned,reviewRequested",
    ]

    # Execute - Expect JSON output
    result = run_gh_command(command)

    # Standardized result handling
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, dict):
        # Check if the expected keys are present, gh returns empty dict {}
        # if no PRs found
        if (
            "createdBy" in result
            or "mentioned" in result
            or "reviewRequested" in result
        ):
            return result  # Successful JSON with data
        else:
            # Return a more informative status if gh returns {}
            return {
                "status": "success",
                "message": "No pull requests found for current status query.",
            }
    else:
        return {"error": "Unexpected result from gh pr status", "raw": result}


def _view_github_pull_request_impl(
    owner: str,
    repo: str,
    pr_identifier: Union[int, str],
    comments: bool = False,  # Flag to include comments
) -> Dict[str, Any]:
    """Implement the logic for viewing details of a GitHub pull request.

    Uses `gh pr view`.
    """
    command = [
        "pr",
        "view",
        str(pr_identifier),
        "--repo",
        f"{owner}/{repo}",
        "--json",
        (
            "number,title,state,url,body,createdAt,updatedAt,labels,"
            "assignees,author,baseRefName,headRefName,comments,reviews"
        ),
    ]

    # Note: The --comments flag in the CLI shows comments in the terminal output,
    # but the --json output includes comments regardless if requested in fields.
    # We include 'comments' and 'reviews' in JSON, so the boolean flag isn't
    # directly passed.
    # We could add logic to filter the JSON output if comments=False, but simpler
    # to return all JSON data.

    # Execute - Expect JSON output
    result = run_gh_command(command)

    # Standardized result handling
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, dict):
        return result  # Successful JSON
    else:  # pragma: no cover
        return {"error": "Unexpected result from gh pr view", "raw": result}


def _update_branch_github_pull_request_impl(
    owner: str,
    repo: str,
    pr_identifier: Optional[Union[int, str, None]] = None,
    rebase: bool = False,
) -> Dict[str, Any]:
    """Update a pull request branch with latest changes from the base branch.

    Uses `gh pr update-branch`.
    """
    # Build the command
    command = ["pr", "update-branch"]

    # Add PR identifier if provided
    if pr_identifier:
        command.append(str(pr_identifier))

    # Add repo information
    command.extend(["--repo", f"{owner}/{repo}"])

    # Add rebase flag if specified
    if rebase:
        command.append("--rebase")

    # Execute the command
    result = run_gh_command(command)

    # Process the result
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str):
        # Success case
        return {"status": "success", "message": result.strip() or "PR branch updated."}
    else:
        # Unexpected result
        return {"status": "success", "message": "PR branch updated."}


# --- Tool Registration ---
def init_tools(server: FastMCP):
    """Register pull request-related tools with the MCP server."""
    server.tool()(_create_pull_request_impl)
    server.tool()(_list_github_pull_requests_impl)
    server.tool()(_checkout_github_pull_request_impl)
    server.tool()(_close_github_pull_request_impl)
    server.tool()(_comment_github_pull_request_impl)
    server.tool()(_diff_github_pull_request_impl)
    server.tool()(_edit_github_pull_request_impl)
    server.tool()(_ready_github_pull_request_impl)
    server.tool()(_reopen_github_pull_request_impl)
    server.tool()(_review_github_pull_request_impl)
    server.tool()(_status_github_pull_request_impl)
    server.tool()(_view_github_pull_request_impl)
    server.tool()(_update_branch_github_pull_request_impl)
