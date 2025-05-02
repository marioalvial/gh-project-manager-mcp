"""Implementations for GitHub issue-related MCP tools."""

import json
import sys  # Import sys for stderr
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from gh_project_manager_mcp.utils.gh_utils import resolve_param, run_gh_command

# --- Tool Implementations (without decorator) ---


def _create_github_issue_impl(
    owner: str,
    repo: str,
    title: str,
    body: str,
    issue_type: Optional[str] = None,
    assignee: Optional[str] = None,
    project: Optional[str] = None,
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Implement the logic for creating a GitHub issue.

    Uses `gh issue create`.
    """
    assignee_resolved = resolve_param("issue", "assignee", assignee)
    project_resolved = resolve_param("issue", "project", project)
    labels_resolved = resolve_param("issue", "labels", labels)
    issue_type_resolved = resolve_param("issue", "issue_type", issue_type)

    command = [
        "issue",
        "create",
        "--repo",
        f"{owner}/{repo}",
        "--title",
        title,
        "--body",
        body,
        "--json",
        "url,number,title,body,state"
    ]
    if project_resolved:
        command.extend(["--project", str(project_resolved)])
    if assignee_resolved:
        command.extend(["--assignee", str(assignee_resolved)])

    labels_to_add = []
    if issue_type_resolved:
        if str(issue_type_resolved).lower() == "feature":
            labels_to_add.append("enhancement")
        elif str(issue_type_resolved).lower() == "bugfix":
            labels_to_add.append("bug")

    if isinstance(labels_resolved, list):
        labels_to_add.extend(labels_resolved)

    for label in labels_to_add:
        command.extend(["--label", label])

    result = run_gh_command(command)

    if isinstance(result, dict):
        return result
    elif isinstance(result, str):
        print(
            f"Warning: gh issue create returned string instead of JSON: {result}",
            file=sys.stderr
        )
        return {"error": "Unexpected string result from gh issue create", "raw": result}
    else:
        print(
            f"Warning: gh issue create returned unexpected type: {type(result)}",
            file=sys.stderr
        )
        return {"error": "Unexpected result type from gh issue create", "raw": str(result)}


def _get_github_issue_impl(
    owner: str,
    repo: str,
    issue_number: int,
) -> Dict[str, Any]:
    """Implement the logic for getting a specific GitHub issue.

    Uses `gh issue view`.
    """
    command = [
        "issue",
        "view",
        str(issue_number),
        "--repo",
        f"{owner}/{repo}",
        "--json",
        (
            "number,title,state,url,body,createdAt,updatedAt,labels,"
            "assignees,comments,author,closedAt"
        )
    ]
    result = run_gh_command(command)

    # Check result type from run_gh_command
    if isinstance(result, dict) and "number" in result: # Check for a key expected in success
        return result # Already parsed JSON dict
    elif isinstance(result, dict) and "error" in result:
        return result # Return error dict directly
    elif isinstance(result, str):
        # Attempt to parse if it's a string (unexpected case for --json)
        try:
            issue = json.loads(result)
            if isinstance(issue, dict):
                return issue
            else:
                print(
                    f"gh issue view returned JSON but not a dict: {result}",
                    file=sys.stderr
                )
                return {
                    "error": ("Expected dict result from gh issue view but got "
                              "different JSON type"),
                    "raw": result
                }
        except json.JSONDecodeError:
            print(f"Error decoding JSON from gh issue view: {result}", file=sys.stderr)
            return {
                "error": "Failed to decode JSON response from gh issue view",
                "raw": result
            }
    else:
        print(
            f"Unexpected result type from gh issue view: {type(result)}",
            file=sys.stderr
        )
        return {
            "error": "Unexpected result type from gh issue view",
            "raw": str(result)
        }


def _list_github_issues_impl(
    owner: str,
    repo: str,
    state: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[List[str]] = None,
    limit: Optional[int] = None,
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """Implement the logic for listing GitHub issues with filters.

    Uses `gh issue list`.
    """
    state_resolved = resolve_param("issue", "state", state)
    assignee_resolved = resolve_param("issue", "assignee", assignee)
    labels_resolved = resolve_param("issue", "labels", labels)
    limit_resolved = resolve_param("issue", "limit", limit)

    command = [
        "issue",
        "list",
        "--repo",
        f"{owner}/{repo}",
        "--json",
        "number,title,state,url,createdAt,updatedAt,labels,assignees",
    ]
    if state_resolved:
        command.extend(["--state", state_resolved])
    if assignee_resolved:
        command.extend(["--assignee", assignee_resolved])

    if isinstance(labels_resolved, list) and labels_resolved:
        # Handle labels correctly: repeat --label flag
        for label in labels_resolved:
             command.extend(["--label", label])
    if limit_resolved:
        command.extend(["--limit", str(limit_resolved)])
    elif limit is not None and limit <= 0:
        print(f"Warning: Invalid limit '{limit}'. Must be positive. Ignoring limit.")

    result = run_gh_command(command)

    # Check result type from run_gh_command
    if isinstance(result, list):
        return result  # Already parsed JSON list
    elif isinstance(result, dict) and "error" in result:
        print(f"Error running gh issue list: {result.get('error')}", file=sys.stderr)
        return [] # Return empty list on error
    elif isinstance(result, str):
        # Attempt to parse if it's a string (unexpected case for --json)
        try:
            issues = json.loads(result)
            if isinstance(issues, list):
                return issues
            else:
                print(
                    f"gh issue list returned JSON but not a list: {result}",
                    file=sys.stderr
                )
                return [
                    {
                        "error": ("Expected list result from gh issue list but got "
                                  "different JSON type"),
                        "raw": result,
                    }
                ]
        except json.JSONDecodeError:
            print(f"Error decoding JSON from gh issue list: {result}", file=sys.stderr)
            return [
                {"error": "Failed to decode JSON response from gh issue list", "raw": result}
            ]
    else:
        # Handle other unexpected types
        print(
            f"Unexpected result type from gh issue list: {type(result)}",
            file=sys.stderr
        )
        return [
            {"error": "Unexpected result type from gh issue list", "raw": str(result)}
        ]


def _close_github_issue_impl(
    owner: str,
    repo: str,
    issue_identifier: Union[int, str],
    comment: Optional[str] = None,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Implement the logic for closing a GitHub issue.

    Uses `gh issue close`.
    """
    comment_resolved = resolve_param("issue", "close_comment", comment)
    reason_resolved = resolve_param("issue", "close_reason", reason)

    valid_reasons = ["completed", "not planned"]
    if reason_resolved and reason_resolved not in valid_reasons:
        return {
            "error": (f"Invalid reason '{reason_resolved}'. "
                      f"Must be one of: {valid_reasons}")
        }

    command = ["issue", "close", str(issue_identifier), "--repo", f"{owner}/{repo}"]
    if comment_resolved:
        command.extend(["--comment", str(comment_resolved)])
    if reason_resolved:
        command.extend(["--reason", reason_resolved])

    result = run_gh_command(command)

    # Standardized result handling (expect string or error dict)
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str):
        # Assume string output means success (URL or confirmation message)
        message = result.strip()
        status = {"status": "success"}
        if message.startswith("https://github.com/"):
            status["url"] = message
        else:
            status["message"] = message
        return status
    else:
        return {"error": "Unexpected result from gh issue close", "raw": result}


def _comment_github_issue_impl(
    owner: str,
    repo: str,
    issue_identifier: Union[int, str],
    body: Optional[str] = None,
    body_file: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a comment to a GitHub issue.

    Uses `gh issue comment`.
    """
    if not body and not body_file:
        return {
            "error": "Required parameter missing: provide either 'body' or 'body_file'."
        }
    if body and body_file:
        return {"error": "Parameters 'body' and 'body_file' are mutually exclusive."}

    body_resolved = resolve_param("issue", "comment_body", body)
    body_file_resolved = resolve_param("issue", "comment_body_file", body_file)

    command = ["issue", "comment", str(issue_identifier), "--repo", f"{owner}/{repo}"]
    if body_resolved:
        command.extend(["--body", str(body_resolved)])
    elif body_file_resolved:
        if str(body_file_resolved) == "-":
            return {
                "error": ("Reading comment body from stdin ('-') is not supported "
                          "via this tool.")
            }
        command.extend(["--body-file", str(body_file_resolved)])

    result = run_gh_command(command)

    # Standardized result handling (expect comment URL string or error dict)
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str) and result.startswith("https://github.com/"):
        return {"status": "success", "comment_url": result.strip()}
    else:
        return {"error": "Unexpected result from gh issue comment", "raw": result}


def _delete_github_issue_impl(
    owner: str,
    repo: str,
    issue_identifier: Union[int, str],
    skip_confirmation: bool = False,
) -> Dict[str, Any]:
    """Delete a GitHub issue.

    Uses `gh issue delete`.
    """
    command = ["issue", "delete", str(issue_identifier), "--repo", f"{owner}/{repo}"]
    if skip_confirmation:
        command.append("--yes")

    result = run_gh_command(command)

    # Standardized result handling (expect simple string or error dict)
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str):
        return {"status": "success", "message": result.strip()}
    else:  # Assume success if no error and not string (e.g., empty output?)
        return {"status": "success"}


def _create_issue_branch_impl(
    owner: str,
    repo: str,
    issue_identifier: Union[int, str],
    branch_name: Optional[str] = None,
    checkout: bool = False,
    base_branch: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a branch from a GitHub issue.

    Uses `gh issue develop`.
    """
    base_branch_resolved = resolve_param("issue", "develop_base_branch", base_branch)

    command = ["issue", "develop", str(issue_identifier), "--repo", f"{owner}/{repo}"]
    if branch_name:
        command.extend(["--branch", branch_name])
    if base_branch_resolved:
        command.extend(["--base", base_branch_resolved])
    if checkout:
        command.append("--checkout")

    result = run_gh_command(command)

    # Standardized result handling (expect string or error dict)
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str):
        return {"status": "success", "message": result.strip()}
    else:
        return {"error": "Unexpected result from gh issue develop", "raw": result}


def _list_issue_linked_branches_impl(
    owner: str, repo: str, issue_identifier: Union[int, str]
) -> Dict[str, Any]:
    """List branches linked to a GitHub issue.

    Uses `gh issue list --linked-prs` (indirectly, need to check gh capabilities).
    NOTE: The gh CLI command might be different or this requires parsing.
          Currently assumes `gh issue view --json branches` might work.
    """
    command = [
        "issue",
        "develop",
        str(issue_identifier),
        "--repo",
        f"{owner}/{repo}",
        "--list",
    ]
    result = run_gh_command(command)

    # Standardized result handling (expect string or error dict)
    if isinstance(result, dict) and "error" in result:
        return result # Return error dict directly
    elif isinstance(result, str):
        # Parse the newline-separated list of branches
        # Return the raw string, let caller parse or handle non-JSON
        # branches = [line.strip() for line in result.splitlines() if line.strip()]
        # return {"status": "success", "linked_branches": branches}
        # Simplification: return raw string if not error
        return {"status": "success", "output": result.strip()}
    elif isinstance(result, list):
         # If gh returns JSON list directly (future proofing)
         return {"status": "success", "linked_branches": result}
    else:
        # Handle unexpected non-string, non-error, non-list results
        return {
            "error": "Unexpected result type from gh issue develop --list",
            "raw": result,
        }


def _status_github_issue_impl() -> Dict[str, Any]:
    """Show the status of relevant issues and PRs.

    Uses `gh issue status`.
    """
    # Restore function body
    command = [
        "issue",
        "status",
        "--json",
        "currentBranch,createdBy,openIssues,closedIssues,openPullRequests",
    ]

    # Execute - Expect JSON output
    result = run_gh_command(command)

    # Standardized result handling
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, dict):
        return result  # Successful JSON
    else:
        return {"error": "Unexpected result from gh issue status", "raw": result}


def _transfer_github_issue_impl(
    owner: str,
    repo: str,
    issue_identifier: Union[int, str],
    destination_repo: str,  # Format: owner/repo
) -> Dict[str, Any]:
    """Transfer a GitHub issue to another repository.

    Uses `gh issue transfer`.
    """
    # Fix indentation for the entire function body
    # Note: The command requires the original repo in the context or via --repo
    command = [
        "issue",
        "transfer",
        str(issue_identifier),
        destination_repo,
        "--repo",
        f"{owner}/{repo}",  # Specify original repo context
    ]

    # Execute - Transfer returns the new issue URL
    result = run_gh_command(command)

    # Standardized result handling
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str) and result.startswith("https://github.com/"):
        return {"status": "success", "new_url": result.strip()}
    else:
        return {"error": "Unexpected result from gh issue transfer", "raw": result}


def _unlock_github_issue_impl(
    owner: str, repo: str, issue_identifier: Union[int, str]
) -> Dict[str, Any]:
    """Unlock a GitHub issue conversation.

    Uses `gh issue unlock`.
    """
    command = ["issue", "unlock", str(issue_identifier), "--repo", f"{owner}/{repo}"]

    # Execute - Unlock doesn't usually return specific data, just confirms/errors
    result = run_gh_command(command)

    # Standardized result handling
    if isinstance(result, dict) and "error" in result:
        return result
    else:
        # Assume success if no error dict (string output is confirmation)
        return {
            "status": "success",
            "message": str(result).strip() if result else "Unlocked successfully",
        }


def _unpin_github_issue_impl(
    owner: str, repo: str, issue_identifier: Union[int, str]
) -> Dict[str, Any]:
    """Unpin a GitHub issue.

    Uses `gh issue unpin`.
    """
    command = ["issue", "unpin", str(issue_identifier), "--repo", f"{owner}/{repo}"]

    # Execute - Unpin doesn't usually return specific data, just confirms/errors
    result = run_gh_command(command)

    # Standardized result handling
    if isinstance(result, dict) and "error" in result:
        return result
    else:
        # Assume success if no error dict (string output is confirmation)
        return {
            "status": "success",
            "message": str(result).strip() if result else "Unpinned successfully",
        }


# --- Tool Registration ---


def init_tools(server: FastMCP):
    """Register issue-related tools with the MCP server."""
    server.tool()(_create_github_issue_impl)
    server.tool()(_get_github_issue_impl)
    server.tool()(_list_github_issues_impl)
    server.tool()(_close_github_issue_impl)
    server.tool()(_comment_github_issue_impl)
    server.tool()(_delete_github_issue_impl)
    server.tool(name="create_issue_branch")(_create_issue_branch_impl)
    server.tool(name="list_issue_linked_branches")(_list_issue_linked_branches_impl)
    server.tool()(_status_github_issue_impl)
    server.tool()(_transfer_github_issue_impl)
    server.tool()(_unlock_github_issue_impl)
    server.tool()(_unpin_github_issue_impl)
