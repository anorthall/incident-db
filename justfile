default:
  just --list

lint +ARGS="":
  uv run ruff format
  uv run ruff check --fix
  just mypy {{ ARGS }}

mypy +ARGS="reportdb/":
  dmypy run -- {{ ARGS }}
