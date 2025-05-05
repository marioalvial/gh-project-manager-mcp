# GitHub Project Manager MCP

Um servidor MCP (Model Context Protocol) para gerenciar projetos no GitHub.

## Descrição

Este projeto implementa um servidor MCP especializado em operações de gerenciamento de projetos GitHub, oferecendo integração com o GitHub CLI (`gh`) para tarefas comuns como:

- Gerenciamento de issues
- Gerenciamento de pull requests
- Futuramente: Integração com GitHub Projects

## Uso com Docker

A imagem Docker é publicada automaticamente no GitHub Container Registry a cada release:

```
docker run -i --rm -e GH_TOKEN=seu_token ghcr.io/marioalvial/gh-project-manager-mcp
```

## Configuração do MCP em Cursor

Para usar este MCP com o Cursor, adicione a seguinte configuração ao seu `.cursor/mcp.json`:

```json
"gh-project-manager": {
  "command": "docker",
  "args": [
    "run",
    "-i",
    "--rm",
    "-e",
    "GH_TOKEN",
    "ghcr.io/marioalvial/gh-project-manager-mcp"
  ],
  "env": {
    "GH_TOKEN": "seu_token_github"
  }
}
```

## Versionamento

Este projeto usa [Semantic Versioning](https://semver.org/) e libera automaticamente novas versões baseadas nos padrões de commit.

# Integration Tests

This project includes a comprehensive suite of integration tests that verify the functionality of our GitHub MCP tools with the actual GitHub API. These tests create and manage real GitHub resources during test execution and clean up afterward.

## Running Integration Tests

To run the integration tests, you'll need a GitHub token with appropriate permissions:

1. Create a GitHub personal access token with at least these scopes: `repo`, `project`
2. Create a `.env` file in the project root with the following content:
   ```bash
   GH_INTEGRATION_TEST_TOKEN=your_github_token_here
   GH_INTEGRATION_TEST_OWNER=marioalvial  # or your own username/organization
   GH_INTEGRATION_TEST_REPO=gh-project-manager-mcp  # or your own repository
   GH_INTEGRATION_TEST_PROJECT_ID=your_project_id  # required for project tests
   ```
3. Run the integration tests:
   ```bash
   make function-integration-test
   ```

## Test Approach

The integration tests use direct function calls to the implementation functions, bypassing the MCP protocol layer to focus on the core GitHub CLI interactions. This approach ensures that:

1. Our tool implementations correctly interact with the GitHub CLI commands
2. Resource creation and cleanup work as expected
3. Error handling is robust across various scenarios, including token permission limitations

The tests are designed to handle various GitHub API limitations and token permission scenarios, automatically skipping or adapting tests that require permissions not available to the provided token.

Note: The tests create and manage real GitHub resources (issues, PRs, branches, etc.), so make sure to use a test repository to avoid clutter in production repositories.

Test line for pull request testing - update for PR testing.
