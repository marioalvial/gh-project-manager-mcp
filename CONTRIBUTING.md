# Contributing to GitHub Project Manager MCP

Thank you for your interest in contributing to the GitHub Project Manager MCP! This document outlines the process for contributing to this project.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to foster an inclusive and respectful community.

## Development Process

### Setting Up Your Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/gh-project-manager-mcp.git
   cd gh-project-manager-mcp
   ```
3. Set up a remote for the upstream repository:
   ```bash
   git remote add upstream https://github.com/marioalvial/gh-project-manager-mcp.git
   ```
4. Install dependencies:
   ```bash
   poetry install --with dev
   ```

### Making Changes

1. Create a new branch from `main` for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes, adhering to the project's coding standards
3. Add tests for any new functionality
4. Make sure all tests pass:
   ```bash
   poetry run pytest
   ```
5. Run linting tools:
   ```bash
   poetry run ruff check .
   ```

### Submitting a Pull Request

1. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
2. Open a pull request against the `main` branch of the upstream repository
3. Provide a clear description of the changes and any related issues
4. Wait for review from maintainers

## Coding Standards

This project follows these standards:

- **Type Annotations**: All functions, methods, and class variables must have type annotations
- **Docstrings**: All public functions, methods, and classes must have docstrings following the format in the project
- **Testing**: All new functionality must be covered by tests
- **Linting**: Code should pass the project's linting rules

## Testing

- Write tests for all new functionality
- Ensure all tests pass before submitting pull requests
- Test coverage should not decrease with new contributions

## Documentation

- Update the README.md when necessary
- Document new features, tools, or configuration options
- Keep docstrings up-to-date with code changes

## Issue Reporting

If you find a bug or have a feature request:

1. Check if it's already been reported in the [Issues](https://github.com/marioalvial/gh-project-manager-mcp/issues)
2. If not, open a new issue with a clear title and description
3. Include steps to reproduce bugs and, if possible, a minimal code example
4. For feature requests, explain the use case and value of the feature

## Review Process

- Pull requests require approval from at least one maintainer
- CI checks must pass before merging
- Maintainers may request changes before merging
- Once approved, maintainers will merge the pull request

## License

By contributing, you agree that your contributions will be licensed under the project's [MIT License](LICENSE). 