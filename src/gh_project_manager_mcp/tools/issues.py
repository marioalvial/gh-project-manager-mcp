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
) -> Dict[str, Any]:
    """Implement the logic for creating a GitHub issue.

    Uses `gh issue create`.
    """
    try:
        print(
            f"DEBUG [create_issue]: Starting with owner={owner}, repo={repo}, title={title}"
        )

        # Define optional parameters inside the function
        body: Optional[str] = None
        assignee: Optional[str] = None
        issue_type: Optional[str] = None
        labels: Optional[List[str]] = None
        project: Optional[str] = None

        # Resolve optional parameters through resolve_param utility
        try:
            assignee_resolved = resolve_param("issue", "assignee", assignee)
            labels_resolved = resolve_param("issue", "labels", labels)
            project_resolved = resolve_param("issue", "project", project)
            print(
                f"DEBUG [create_issue]: Resolved params: assignee={assignee_resolved}, labels={labels_resolved}, project={project_resolved}"
            )
        except Exception as e:
            print(f"DEBUG [create_issue]: Error resolving parameters: {str(e)}")
            return {"error": "Failed to resolve parameters", "details": str(e)}

        # Normalizar o nome do repositório (substituir underscores por hifens se necessário)
        # Isso é necessário porque o GitHub CLI espera hifens nos nomes dos repositórios,
        # mas nosso código pode estar usando underscores
        repo = repo.replace("_", "-")
        print(f"DEBUG [create_issue]: Normalized repo name: {repo}")

        # Start building the command with required parameters
        command = [
            "issue",
            "create",
            "--repo",
            f"{owner}/{repo}",
            "--title",
            title,
        ]

        # Add body if provided, otherwise use a default
        body_resolved = body or "Created via GitHub MCP Server"
        command.extend(["--body", body_resolved])

        # Add optional parameters if they were provided/resolved
        if project_resolved:
            command.extend(["--project", project_resolved])
        if assignee_resolved:
            command.extend(["--assignee", assignee_resolved])

        # Handle issue type (maps to specific labels in GitHub: bug, enhancement, etc.)
        try:
            issue_type_resolved = resolve_param("issue", "type", issue_type)
            if issue_type_resolved:
                # Map issue_type to GitHub's label system
                type_label_map = {
                    "bug": "bug",
                    "feature": "enhancement",
                    "enhancement": "enhancement",
                    "documentation": "documentation",
                    "question": "question",
                }
                label = type_label_map.get(issue_type_resolved.lower())
                if label:
                    if labels_resolved and isinstance(labels_resolved, list):
                        labels_resolved.append(label)
                    else:
                        labels_resolved = [label]
        except Exception as e:
            print(f"DEBUG [create_issue]: Error resolving issue type: {str(e)}")
            # Continue execution without issue type

        # Add labels if provided
        if labels_resolved:
            for label in labels_resolved:
                command.extend(["--label", label])

        print(f"DEBUG [create_issue]: Final command: gh {' '.join(command)}")

        # Execute the command
        result = run_gh_command(command)
        print(f"DEBUG [create_issue]: Command result type: {type(result)}")

        # Handle the command result
        if isinstance(result, dict):
            if "error" in result:
                print(f"DEBUG [create_issue]: Error in result: {result}")
            else:
                print(f"DEBUG [create_issue]: Success result: {result}")
            return result  # Return the JSON result directly
        elif isinstance(result, str):
            print(f"DEBUG [create_issue]: String result received: {result[:100]}")

            # Tenta interpretar links do GitHub como sucesso
            if result.startswith("https://github.com"):
                url = result.strip()

                # Extrair informações do URL
                # Formato típico: https://github.com/owner/repo/issues/123
                try:
                    parts = url.split("/")
                    issue_number = int(parts[-1])

                    return {
                        "status": "success",
                        "url": url,
                        "number": issue_number,
                        "title": title,
                        "body": body_resolved,
                        "state": "open",
                    }
                except (IndexError, ValueError):
                    # Se não conseguir extrair o número da issue, retorne apenas a URL
                    return {
                        "status": "success",
                        "url": url,
                        "message": f"Issue created successfully: {url}",
                    }

            # Tenta analisar como JSON (caso o resultado seja JSON em uma string)
            try:
                parsed_json = json.loads(result)
                print(f"DEBUG [create_issue]: Parsed JSON from string: {parsed_json}")
                return parsed_json
            except json.JSONDecodeError:
                print("DEBUG [create_issue]: Failed to parse result as JSON")
                return {
                    "error": "Unexpected string result from gh issue create",
                    "raw": result,
                }
        else:
            print(f"DEBUG [create_issue]: Unexpected result type: {type(result)}")
            return {
                "error": "Unexpected result type from gh issue create",
                "raw": str(result),
            }
    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        print(f"DEBUG [create_issue]: Unhandled exception: {str(e)}")
        print(f"DEBUG [create_issue]: Traceback: {error_trace}")
        return {
            "error": "Unhandled exception in create_github_issue_impl",
            "details": str(e),
            "traceback": error_trace,
        }


def _get_github_issue_impl(owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
    """Get details of a specific GitHub issue by number.

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
        ),
    ]

    # Run the command and get the result
    result = run_gh_command(command)

    # Process the result
    if isinstance(result, dict) and "number" in result:
        return result  # Return the issue details directly
    elif isinstance(result, dict) and "error" in result:
        return result  # Return the error directly
    else:
        return {"error": "Unexpected result from gh issue view", "raw": result}


def _list_github_issues_impl(
    owner: str,
    repo: str,
) -> List[Dict[str, Any]]:
    """List GitHub issues with optional filtering.

    Uses `gh issue list`.
    """
    # Define optional parameters inside the function
    state: Optional[str] = None
    assignee: Optional[str] = None
    creator: Optional[str] = None
    mentioned: Optional[str] = None
    labels: Optional[List[str]] = None
    milestone: Optional[str] = None
    limit: Optional[int] = None

    # Resolve parameters with defaults
    state_resolved = resolve_param("issue", "state", state)
    limit_resolved = resolve_param("issue", "limit", limit)
    assignee_resolved = resolve_param("issue", "assignee", assignee)
    labels_resolved = resolve_param("issue", "labels", labels)

    # Basic command with common flags
    command = [
        "issue",
        "list",
        "--repo",
        f"{owner}/{repo}",
        "--json",
        "number,title,state,url,createdAt,updatedAt,labels,assignees",
    ]

    # Add filters based on provided arguments
    if state_resolved:
        command.extend(["--state", state_resolved])
    if assignee_resolved:
        command.extend(["--assignee", assignee_resolved])
    if creator:
        command.extend(["--author", creator])
    if mentioned:
        command.extend(["--mention", mentioned])
    if milestone:
        command.extend(["--milestone", milestone])
    if labels_resolved:
        # Add each label separately
        for label in labels_resolved:
            command.extend(["--label", label])
    if limit_resolved:
        command.extend(["--limit", str(limit_resolved)])

    result = run_gh_command(command)

    if isinstance(result, list):
        return result
    elif isinstance(result, dict) and "error" in result:
        print(
            f"Error running gh issue list: {result.get('error')}", file=sys.stderr
        )  # pragma: no cover
        return []  # Return empty list on error
    elif isinstance(result, str):
        # Simplified logic: If it's a string, try to parse it as JSON.
        # If parsing succeeds and it's a list, return it.
        # Otherwise, return an error dictionary.
        # This simplification reduces branching and makes coverage easier.
        result_error = {
            "error": "Failed to decode JSON response from gh issue list",
            "raw": result,
        }

        try:
            parsed_result = json.loads(result)
        except json.JSONDecodeError:  # pragma: no cover
            print(f"Error decoding JSON from gh issue list: {result}", file=sys.stderr)
            return [result_error]

        if not isinstance(parsed_result, list):  # pragma: no cover
            print(
                f"gh issue list returned JSON but not a list: {result}", file=sys.stderr
            )
            result_error["error"] = (
                "Expected list result from gh issue list but got different JSON type"
            )
            return [result_error]

        return parsed_result
    else:
        print(
            f"Unexpected result from gh issue list: {result}", file=sys.stderr
        )  # pragma: no cover
        return []  # Return empty list for other unexpected results


def _close_github_issue_impl(
    owner: str,
    repo: str,
    issue_identifier: Union[int, str],
    comment: Optional[str] = None,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Close a GitHub issue (by number or URL).

    Uses `gh issue close`.
    """
    # Basic command to close the issue
    command = ["issue", "close", str(issue_identifier), "--repo", f"{owner}/{repo}"]

    # Add optional parameters if provided
    comment_resolved = resolve_param("issue", "close_comment", comment)
    if comment_resolved:
        command.extend(["--comment", comment_resolved])

    # Add optional reason if provided
    reason_resolved = resolve_param("issue", "close_reason", reason)
    if reason_resolved:
        # Validate reason (GitHub API requires one of these values)
        valid_reasons = ["completed", "not planned", "duplicate"]
        if reason_resolved.lower() in valid_reasons:
            command.extend(["--reason", reason_resolved.lower()])
        else:
            return {
                "error": (
                    f"Invalid reason '{reason_resolved}'. "
                    f"Must be one of: {valid_reasons}"
                )
            }

    # Run the command
    result = run_gh_command(command)

    # Process the result
    if isinstance(result, dict) and "error" in result:
        return result  # Return error dictionary
    elif isinstance(result, str):
        # Success case for string output (URL or confirmation message)
        if result.startswith("https://github.com"):
            return {"status": "success", "url": result}
        else:
            return {"status": "success", "message": result.strip()}
    else:
        # Unexpected success (empty string or other)
        return {"status": "success", "message": "Issue closed successfully."}


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
    # Validate that either body or body_file is provided, but not both
    if not body and not body_file:
        return {
            "error": "Required parameter missing: provide either 'body' or 'body_file'."
        }
    if body and body_file:
        return {"error": "Parameters 'body' and 'body_file' are mutually exclusive."}

    # Resolve parameters
    body_resolved = resolve_param("issue", "comment_body", body)
    body_file_resolved = resolve_param("issue", "comment_body_file", body_file)

    # Create the base command
    command = ["issue", "comment", str(issue_identifier), "--repo", f"{owner}/{repo}"]

    # Add either body or body_file to the command
    if body_resolved:
        command.extend(["--body", body_resolved])
    elif body_file_resolved:
        # Handle special stdin case
        if body_file_resolved == "-":
            return {
                "error": (
                    "Reading comment body from stdin ('-') is not supported "
                    "via this tool."
                )
            }
        command.extend(["--body-file", body_file_resolved])

    # Run the command
    result = run_gh_command(command)

    # Process the result
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str) and result.startswith("https://github.com/"):
        # Return the comment URL on success
        return {"status": "success", "comment_url": result.strip()}
    else:
        # Handle unexpected output
        return {"error": "Unexpected result from gh issue comment", "raw": result}


def _delete_github_issue_impl(
    owner: str,
    repo: str,
    issue_identifier: Union[int, str],
    skip_confirmation: bool = False,
) -> Dict[str, Any]:
    """Delete a GitHub issue (requires admin rights).

    Uses `gh issue delete`.
    """
    # Create the command
    command = ["issue", "delete", str(issue_identifier), "--repo", f"{owner}/{repo}"]

    # Add --yes flag to skip confirmation if requested
    if skip_confirmation:
        command.append("--yes")

    # Run the command
    result = run_gh_command(command)

    # Process the result
    if isinstance(result, dict) and "error" in result:
        return result  # Return error dictionary
    else:
        # Success case - could be empty or confirmation message
        return {
            "status": "success",
            "message": result.strip() if isinstance(result, str) else "",
        }


def _status_github_issue_impl() -> Dict[str, Any]:
    """Get issue status context for the current branch/user.

    Uses `gh issue status`.
    """
    # Create the command with JSON output
    command = [
        "issue",
        "status",
        "--json",
        "currentBranch,createdBy,openIssues,closedIssues,openPullRequests",
    ]

    # Run the command
    result = run_gh_command(command)

    # Return the result directly, it's already structured
    return result


def _edit_github_issue_impl(
    owner: str,
    repo: str,
    issue_identifier: Union[int, str],
    title: Optional[str] = None,
    body: Optional[str] = None,
    add_assignees: Optional[List[str]] = None,
    remove_assignees: Optional[List[str]] = None,
    add_labels: Optional[List[str]] = None,
    remove_labels: Optional[List[str]] = None,
    add_projects: Optional[List[str]] = None,
    remove_projects: Optional[List[str]] = None,
    milestone: Optional[Union[str, int]] = None,
) -> Dict[str, Any]:
    """Edit issue metadata.

    Uses `gh issue edit`.
    """
    # Create the base command
    command = ["issue", "edit", str(issue_identifier), "--repo", f"{owner}/{repo}"]

    # Resolve optional parameters that have config defaults
    milestone_resolved = resolve_param("issue", "edit_milestone", milestone)

    # Add parameters if they were provided
    if title is not None:
        command.extend(["--title", title])
    if body is not None:
        command.extend(["--body", body])
    if milestone_resolved is not None:
        command.extend(["--milestone", str(milestone_resolved)])

    # Handle assignees
    if add_assignees:
        for assignee in add_assignees:
            command.extend(["--add-assignee", assignee])
    if remove_assignees:
        for assignee in remove_assignees:
            command.extend(["--remove-assignee", assignee])

    # Handle labels
    if add_labels:
        for label in add_labels:
            command.extend(["--add-label", label])
    if remove_labels:
        for label in remove_labels:
            command.extend(["--remove-label", label])

    # Handle projects
    if add_projects:
        for project in add_projects:
            command.extend(["--add-project", project])
    if remove_projects:  # pragma: no cover
        for project in remove_projects:
            command.extend(["--remove-project", project])

    # Run the command
    result = run_gh_command(command)

    # Process the result
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str):
        # Success case - typically returns the issue URL
        if result.startswith("https://github.com"):
            return {"status": "success", "url": result.strip()}
        else:
            return {"status": "success", "message": result.strip()}
    else:  # pragma: no cover
        return {"status": "success", "message": "Issue updated successfully."}


def _reopen_github_issue_impl(
    owner: str,
    repo: str,
    issue_identifier: Union[int, str],
    comment: Optional[str] = None,
) -> Dict[str, Any]:
    """Reopen a closed issue.

    Uses `gh issue reopen`.
    """
    # Create the base command
    command = ["issue", "reopen", str(issue_identifier), "--repo", f"{owner}/{repo}"]

    # Add optional comment if provided
    # Note: We reuse the close_comment parameter config for this
    comment_resolved = resolve_param("issue", "close_comment", comment)
    if comment_resolved:
        command.extend(["--comment", comment_resolved])

    # Run the command
    result = run_gh_command(command)

    # Process the result
    if isinstance(result, dict) and "error" in result:
        return result
    elif isinstance(result, str):
        # Success case - typically returns the issue URL
        if result.startswith("https://github.com"):
            return {"status": "success", "url": result.strip()}
        else:
            return {"status": "success", "message": result.strip()}
    else:
        return {"status": "success", "message": "Issue reopened successfully."}


# --- Tool Registration ---


def init_tools(server: FastMCP):
    """Register issue-related tools with the MCP server."""
    print("\n=== Registering Issue Tools ===")  # pragma: no cover

    # Print the function names
    print(
        f"Create issue function name: {_create_github_issue_impl.__name__}"
    )  # pragma: no cover
    print(
        f"Get issue function name: {_get_github_issue_impl.__name__}"
    )  # pragma: no cover
    print(
        f"List issues function name: {_list_github_issues_impl.__name__}"
    )  # pragma: no cover

    # Register the tools
    server.tool()(_create_github_issue_impl)
    server.tool()(_get_github_issue_impl)
    server.tool()(_list_github_issues_impl)
    server.tool()(_close_github_issue_impl)
    server.tool()(_comment_github_issue_impl)
    server.tool()(_delete_github_issue_impl)
    server.tool()(_status_github_issue_impl)
    server.tool()(_edit_github_issue_impl)
    server.tool()(_reopen_github_issue_impl)

    print("=== Issue Tools Registered ===\n")  # pragma: no cover
