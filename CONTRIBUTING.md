# Contributing to AI CV Builder

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/cv-builder.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate it and install dev dependencies: `pip install -r requirements.txt -e ".[dev]"`
5. Create a feature branch: `git checkout -b feature/your-feature-name`

## Development Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ scripts/

# Lint code
flake8 src/ scripts/

# Type check
mypy src/
```

## Code Style

- Follow PEP 8
- Use type hints where possible
- Keep functions small and focused
- Add docstrings to public functions
- Use Black for formatting

## Making Changes

1. Make your changes in a feature branch
2. Add/update tests if needed
3. Update documentation if needed
4. Test locally: `pytest`
5. Commit with clear, descriptive messages

## Commit Messages

Use clear, descriptive commit messages:
- ✅ Good: "Add ATS keyword injection for better CV optimization"
- ❌ Bad: "fix stuff"

## Pull Requests

1. Include a clear description of changes
2. Reference any related issues: "Closes #123"
3. Ensure all tests pass
4. Update README if adding new features

## Reporting Bugs

- Use GitHub Issues
- Include: reproduction steps, expected behavior, actual behavior
- Attach error messages or screenshots if relevant

## Suggesting Features

- Open a GitHub Issue with the `feature` label
- Describe the use case and expected behavior
- Discuss before implementing major changes

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
