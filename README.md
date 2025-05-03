# GitHub Project Manager MCP Server

This is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) server that acts as a wrapper around the GitHub CLI (`gh`), providing access to common GitHub operations like managing issues, pull requests, and projects directly within MCP-compatible clients (e.g., Cursor IDE, Claude IDE).

## Overview

This server allows AI models and tools to interact with GitHub repositories programmatically using the `gh` command-line tool. It exposes specific `gh` commands as MCP tools, enabling automation and integration for GitHub-related tasks.

## Use Cases

*   Automating issue creation, assignment, and management.
*   Managing pull requests (creation, listing, merging).
*   Interacting with GitHub Projects (listing items, adding issues/PRs).
*   Building AI-powered workflows that operate on GitHub repositories.

## Prerequisites

1.  **Docker:** You need [Docker](https://www.docker.com/) installed and running to use the pre-built server image.
2.  **GitHub CLI (`gh`) Authentication:** The server uses the `gh` CLI internally. Before running the container, ensure you have authenticated `gh` with the necessary permissions for the repositories you intend to interact with. The easiest way is often to run `gh auth login` on your host machine. The Docker container will typically mount and use your host's `gh` configuration (`~/.config/gh`).
3.  **GitHub Personal Access Token (PAT):** You **MUST** provide a GitHub Personal Access Token via the `GH_TOKEN` environment variable for the server to authenticate its internal `gh` CLI calls. While mounting the host's `gh` configuration helps, the server relies on this token for reliable authentication within the container's execution context. [Create a GitHub Personal Access Token](https://github.com/settings/personal-access-tokens/new) with appropriate scopes (e.g., `repo`, `project`, `read:org`) for the operations you intend to perform.

## Usage with MCP Clients (Cursor, Claude IDE, etc.)

This server is designed to be run as a Docker container. You do **not** need to clone this repository to use it.

We plan to publish the Docker image to a container registry (e.g., GitHub Container Registry - `ghcr.io`). Replace `<your-docker-image-uri>` in the examples below with the actual image URI once published.

### Configuration in your MCP Client (Example: VS Code User Settings)

Add the following to your client's MCP server configuration (e.g., VS Code `settings.json` or `.vscode/mcp.json`, or the equivalent in your IDE):

```json
{
  // In VS Code settings.json, wrap this whole block in "mcp": { ... }
  "inputs": [
    {
      "type": "promptString",
      "id": "github_token",
      "description": "GitHub Personal Access Token (Required)",
      "password": true
    }
  ],
  "servers": {
    "gh_cli": { // You can name this server entry descriptively
      "command": "docker",
      "args": [
        "run",
        "-i", // Interactive mode for MCP communication
        "--rm", // Remove container on exit
        // Mount gh config directory from host:
        "-v", "${env:HOME}/.config/gh:/home/vscode/.config/gh",
        // Pass GH_TOKEN (Mandatory):
        "-e", "GH_TOKEN=${input:github_token}",
        // (Optional) Pass other config environment variables (see below):
        // "-e", "DEFAULT_ISSUE_ASSIGNEE=@me",
        // "-e", "DEFAULT_PROJECT_TARGET=MyProject",
        // "-e", "DEFAULT_PROJECT_OWNER=my-org",
        "<your-docker-image-uri>" // <-- Replace with the actual Docker image URI
      ],
      // Map environment variables from inputs or define directly:
      "env": {
        // Map the mandatory GH_TOKEN from the input prompt defined above
        "GH_TOKEN": "${input:github_token}",
        // Example direct env var for optional config:
        // "DEFAULT_ISSUE_ASSIGNEE": "@me",
        // "DEFAULT_PROJECT_TARGET": "MyProject",
        // "DEFAULT_PROJECT_OWNER": "my-org"
      }
    }
  }
}
```

**Key Configuration Points:**

*   **`command: "docker"`**: Specifies Docker to run the server.
*   **`args`**:
    *   `run -i --rm`: Standard Docker flags for interactive, temporary containers.
    *   `-v "${env:HOME}/.config/gh:/home/vscode/.config/gh"`: **Crucial step.** Mounts your host's `gh` configuration directory into the container, allowing the server to use your existing `gh` authentication. Adjust the host path (`${env:HOME}/.config/gh`) if your configuration is stored elsewhere. The container path (`/home/vscode/.config/gh`) assumes the container runs as a non-root user like `vscode` (common in dev containers). Adjust if the Docker image uses a different user or path.
    *   `-e VAR=value`: Use this to pass environment variables for configuration (see "Environment Variables" section below).
    *   `<your-docker-image-uri>`: The full path to the Docker image in the registry.
*   **`(Optional) inputs`**: Define prompts if you want the IDE to ask for values like a `GH_TOKEN`.
*   **`(Optional) env`**: Map inputs or define static environment variables to be passed to the container.

Consult your specific MCP client's documentation for the exact configuration format.

## Available Tools

The server exposes the following `gh` command functionalities as MCP tools.

### Issues

*   **mcp_github_create_issue** - Create a new issue (`gh issue create`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `title`: Issue title (string, required)
    *   `body`: Issue body content (string, required)
    *   `issue_type`: Type label to add (e.g., 'feature', 'bugfix') (string, optional)
    *   `assignee`: User to assign (e.g., '@me') (string, optional)
    *   `project`: Project to add the issue to (string, optional)
    *   `labels`: Additional labels to apply (array of strings, optional)

*   **mcp_github_get_issue** - Get details of a specific issue (`gh issue view`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `issue_number`: The number of the issue (number, required)

*   **mcp_github_list_issues** - List issues in a repository (`gh issue list`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `state`: Filter by state ('open', 'closed', 'all') (string, optional)
    *   `assignee`: Filter by assignee (string, optional)
    *   `labels`: Filter by labels (array of strings, optional)
    *   `limit`: Maximum number of issues to return (number, optional)

*   **mcp_github_close_issue** - Close an issue (`gh issue close`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `issue_identifier`: Issue number or URL (number or string, required)
    *   `comment`: Closing comment (string, optional)
    *   `reason`: Closing reason ('completed' or 'not planned') (string, optional)

*   **mcp_github_comment_issue** - Add a comment to an issue (`gh issue comment`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `issue_identifier`: Issue number or URL (number or string, required)
    *   `body`: Comment text (string, optional but required if `body_file` is not set)
    *   `body_file`: File containing comment text (string, optional but required if `body` is not set)

*   **mcp_github_delete_issue** - Delete an issue (`gh issue delete`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `issue_identifier`: Issue number or URL (number or string, required)
    *   `skip_confirmation`: Skip the confirmation prompt (boolean, optional, default: false)

*   **mcp_github_create_issue_branch** - Create a branch from an issue (`gh issue develop`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `issue_identifier`: Issue number or URL (number or string, required)
    *   `branch_name`: Name for the new branch (string, optional)
    *   `checkout`: Checkout the new branch locally (boolean, optional, default: false)
    *   `base_branch`: Base branch to create from (string, optional)

*   **mcp_github_list_issue_linked_branches** - List branches linked to an issue (`gh issue develop --list`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `issue_identifier`: Issue number or URL (number or string, required)

*   **mcp_github_status_issue** - Show issue/PR status for the current branch/repo (`gh issue status`).
    *   *(No parameters)*

*   **mcp_github_transfer_issue** - Transfer an issue to another repository (`gh issue transfer`).
    *   `owner`: Current repository owner (string, required)
    *   `repo`: Current repository name (string, required)
    *   `issue_identifier`: Issue number or URL (number or string, required)
    *   `destination_repo`: Target repository in 'owner/repo' format (string, required)

*   **mcp_github_unlock_issue** - Unlock an issue conversation (`gh issue unlock`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `issue_identifier`: Issue number or URL (number or string, required)

*   **mcp_github_unpin_issue** - Unpin an issue (`gh issue unpin`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `issue_identifier`: Issue number or URL (number or string, required)

*   **mcp_github_edit_issue** - Edit issue metadata (`gh issue edit`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `issue_identifier`: Issue number or URL (number or string, required)
    *   `title`: New title (string, optional)
    *   `body`: New body content (string, optional)
    *   `add_assignees`: Usernames to add as assignees (array of strings, optional)
    *   `remove_assignees`: Usernames to remove as assignees (array of strings, optional)
    *   `add_labels`: Labels to add (array of strings, optional)
    *   `remove_labels`: Labels to remove (array of strings, optional)
    *   `add_projects`: Projects (number or URL) to add the issue to (array of strings, optional)
    *   `remove_projects`: Projects (number or URL) to remove the issue from (array of strings, optional)
    *   `milestone`: Milestone name or number to apply (string or number, optional)

*   **mcp_github_reopen_issue** - Reopen a closed issue (`gh issue reopen`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `issue_identifier`: Issue number or URL (number or string, required)
    *   `comment`: Comment to add upon reopening (string, optional)

*   **mcp_github_pin_issue** - Pin an issue (`gh issue pin`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `issue_identifier`: Issue number or URL (number or string, required)

*   **mcp_github_lock_issue** - Lock an issue conversation (`gh issue lock`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `issue_identifier`: Issue number or URL (number or string, required)
    *   `reason`: Reason for locking ('off-topic', 'resolved', 'spam', 'too heated') (string, optional)

### Pull Requests

*   **mcp_github_create_pull_request** - Create a new pull request (`gh pr create`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `base`: Branch to merge into (string, required)
    *   `head`: Branch containing changes (string, required)
    *   `title`: PR title (string, required)
    *   `body`: PR description (string, optional)
    *   `draft`: Create as draft PR (boolean, optional)
    *   `reviewers`: Usernames or team names for review requests (array of strings, optional)
    *   `pr_labels`: Labels to apply (array of strings, optional)
    *   `pr_project`: Project to add the PR to (string, optional)

*   **mcp_github_list_pull_requests** - List pull requests (`gh pr list`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `pr_state`: Filter by state ('open', 'closed', 'all', 'merged') (string, optional)
    *   `pr_labels`: Filter by labels (array of strings, optional)
    *   `base`: Filter by base branch (string, optional)
    *   `head`: Filter by head branch (string, optional)
    *   `pr_limit`: Maximum number of PRs to return (number, optional)

*   **mcp_github_get_pull_request** - Get details of a specific pull request (`gh pr view --json ...`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `pull_number`: Pull request number (number, required)

*   **mcp_github_merge_pull_request** - Merge a pull request (`gh pr merge`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `pull_number`: Pull request number (number, required)
    *   `merge_method`: Merge method ('merge', 'squash', 'rebase') (string, optional)
    *   `delete_branch`: Delete head branch after merge (boolean, optional, default: true based on config)
    *   `commit_title`: Title for merge commit (string, optional)
    *   `commit_message`: Body for merge commit (string, optional, cannot use with rebase)

*   **mcp_github_checks_pull_request** - Show status of PR checks (`gh pr checks`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `pr_identifier`: PR number, URL, or branch name (number or string, optional, defaults to current branch)
    *   `fail_fast`: Exit early if any check fails (boolean, optional, default: false)
    *   `required`: Only show required checks (boolean, optional, default: false)

*   **mcp_github_checkout_pull_request** - Check out a PR locally (`gh pr checkout`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `pr_identifier`: PR number, URL, or branch name (number or string, required)
    *   `checkout_branch_name`: Name for the local branch (string, optional)
    *   `detach`: Checkout commit SHA instead of branch (boolean, optional, default: false)
    *   `recurse_submodules`: Update submodules (boolean, optional, default: false)
    *   `force`: Force checkout, discarding local changes (boolean, optional, default: false)

*   **mcp_github_close_pull_request** - Close a pull request (`gh pr close`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `pr_identifier`: PR number, URL, or branch name (number or string, required)
    *   `comment`: Closing comment (string, optional)
    *   `delete_branch`: Delete the head branch after closing (boolean, optional, default: false)

*   **mcp_github_comment_pull_request** - Add a comment to a PR (`gh pr comment`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `pr_identifier`: PR number, URL, or branch name (number or string, required)
    *   `body`: Comment text (string, optional but required if `body_file` is not set)
    *   `body_file`: File containing comment text (string, optional but required if `body` is not set)

*   **mcp_github_diff_pull_request** - View changes in a PR (`gh pr diff`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `pr_identifier`: PR number, URL, or branch name (number or string, optional, defaults to current branch)
    *   `color`: Use color in output ('always', 'never', 'auto') (string, optional)
    *   `patch`: Display diff in patch format (boolean, optional, default: false)
    *   `name_only`: Show only names of changed files (boolean, optional, default: false)

*   **mcp_github_edit_pull_request** - Edit pull request metadata (`gh pr edit`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `pr_identifier`: PR number, URL, or branch name (number or string, required)
    *   `title`: New title (string, optional)
    *   `body`: New body content (string, optional)
    *   `base_branch`: New base branch (string, optional)
    *   `milestone`: Milestone name or number to apply (string or number, optional)
    *   `add_assignees`: Usernames to add as assignees (array of strings, optional)
    *   `remove_assignees`: Usernames to remove as assignees (array of strings, optional)
    *   `add_labels`: Labels to add (array of strings, optional)
    *   `remove_labels`: Labels to remove (array of strings, optional)
    *   `add_projects`: Projects (number or URL) to add the PR to (array of strings, optional)
    *   `remove_projects`: Projects (number or URL) to remove the PR from (array of strings, optional)
    *   `add_reviewers`: Usernames or team names to add as reviewers (array of strings, optional)
    *   `remove_reviewers`: Usernames or team names to remove as reviewers (array of strings, optional)

*   **mcp_github_lock_pull_request** - Lock PR conversation (`gh pr lock`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `pr_identifier`: PR number, URL, or branch name (number or string, required)
    *   `reason`: Reason for locking ('off-topic', 'resolved', 'spam', 'too heated') (string, optional)

*   **mcp_github_ready_pull_request** - Mark a PR as ready for review (`gh pr ready`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `pr_identifier`: PR number, URL, or branch name (number or string, required)

*   **mcp_github_reopen_pull_request** - Reopen a closed PR (`gh pr reopen`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `pr_identifier`: PR number, URL, or branch name (number or string, required)
    *   `comment`: Comment to add upon reopening (string, optional)

*   **mcp_github_review_pull_request** - Add a review to a PR (`gh pr review`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `pr_identifier`: PR number, URL, or branch name (number or string, required)
    *   `action`: Review action ('approve', 'request-changes', 'comment') (string, required)
    *   `body`: Review comment text (string, optional but required if `body_file` is not set and action is 'comment' or 'request-changes')
    *   `body_file`: File containing review comment text (string, optional but required if `body` is not set and action is 'comment' or 'request-changes')

*   **mcp_github_status_pull_request** - Show status of relevant PRs (`gh pr status`).
    *   *(No parameters)*

*   **mcp_github_unlock_pull_request** - Unlock PR conversation (`gh pr unlock`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `pr_identifier`: PR number, URL, or branch name (number or string, required)

*   **mcp_github_view_pull_request** - View a PR in the terminal or browser (`gh pr view`).
    *   `owner`: Repository owner (string, required)
    *   `repo`: Repository name (string, required)
    *   `pr_identifier`: PR number, URL, or branch name (number or string, required)
    *   `comments`: View PR comments (boolean, optional, default: false)
    *   `web`: Open PR in the browser (boolean, optional, default: false)

### Projects

*   **mcp_github_copy_project** - Copy a project (`gh project copy`).
    *   `project_id`: Project number or URL to copy (number or string, required)
    *   `target_owner`: Owner (user or org) to copy the project to (string, required)
    *   `new_title`: New title for the copied project (string, optional)
    *   `source_owner`: Owner of the source project (if not inherent in `project_id` URL) (string, optional)

*   **mcp_github_create_project** - Create a project (`gh project create`).
    *   `owner`: Owner (user or org) for the new project (string, required)
    *   `title`: Title for the new project (string, required)

*   **mcp_github_delete_project** - Delete a project (`gh project delete`).
    *   `project_id`: Project number or URL to delete (number or string, required)
    *   `owner`: Owner (user or org) of the project (if not inherent in `project_id` URL) (string, optional)

*   **mcp_github_edit_project** - Edit project metadata (`gh project edit`).
    *   `project_id`: Project number or URL to edit (number or string, required)
    *   `owner`: Owner (user or org) of the project (string, optional)
    *   `title`: New title (string, optional)
    *   `description`: New description (string, optional)
    *   `visibility`: New visibility ('public' or 'private') (string, optional)
    *   `readme`: New README content (string, optional)

*   **mcp_github_list_projects** - List projects (`gh project list`).
    *   `owner`: Owner (user or org) to list projects for (string, optional)
    *   `limit`: Maximum number of projects to return (number, optional)
    *   `closed`: Include closed projects (boolean, optional, default: false)

*   **mcp_github_view_project** - View project details (`gh project view`).
    *   `project_id`: Project number or URL to view (number or string, required)
    *   `owner`: Owner (user or org) of the project (string, optional)
    *   `web`: Open project in the browser (boolean, optional, default: false)

### Project Fields

*   **mcp_github_create_project_field** - Create a field in a project (`gh project field-create`).
    *   `project_id`: Project number or URL (number or string, required)
    *   `name`: Name for the new field (string, required)
    *   `owner`: Owner (user or org) of the project (string, optional)
    *   `data_type`: Data type ('TEXT', 'NUMBER', 'DATE', 'SINGLE_SELECT', 'ITERATION') (string, optional, default: 'TEXT')
    *   `single_select_options`: Comma-separated options (required if `data_type` is 'SINGLE_SELECT') (array of strings, optional)

*   **mcp_github_delete_project_field** - Delete a field from a project (`gh project field-delete`).
    *   `field_id`: ID of the field to delete (string, required)
    *   `project_id`: Project number or URL (not used by `gh` command but kept for potential future API changes) (number or string, optional)

*   **mcp_github_list_project_fields** - List fields in a project (`gh project field-list`).
    *   `project_id`: Project number or URL (number or string, required)
    *   `owner`: Owner (user or org) of the project (string, optional)
    *   `limit`: Maximum number of fields to return (number, optional)

### Project Items

*   **mcp_github_add_project_item** - Add an issue or PR to a project (`gh project item-add`).
    *   `project_id`: Project number or URL to add item to (number or string, required)
    *   `owner`: Owner (user or org) of the project (string, optional)
    *   `issue_id`: URL or ID of the issue to add (string, optional, required if `pull_request_id` not set)
    *   `pull_request_id`: URL or ID of the pull request to add (string, optional, required if `issue_id` not set)

*   **mcp_github_archive_project_item** - Archive or unarchive an item (`gh project item-archive`).
    *   `item_id`: ID of the item to archive/unarchive (string, required)
    *   `project_id`: Project number or URL containing the item (number or string, optional)
    *   `owner`: Owner (user or org) of the project (string, optional)
    *   `undo`: Unarchive the item instead of archiving (boolean, optional, default: false)

*   **mcp_github_delete_project_item** - Delete an item from a project (`gh project item-delete`).
    *   `item_id`: ID of the item to delete (string, required)
    *   `project_id`: Project number or URL containing the item (number or string, optional)
    *   `owner`: Owner (user or org) of the project (string, optional)

*   **mcp_github_edit_project_item** - Edit item field values (`gh project item-edit`).
    *   `item_id`: ID of the item to edit (string, required)
    *   `project_id`: Project number or URL containing the item (number or string, optional)
    *   `owner`: Owner (user or org) of the project (string, optional)
    *   `field_id`: ID of the field to set or clear (string, required unless `--clear` is used in a future unsupported way)
    *   `clear`: Clear the value of the specified field (boolean, optional, default: false)
    *   `text_value`: Set text field value (string, optional, requires `field_id`)
    *   `number_value`: Set number field value (number, optional, requires `field_id`)
    *   `date_value`: Set date field value (YYYY-MM-DD format) (string, optional, requires `field_id`)
    *   `single_select_option_id`: Set single-select option ID (string, optional, requires `field_id`)
    *   `iteration_id`: Set iteration ID ('@current', '@next', or ID) (string, optional, requires `field_id`)

*   **mcp_github_list_project_items** - List items in a project (`gh project item-list`).
    *   `project_id`: Project number or URL (number or string, required)
    *   `owner`: Owner (user or org) of the project (string, optional)
    *   `limit`: Maximum number of items to return (number, optional)

### Repositories

*   **mcp_github_list_repos** - List repositories for an owner (`gh repo list`).
    *   `owner`: User or organization to list repositories for (string, required)
    *   `limit`: Maximum number of repositories to return (number, optional)
    *   `visibility`: Filter by visibility ('public', 'private', 'internal') (string, optional)
    *   `fork`: Filter for forks only (boolean, optional, default: false)
    *   `source`: Filter for non-forks only (boolean, optional, default: false)
    *   `language`: Filter by primary language (string, optional)
    *   `topic`: Filter by topic (string, optional)

Refer to the specific tool function definitions within your MCP client for detailed return values and potential exceptions.

## Environment Variables for Configuration

You can configure default behaviors or provide necessary context by setting environment variables when running the Docker container (using `-e VAR=value`). These correspond to optional parameters in the tool functions.

**General:**

*   `GH_TOKEN`: **(Mandatory)** Your GitHub Personal Access Token used for authenticating all `gh` CLI commands executed by the server.
*   `MCP_GITHUB_DEFAULT_BASE_BRANCH`: Default base branch for operations like `gh issue develop`.

**Issues (`gh issue ...`):**

*   `DEFAULT_ISSUE_ASSIGNEE`: Default user to assign issues to (e.g., `@me`). Default: `@me`.
*   `DEFAULT_ISSUE_PROJECT`: Default project to add new issues to. Default: `None`.
*   `DEFAULT_ISSUE_LABELS`: Comma-separated list of default labels for new issues. Default: `None`.
*   `DEFAULT_ISSUE_TYPE`: Default type for `gh issue create --type` (e.g., `bug`, `enhancement`). Default: `None`.
*   `DEFAULT_ISSUE_LIST_STATE`: Default state for `gh issue list` (`open`, `closed`, `all`). Default: `open`.
*   `DEFAULT_ISSUE_LIST_LIMIT`: Default limit for `gh issue list`. Default: `30`.
*   `DEFAULT_ISSUE_EDIT_MILESTONE`: Default milestone for `gh issue edit`. Default: `None`.

**Pull Requests (`gh pr ...`):**

*   `DEFAULT_PR_DRAFT`: Set to `true` to create PRs as drafts by default. Default: `false`.
*   `DEFAULT_PR_ASSIGNEES`: Comma-separated list of default assignees for new PRs (e.g., `@me`). Default: `@me`.
*   `DEFAULT_PR_REVIEWERS`: Comma-separated list of default reviewers for new PRs. Default: `None`.
*   `DEFAULT_PR_LABELS`: Comma-separated list of default labels for new PRs. Default: `None`.
*   `DEFAULT_PR_PROJECT`: Default project to add new PRs to. Default: `None`.
*   `DEFAULT_PR_LIST_STATE`: Default state for `gh pr list` (`open`, `closed`, `all`). Default: `open`.
*   `DEFAULT_PR_LIST_LIMIT`: Default limit for `gh pr list`. Default: `30`.
*   `DEFAULT_PR_MERGE_METHOD`: Default merge method for `gh pr merge` (`merge`, `squash`, `rebase`). Default: `merge`.
*   `DEFAULT_PR_DELETE_BRANCH`: Set to `true` to delete the head branch after merging by default. Default: `true`.

**Projects (`gh project ...` / `gh project item-...`):**

*   `DEFAULT_PROJECT_OWNER`: Default owner (`@me`, `org-name`) for project operations where owner is ambiguous. Default: `None`.
*   `DEFAULT_PROJECT_TARGET`: Default project number or title for adding items. Default: `None`.
*   `DEFAULT_PROJECT_ITEM_PRIORITY`: Default priority for new project items (if applicable). Default: `Medium`.
*   `DEFAULT_PROJECT_ITEM_STATUS`: Default status for new project items (if applicable). Default: `to-do`.
*   `DEFAULT_PROJECT_COPY_SOURCE_OWNER`: Default source owner for `gh project copy`. Default: `None`.
*   `DEFAULT_PROJECT_DELETE_OWNER`: Default owner for `gh project delete`. Default: `None`.
*   `DEFAULT_PROJECT_EDIT_OWNER`: Default owner for `gh project edit`. Default: `None`.
*   `DEFAULT_PROJECT_FIELD_OWNER`: Default owner for `gh project field-create/delete`. Default: `None`.
*   `DEFAULT_PROJECT_FIELD_LIST_OWNER`: Default owner for `gh project field-list`. Default: `None`.
*   `DEFAULT_PROJECT_FIELD_LIST_LIMIT`: Default limit for `gh project field-list`. Default: `30`.
*   `DEFAULT_PROJECT_ITEM_ADD_OWNER`: Default owner for `gh project item-add`. Default: `None`.
*   `DEFAULT_PROJECT_ITEM_ARCHIVE_OWNER`: Default owner for `gh project item-archive`. Default: `None`.
*   `DEFAULT_PROJECT_ITEM_ARCHIVE_PROJECT_ID`: Default project ID for `gh project item-archive`. Default: `None`.
*   `DEFAULT_PROJECT_ITEM_DELETE_OWNER`: Default owner for `gh project item-delete`. Default: `None`.
*   `DEFAULT_PROJECT_ITEM_DELETE_PROJECT_ID`: Default project ID for `gh project item-delete`. Default: `None`.
*   `DEFAULT_PROJECT_ITEM_EDIT_OWNER`: Default owner for `gh project item-edit`. Default: `None`.
*   `DEFAULT_PROJECT_ITEM_EDIT_PROJECT_ID`: Default project ID for `gh project item-edit`. Default: `None`.
*   `DEFAULT_PROJECT_ITEM_LIST_OWNER`: Default owner for `gh project item-list`. Default: `None`.
*   `DEFAULT_PROJECT_ITEM_LIST_LIMIT`: Default limit for `gh project item-list`. Default: `30`.
*   `DEFAULT_PROJECT_ITEM_LIST_PROJECT_ID`: Default project ID for `gh project item-list`. Default: `None`.
*   `DEFAULT_PROJECT_ITEM_LIST_FORMAT`: Default format for `gh project item-list`. Default: `json`.
*   `DEFAULT_PROJECT_LIST_OWNER`: Default owner for `gh project list`. Default: `None`.
*   `DEFAULT_PROJECT_LIST_LIMIT`: Default limit for `gh project list`. Default: `30`.
*   `DEFAULT_PROJECT_MARK_AS_TEMPLATE_OWNER`: Default owner for `gh project mark-as-template`. Default: `None`.
*   `DEFAULT_PROJECT_VIEW_LIST_OWNER`: Default owner for `gh project view list`. Default: `None`.
*   `DEFAULT_PROJECT_VIEW_LIST_LIMIT`: Default limit for `gh project view list`. Default: `30`.
*   `DEFAULT_PROJECT_VIEW_LIST_PROJECT_ID`: Default project ID for `gh project view list`. Default: `None`.

**Repositories (`gh repo ...`):**

*   `DEFAULT_REPO_LIST_LIMIT`: Default limit for `gh repo list`. Default: `30`.
*   `DEFAULT_REPO_LIST_VISIBILITY`: Default visibility filter for `gh repo list` (`public`, `private`, `internal`). Default: `None`.

## Development

Instructions for setting up a local development environment if you wish to contribute or modify the server.

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd gh-project-manager-mcp
    ```
2.  **Install Dependencies:** Uses Poetry.
    ```bash
    poetry install
    ```
    (If you have `uv` installed via `pipx install uv`, you can potentially use `poetry config virtualenvs.prefer-active-python true && poetry run uv pip sync pyproject.toml` for faster installs).
3.  **Activate Environment:**
    ```bash
    poetry shell
    ```
4.  **Run the Server:**
    ```bash
    python -m src.gh_project_manager_mcp.server
    ```
5.  **Testing:** Uses `pytest`. Run tests with:
    ```bash
    make test
    # or directly
    poetry run pytest
    ```
6.  **Linting/Formatting:** Uses `ruff`.
    ```bash
    make format
    make lint
    # or directly
    poetry run ruff format .
    poetry run ruff check . --fix
    ```
7.  **Building Docker Image:**
    ```bash
    make build-docker
    ```

## Contributing

Contributions are welcome! Please follow standard GitHub flow (fork, branch, PR) and ensure tests and linters pass.
