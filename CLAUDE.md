# Commands

- `just dc <docker-compose args>`: Run docker-compose commands
- `just dj <manage.py args>`: Run Django management commands
- `just ruff`: Run ruff
- `just mypy`: Run mypy type checker
- `just lint`: Run all linters (ruff and mypy)

# Code style

- YOU MUST NEVER leave comments in code that are not strictly 100% necessary for understanding.
  Do not write docstrings or general comments unless truly required or asked to do so.
- YOU MUST NEVER use `# type: ignore` comments to silence mypy errors.
- You MUST code that can be strictly type checked with mypy without any errors.
- You MUST use ruff to format code and fix linting issues.
- You MUST use modern Python typing, e.g. `list[int]` instead of `List[int]`.
- YOU MUST NEVER use `Optional` or `Any` from `typing` module unless strictly necessary.

# Procedure

- Always raise any architectural concerns before a task.
- After any coding task, check for dead code and remove it.
- Run `just lint` to ensure code quality before committing changes.
- Review code for adherence to style guidelines and best practices.
