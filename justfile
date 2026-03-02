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

test-backend +ARGS="--tb=short -q":
    just dc exec web uv run pytest {{ ARGS }}

test-frontend +ARGS="":
    cd frontend/cidb && pnpm test {{ ARGS }}

test:
    just test-backend
    just test-frontend
