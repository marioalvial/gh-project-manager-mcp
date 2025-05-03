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
