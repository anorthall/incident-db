default:
  just --list

lint:
  uv run ruff format
  uv run ruff check --fix
  mypy reportdb/ --strict --no-namespace-packages
