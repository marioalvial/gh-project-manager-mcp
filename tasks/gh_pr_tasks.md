# GH PR Commands Implementation

Tracking implementation status for `gh pr` subcommands as MCP tools.

## Completed Tasks

- [x] `gh pr create` (_create_github_pull_request_impl)
- [x] Add tests for `gh pr create`
- [x] `gh pr checks`
- [x] Add tests for `gh pr checks`
- [x] `gh pr checkout`
- [x] Add tests for `gh pr checkout`
- [x] `gh pr close`
- [x] Add tests for `gh pr close`
- [x] `gh pr edit`
- [x] Add tests for `gh pr edit`
- [x] `gh pr list`
- [x] Add tests for `gh pr list`
- [x] `gh pr lock`
- [x] Add tests for `gh pr lock`
- [x] `gh pr merge`
- [x] Add tests for `gh pr merge`
- [x] `gh pr ready`
- [x] Add tests for `gh pr ready`
- [x] `gh pr reopen`
- [x] Add tests for `gh pr reopen`
- [x] `gh pr review`
- [x] Add tests for `gh pr review`

## In Progress Tasks

*(Ordered list - complete sequentially)*
- [x] Add tests for `gh pr comment`

## Future Tasks

*(Ordered list - complete sequentially)*
- [x] Add tests for `gh pr diff`
- [x] Add tests for `gh pr status`
- [x] Add tests for `gh pr unlock`
- [x] Add tests for `gh pr view`

## Implementation Plan

- Each subcommand will be implemented as a private function (`_impl`) in `src/gh_project_manager_mcp/tools/pull_requests.py`.
- Corresponding `TOOL_PARAM_CONFIG` entries will be added in `src/gh_project_manager_mcp/config.py`.
- Each implementation will use `resolve_param` and `run_gh_command`.
- Return values will be standardized.
- New tools will be registered in `src/gh_project_manager_mcp/tools/pull_requests.py:init_tools`.
- Comprehensive unit tests will be added in `tests/tools/test_pull_requests.py`.

### Relevant Files

- ✅ `src/gh_project_manager_mcp/tools/pull_requests.py` - Tool implementations
- ✅ `src/gh_project_manager_mcp/config.py` - Parameter configuration
- ✅ `src/gh_project_manager_mcp/utils/gh_utils.py` - Core helpers
- ✅ `tests/tools/test_pull_requests.py` - Unit tests (partially complete) 