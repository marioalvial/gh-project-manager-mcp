# GH Issue Commands Implementation

Tracking implementation status for `gh issue` subcommands as MCP tools.

## Completed Tasks

- [x] `gh issue create` (_create_github_issue_impl)
- [x] Add tests for `gh issue create`
- [x] `gh issue list` (_list_github_issues_impl)
- [x] Add tests for `gh issue list`
- [x] `gh issue view <number>` (_get_github_issue_impl)
- [x] Add tests for `gh issue view`
- [x] `gh issue close` (_close_github_issue_impl)
- [x] Add tests for `gh issue close`
- [x] `gh issue comment` (_comment_github_issue_impl)
- [x] Add tests for `gh issue comment`
- [x] `gh issue delete` (_delete_github_issue_impl)
- [x] Add tests for `gh issue delete`
- [x] `gh issue develop` (Create branch, list linked branches)
- [x] Add tests for `gh issue develop` (Create branch, list linked branches)
- [x] `gh issue develop` (Complete implementation: checkout, other flags?)
- [x] Add tests for `gh issue develop` (Complete implementation)
- [x] `gh issue edit` (Might require editor interaction handling or alternative approach)
- [x] Add tests for `gh issue edit`
- [x] `gh issue lock`
- [x] Add tests for `gh issue lock`
- [x] `gh issue pin`
- [x] Add tests for `gh issue pin`
- [x] `gh issue reopen`
- [x] Add tests for `gh issue reopen`
- [x] `gh issue status`
- [x] Add tests for `gh issue status`
- [x] `gh issue transfer`
- [x] Add tests for `gh issue transfer`
- [x] `gh issue unlock`
- [x] Add tests for `gh issue unlock`
- [x] `gh issue unpin`
- [x] Add tests for `gh issue unpin`
- [ ] `gh issue duplicate` (N/A - Command does not exist)
- [ ] Add tests for `gh issue duplicate` (N/A)

## In Progress Tasks

*(Ordered list - complete sequentially)*
# No tasks in progress

## Future Tasks

*(Ordered list - complete sequentially)*
# All issue commands implemented

## Implementation Plan

- Each subcommand will be implemented as a private function (`_impl`) in `src/gh_project_manager_mcp/tools/issues.py`.
- Corresponding `TOOL_PARAM_CONFIG` entries will be added in `src/gh_project_manager_mcp/config.py` for optional parameters, ensuring `'type'` is specified.
- Each implementation will use `resolve_param` for configurable parameters and `run_gh_command` for execution.
- Return values will be standardized (JSON dict/list for success, error dict `{"error": ...}` on failure).
- New tools will be registered in `src/gh_project_manager_mcp/tools/issues.py:init_tools`.
- Comprehensive unit tests will be added in `tests/tools/test_issues.py` following the GWT pattern and testing parameter resolution, success cases, and error handling.

### Relevant Files

- `src/gh_project_manager_mcp/tools/issues.py` - Tool implementations
- `src/gh_project_manager_mcp/config.py` - Parameter configuration
- `src/gh_project_manager_mcp/utils/gh_utils.py` - Core helpers (`run_gh_command`, `resolve_param`)
- `tests/tools/test_issues.py` - Unit tests