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

prod-shell:
    aws ssm start-session --target "$CIDB_PROD_INSTANCE_ID"

prod-manage +ARGS:
    aws ssm send-command \
      --instance-ids "$CIDB_PROD_INSTANCE_ID" \
      --document-name AWS-RunShellScript \
      --parameters 'commands=["cd /opt/cidb && docker compose --env-file prod.env -f compose.yml exec -T web python cidb/manage.py {{ ARGS }}"]' \
      --query Command.CommandId --output text
