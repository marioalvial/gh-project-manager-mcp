# GitHub Project Manager MCP Server

[![Python Version](https://img.shields.io/pypi/pyversions/gh-project-manager-mcp.svg)](https://pypi.org/project/gh-project-manager-mcp/) <!-- Placeholder: Add actual PyPI badge when published -->
[![PyPI version](https://badge.fury.io/py/gh-project-manager-mcp.svg)](https://badge.fury.io/py/gh-project-manager-mcp) <!-- Placeholder: Add actual PyPI badge when published -->

An MCP (Model Context Protocol) server wrapping the GitHub CLI (`gh`) to provide tools for managing GitHub resources like issues, pull requests, and projects.

## Overview

This project exposes various `gh` commands as MCP tools, allowing language models or other MCP clients to interact with GitHub programmatically. It aims to provide a robust and configurable interface for automating GitHub workflows.

## Features

Currently implemented capabilities include:

*   **Issues:** Create, view, list, close, comment, delete, create branches, list linked branches, get status, transfer, unlock, unpin.
*   **Pull Requests:** Create, view, list, close, comment, edit, merge, review, diff, checkout, ready, create-review, list-reviews, reopen, checks.
*   **Projects:** Create, close, copy, delete, edit, list, view, field-create, field-delete, field-list, item-add, item-archive, item-create, item-delete, item-edit, item-list.
*   **Repositories:** List repositories.
*   **(And potentially others as development continues)**

## Installation

This project uses Poetry for dependency management and packaging.

**1. Build the Package:**

Navigate to the project root directory and run:

```bash
poetry build
```

This will create a `dist/` directory containing the build artifacts (wheel and source distribution).

**2. Install the Package:**

You can install the package using `pip`. Choose one of the following methods:

*   **From Local Build:**
    ```bash
    # Replace <version> with the actual version built
    pip install dist/gh_project_manager_mcp-<version>-py3-none-any.whl
    ```

*   **From PyPI (Once Published):**
    ```bash
    pip install gh-project-manager-mcp
    ```

*   **Directly from Git (for development/testing):**
    ```bash
    pip install git+https://github.com/<your-username>/gh_project_manager_mcp.git@main # Or specify a branch/tag
    ```

## Running the Server

Once installed, the server can be started using the console script added during installation:

```bash
gh-pm-mcp-server
```

The server will start and listen for incoming MCP connections. By default, `FastMCP` usually listens on `localhost` and a specific port (e.g., 8080), which will be printed to the console on startup.

```
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
Registering tools...
Registering GitHub issue tools...
GitHub issue tools registered.
Registering GitHub pull request tools...
GitHub pull request tools registered.
Registering GitHub project tools...
GitHub project tools registered.
Tools registered successfully.
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Your MCP client will need to be configured to connect to the host and port the server is listening on (e.g., `http://127.0.0.1:8080`).

## Authentication

The server uses the GitHub CLI (`gh`) internally. Authentication is handled automatically by `gh`. Ensure you have authenticated `gh` in the environment where the server is running:

```bash
gh auth login
```

Alternatively, you can set the `GH_TOKEN` environment variable with a GitHub Personal Access Token (PAT) that has the necessary scopes (e.g., `repo`, `project`, `read:org`).

## Configuration

Many tool parameters can be configured using environment variables or have default values. The resolution precedence is:

1.  **Runtime Value:** Value provided directly in the tool call.
2.  **Environment Variable:** Value set in the server's environment.
3.  **Default Value:** Predefined default in the server configuration.

### Environment Variables & Defaults

The following table lists configurable parameters, their corresponding environment variables, and default values:

| Capability     | Parameter               | Environment Variable                    | Default Value   | Type   | Notes                                           |
|----------------|-------------------------|-----------------------------------------|-----------------|--------|-------------------------------------------------|
| **Issue**      | `assignee`              | `DEFAULT_ISSUE_ASSIGNEE`                | `@me`           | `str`  |                                                 |
|                | `project`               | `DEFAULT_ISSUE_PROJECT`                 | `None`          | `str`  |                                                 |
|                | `labels`                | `DEFAULT_ISSUE_LABELS`                  | `None`          | `list` | Comma-separated in env var                      |
|                | `issue_type`            | `DEFAULT_ISSUE_TYPE`                    | `None`          | `str`  | Special handling for `feature`/`bugfix` labels    |
|                | `state` (list)          | `DEFAULT_ISSUE_LIST_STATE`              | `open`          | `str`  |                                                 |
|                | `limit` (list)          | `DEFAULT_ISSUE_LIST_LIMIT`              | `30`            | `int`  |                                                 |
|                | `close_comment`         | `None`                                  | `None`          | `str`  |                                                 |
|                | `close_reason`          | `None`                                  | `None`          | `str`  | Valid: `completed`, `not planned`               |
|                | `comment_body`          | `None`                                  | `None`          | `str`  | For `gh issue comment`                          |
|                | `comment_body_file`     | `None`                                  | `None`          | `str`  | For `gh issue comment`                          |
|                | `develop_base_branch`   | `MCP_GITHUB_DEFAULT_BASE_BRANCH`        | `None`          | `str`  | For `gh issue develop`                          |
|                | `edit_milestone`        | `DEFAULT_ISSUE_EDIT_MILESTONE`          | `None`          | `str`  | For `gh issue edit`                             |
| **Pull Req.**  | `assignee`              | `DEFAULT_PR_ASSIGNEE`                   | `@me`           | `str`  |                                                 |
|                | `project`               | `DEFAULT_PR_PROJECT`                    | `None`          | `str`  |                                                 |
|                | `reviewers`             | `DEFAULT_PR_REVIEWERS`                  | `None`          | `list` | Comma-separated in env var                      |
|                | `labels`                | `DEFAULT_PR_LABELS`                     | `None`          | `list` | Comma-separated in env var                      |
|                | `body` (create)         | `None`                                  | `""`            | `str`  |                                                 |
|                | `close_comment`         | `DEFAULT_PR_CLOSE_COMMENT`              | `None`          | `str`  |                                                 |
|                | `comment_body`          | `None`                                  | `None`          | `str`  | For `gh pr comment`                             |
|                | `comment_body_file`     | `None`                                  | `None`          | `str`  | For `gh pr comment`                             |
|                | `edit_milestone`        | `DEFAULT_PR_EDIT_MILESTONE`             | `None`          | `str`  | For `gh pr edit`                                |
|                | `list_state`            | `DEFAULT_PR_LIST_STATE`                 | `open`          | `str`  |                                                 |
|                | `list_limit`            | `DEFAULT_PR_LIST_LIMIT`                 | `30`            | `int`  |                                                 |
|                | `author` (list)         | `DEFAULT_PR_LIST_AUTHOR`                | `None`          | `str`  |                                                 |
|                | `base` (list)           | `DEFAULT_PR_LIST_BASE`                  | `None`          | `str`  |                                                 |
|                | `head` (list)           | `DEFAULT_PR_LIST_HEAD`                  | `None`          | `str`  |                                                 |
|                | `merge_body`            | `None`                                  | `None`          | `str`  | Placeholder                                     |
|                | `review_body`           | `None`                                  | `None`          | `str`  | Placeholder                                     |
|                | `review_body_file`      | `None`                                  | `None`          | `str`  | Placeholder                                     |
| **ProjectItem**| `project_owner`         | `DEFAULT_PROJECT_OWNER`                 | `None`          | `str`  | For adding items                                |
|                | `project` (target)      | `DEFAULT_PROJECT_TARGET`                | `None`          | `str`  | For adding items                                |
|                | `priority`              | `DEFAULT_PROJECT_ITEM_PRIORITY`         | `Medium`        | `str`  | Potential future tool use                       |
|                | `status`                | `DEFAULT_PROJECT_ITEM_STATUS`           | `to-do`         | `str`  | Potential future tool use                       |
| **Repo**       | `limit` (list)          | `DEFAULT_REPO_LIST_LIMIT`               | `30`            | `int`  |                                                 |
|                | `visibility` (list)     | `DEFAULT_REPO_LIST_VISIBILITY`          | `None`          | `str`  |                                                 |
| **Project**    | `copy_source_owner`     | `DEFAULT_PROJECT_COPY_SOURCE_OWNER`     | `None`          | `str`  |                                                 |
|                | `delete_owner`          | `DEFAULT_PROJECT_DELETE_OWNER`          | `None`          | `str`  |                                                 |
|                | `edit_owner`            | `DEFAULT_PROJECT_EDIT_OWNER`            | `None`          | `str`  |                                                 |
|                | `field_owner`           | `DEFAULT_PROJECT_FIELD_OWNER`           | `None`          | `str`  | For `field-create`, `field-delete`              |
|                | `field_list_owner`      | `DEFAULT_PROJECT_FIELD_LIST_OWNER`      | `None`          | `str`  |                                                 |
|                | `field_list_limit`      | `DEFAULT_PROJECT_FIELD_LIST_LIMIT`      | `30`            | `int`  |                                                 |
|                | `item_add_owner`        | `DEFAULT_PROJECT_ITEM_ADD_OWNER`        | `None`          | `str`  |                                                 |
|                | `item_archive_owner`    | `DEFAULT_PROJECT_ITEM_ARCHIVE_OWNER`    | `None`          | `str`  |                                                 |
|                | `item_archive_project_id`| `DEFAULT_PROJECT_ITEM_ARCHIVE_PROJECT_ID`| `None`          | `int`  |                                                 |
|                | `item_delete_owner`     | `DEFAULT_PROJECT_ITEM_DELETE_OWNER`     | `None`          | `str`  |                                                 |
|                | `item_delete_project_id` | `DEFAULT_PROJECT_ITEM_DELETE_PROJECT_ID` | `None`          | `int`  |                                                 |
|                | `item_edit_owner`       | `DEFAULT_PROJECT_ITEM_EDIT_OWNER`       | `None`          | `str`  |                                                 |
|                | `item_edit_project_id`  | `DEFAULT_PROJECT_ITEM_EDIT_PROJECT_ID`  | `None`          | `int`  |                                                 |
|                | `item_list_owner`       | `DEFAULT_PROJECT_ITEM_LIST_OWNER`       | `None`          | `str`  |                                                 |
|                | `item_list_limit`       | `DEFAULT_PROJECT_ITEM_LIST_LIMIT`       | `30`            | `int`  |                                                 |
|                | `list_owner`            | `DEFAULT_PROJECT_LIST_OWNER`            | `None`          | `str`  |                                                 |
|                | `list_limit`            | `DEFAULT_PROJECT_LIST_LIMIT`            | `30`            | `int`  |                                                 |
|                | `view_owner`            | `DEFAULT_PROJECT_VIEW_OWNER`            | `None`          | `str`  |                                                 |

*(Note: `None` default means the parameter is truly optional unless explicitly required by the underlying `gh` command. For list types set via environment variable, use comma-separated values, e.g., `DEFAULT_ISSUE_LABELS="bug,docs"*)

## Development

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/<your-username>/gh_project_manager_mcp.git
    cd gh_project_manager_mcp
    ```
2.  **Install dependencies (including dev):**
    ```bash
    poetry install --all-extras
    ```
3.  **Run tests:**
    ```bash
    poetry run pytest
    ```
4.  **Run linters/formatters (e.g., black):**
    ```bash
    poetry run black .
    ```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

<!-- Choose and add your license here, e.g., MIT -->
This project is licensed under the MIT License. See the LICENSE file for details.
