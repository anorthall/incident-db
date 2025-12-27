default:
    just --list

ruff +ARGS="":
    uv run ruff format
    uv run ruff check --fix

mypy +ARGS="./":
    dmypy run -- {{ ARGS }}

lint +ARGS="":
    just ruff
    just mypy {{ ARGS }}

dj +ARGS="":
    docker compose run --rm web python cidb/manage.py {{ ARGS }}

dc +ARGS="":
    docker compose {{ ARGS }}

fe +ARGS="dev":
    cd frontend/cidb && pnpm {{ ARGS }}
