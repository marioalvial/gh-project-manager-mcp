"""Configuration for the GitHub Project Manager MCP tool parameters."""

import os
from typing import Any, Dict

# Define the mapping for tool parameters
# Structure:
# CAPABILITY -> PARAMETER_NAME -> {
#    'env_var': Optional[str] (Environment variable name),
#    'default': Optional[Any] (Default value if env var not set),
#    'type': Literal['str', 'int', 'list', 'bool'] (Type hint for conversion)
# }
TOOL_PARAM_CONFIG: Dict[str, Dict[str, Dict[str, Any]]] = {
    "issue": {
        # --- create_github_issue ---
        "assignee": {
            "env_var": "DEFAULT_ISSUE_ASSIGNEE",
            "default": "@me",
            "type": "str",
        },
        "project": {"env_var": "DEFAULT_ISSUE_PROJECT", "default": None, "type": "str"},
        "labels": {
            "env_var": "DEFAULT_ISSUE_LABELS",
            "default": None,
            "type": "list",
        },  # Comma-separated in env var
        "issue_type": {
            "env_var": "DEFAULT_ISSUE_TYPE",
            "default": None,
            "type": "str",
        },  # Used for 'enhancement'/'bug'
        # body is now mandatory, no config needed
        # --- list_github_issues ---
        "state": {
            "env_var": "DEFAULT_ISSUE_LIST_STATE",
            "default": "open",
            "type": "str",
        },
        "limit": {"env_var": "DEFAULT_ISSUE_LIST_LIMIT", "default": 30, "type": "int"},
        # 'assignee' and 'labels' for list can reuse the create definitions above
        # --- get_github_issue ---
        # No configurable defaults for get_github_issue (owner, repo,
        # issue_number are mandatory)
        "close_comment": {"env_var": None, "default": None, "type": "str"},
        "close_reason": {
            "env_var": None,
            "default": None,
            "type": "str",
        },  # Valid: 'completed', 'not planned'
        # Added for gh issue comment
        "comment_body": {"env_var": None, "default": None, "type": "str"},
        "comment_body_file": {"env_var": None, "default": None, "type": "str"},
        # Added for gh issue develop (create branch)
        "develop_base_branch": {
            "env_var": "MCP_GITHUB_DEFAULT_BASE_BRANCH",
            "default": None,
            "type": "str",
        },
        # Added for gh issue edit
        "edit_milestone": {
            "env_var": "DEFAULT_ISSUE_EDIT_MILESTONE",
            "default": None,
            "type": "str",
        },
    },
    "pull_request": {
        # --- create_pull_request ---
        "draft": {"env_var": "DEFAULT_PR_DRAFT", "default": False, "type": "bool"},
        "assignees": {
            "env_var": "DEFAULT_PR_ASSIGNEES",
            "default": "@me",
            "type": "list",
        },  # Comma-separated
        "reviewers": {
            "env_var": "DEFAULT_PR_REVIEWERS",
            "default": None,
            "type": "list",
        },  # Comma-separated
        "pr_labels": {
            "env_var": "DEFAULT_PR_LABELS",
            "default": None,
            "type": "list",
        },  # Comma-separated (using pr_labels to avoid clash with issue labels)
        "pr_project": {"env_var": "DEFAULT_PR_PROJECT", "default": None, "type": "str"},
        # --- list_pull_requests ---
        "pr_state": {
            "env_var": "DEFAULT_PR_LIST_STATE",
            "default": "open",
            "type": "str",
        },  # Using pr_state to avoid clash
        "pr_limit": {"env_var": "DEFAULT_PR_LIST_LIMIT", "default": 30, "type": "int"},
        # 'pr_labels' for list can reuse the create definition above
        # --- get_pull_request ---
        # No specific optional parameters with defaults needed here
        # --- merge_pull_request ---
        "merge_method": {
            "env_var": "DEFAULT_PR_MERGE_METHOD",
            "default": "merge",
            "type": "str",
        },
        "delete_branch": {
            "env_var": "DEFAULT_PR_DELETE_BRANCH",
            "default": True,
            "type": "bool",
        },
    },
    "project_item": {
        # --- add_github_item_to_project ---
        "project_owner": {
            "env_var": "DEFAULT_PROJECT_OWNER",
            "default": None,
            "type": "str",
        },
        "project": {
            "env_var": "DEFAULT_PROJECT_TARGET",
            "default": None,
            "type": "str",
        },
        # --- Potential future tools (create/update project item) ---
        "priority": {
            "env_var": "DEFAULT_PROJECT_ITEM_PRIORITY",
            "default": "Medium",
            "type": "str",
        },
        "status": {
            "env_var": "DEFAULT_PROJECT_ITEM_STATUS",
            "default": "to-do",
            "type": "str",
        },
    },
    "project": {
        # Existing example placeholders removed for clarity, adding actual used params
        "copy_source_owner": {
            "env_var": "DEFAULT_PROJECT_COPY_SOURCE_OWNER",
            "default": None,
            "type": "str",
        },
        "delete_owner": {
            "env_var": "DEFAULT_PROJECT_DELETE_OWNER",
            "default": None,
            "type": "str",
        },
        "edit_owner": {
            "env_var": "DEFAULT_PROJECT_EDIT_OWNER",
            "default": None,
            "type": "str",
        },
        "field_owner": {
            "env_var": "DEFAULT_PROJECT_FIELD_OWNER",
            "default": None,
            "type": "str",
        },  # For field-create, field-delete
        "field_list_owner": {
            "env_var": "DEFAULT_PROJECT_FIELD_LIST_OWNER",
            "default": None,
            "type": "str",
        },
        "field_list_limit": {
            "env_var": "DEFAULT_PROJECT_FIELD_LIST_LIMIT",
            "default": 30,
            "type": "int",
        },
        "item_add_owner": {
            "env_var": "DEFAULT_PROJECT_ITEM_ADD_OWNER",
            "default": None,
            "type": "str",
        },
        "item_archive_owner": {
            "env_var": "DEFAULT_PROJECT_ITEM_ARCHIVE_OWNER",
            "default": None,
            "type": "str",
        },
        "item_archive_project_id": {
            "env_var": "DEFAULT_PROJECT_ITEM_ARCHIVE_PROJECT_ID",
            "default": None,
            "type": "int",
        },
        "item_delete_owner": {
            "env_var": "DEFAULT_PROJECT_ITEM_DELETE_OWNER",
            "default": None,
            "type": "str",
        },
        "item_delete_project_id": {
            "env_var": "DEFAULT_PROJECT_ITEM_DELETE_PROJECT_ID",
            "default": None,
            "type": "int",
        },
        "item_edit_owner": {
            "env_var": "DEFAULT_PROJECT_ITEM_EDIT_OWNER",
            "default": None,
            "type": "str",
        },
        "item_edit_project_id": {
            "env_var": "DEFAULT_PROJECT_ITEM_EDIT_PROJECT_ID",
            "default": None,
            "type": "int",
        },
        "item_list_owner": {
            "env_var": "DEFAULT_PROJECT_ITEM_LIST_OWNER",
            "default": None,
            "type": "str",
        },
        "item_list_limit": {
            "env_var": "DEFAULT_PROJECT_ITEM_LIST_LIMIT",
            "default": 30,
            "type": "int",
        },
        "item_list_project_id": {
            "env_var": "DEFAULT_PROJECT_ITEM_LIST_PROJECT_ID",
            "default": None,
            "type": "int",
        },
        "item_list_format": {
            "env_var": "DEFAULT_PROJECT_ITEM_LIST_FORMAT",
            "default": "json",
            "type": "str",
        },
        "list_owner": {
            "env_var": "DEFAULT_PROJECT_LIST_OWNER",
            "default": None,
            "type": "str",
        },
        "list_limit": {
            "env_var": "DEFAULT_PROJECT_LIST_LIMIT",
            "default": 30,
            "type": "int",
        },
        "mark_as_template_owner": {
            "env_var": "DEFAULT_PROJECT_MARK_AS_TEMPLATE_OWNER",
            "default": None,
            "type": "str",
        },
        "view_list_owner": {
            "env_var": "DEFAULT_PROJECT_VIEW_LIST_OWNER",
            "default": None,
            "type": "str",
        },
        "view_list_limit": {
            "env_var": "DEFAULT_PROJECT_VIEW_LIST_LIMIT",
            "default": 30,
            "type": "int",
        },
        "view_list_project_id": {
            "env_var": "DEFAULT_PROJECT_VIEW_LIST_PROJECT_ID",
            "default": None,
            "type": "int",
        },
    },
    # Add more capabilities (e.g., 'release') and parameters as needed
}

# Potential future enhancement: Add metadata like 'type' (str, int, list) or 'mandatory'
# 'assignee': {'env_var': 'DEFAULT_ISSUE_ASSIGNEE', 'default': '@me', 'type': 'str'},
# 'limit':    {'env_var': 'DEFAULT_ISSUE_LIST_LIMIT', 'default': 30, 'type': 'int'},
# 'labels':   {'env_var': 'DEFAULT_ISSUE_LABELS', 'default': None, 'type': 'list'},


# Function to get GitHub token (remains the same)
def get_github_token() -> str | None:
    """Retrieve the GitHub token from the environment or auth status.

    Looks in the following places in order:
    1. GITHUB_TOKEN environment variable
    2. GH_TOKEN environment variable
    3. Current gh auth status (if authenticated)

    Returns
    -------
        str: The token or "gh_auth_available" if authenticated via gh CLI
        None: If no token found and not authenticated

    """
    # Check for token in environment variables
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    # If no token in env vars, try to get from gh auth status
    if not token:
        try:
            import subprocess

            # Check if gh is authenticated
            result = subprocess.run(
                ["gh", "auth", "status"], capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                print("gh auth status successful, using existing token")
                # We're authenticated, return a marker value
                return "gh_auth_available"
        except Exception as e:
            print(f"Error checking gh auth status: {e}")

    return token
