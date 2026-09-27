#!/bin/bash
# Runs the real production stack locally and asserts it actually works.
# Catches what static checks cannot: the image failing to build, gunicorn
# failing to start, migrations failing, and the reverse-proxy behaviours the
# application depends on in production.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
REPO_ROOT="$(cd .. && pwd)"
ENV_FILE="prod.env"
BASE_URL="https://localhost:8443"
KEEP_UP="${KEEP_UP:-false}"

pass=0
fail=0

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
ok() { printf '  \033[32m✓\033[0m %s\n' "$*"; pass=$((pass + 1)); }
bad() { printf '  \033[31m✗\033[0m %s\n' "$*"; fail=$((fail + 1)); }

dc() { docker compose --env-file "$ENV_FILE" -f compose.yml -f compose.local.yml "$@"; }

cleanup() {
  if [ "$KEEP_UP" = true ]; then
    printf '\nKEEP_UP=true, leaving the stack running. Tear down with:\n'
    printf '  cd %s/deploy && docker compose --env-file prod.env -f compose.yml -f compose.local.yml down -v\n' "$REPO_ROOT"
    return
  fi
  printf '\nTearing down...\n'
  dc down -v >/dev/null 2>&1 || true
  rm -f "$ENV_FILE"
}
trap cleanup EXIT

if [ -e "$ENV_FILE" ]; then
  echo "Refusing to overwrite an existing ${PWD}/${ENV_FILE}. Move it aside first." >&2
  exit 1
fi

say "Building the production image for linux/arm64"
docker buildx build --platform linux/arm64 -t cidb:local --load "$REPO_ROOT" >/dev/null
ok "image builds"

# Generated, never written down: the local database uses trust auth, so the
# value only has to exist for compose interpolation.
throwaway="$(head -c 12 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9')"

cat > "$ENV_FILE" <<EOF
SECRET_KEY=${throwaway}
POSTGRES_PASSWORD=${throwaway}
DEBUG=false
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,web
CSRF_TRUSTED_ORIGINS=https://localhost:8443
CORS_ALLOWED_ORIGINS=https://localhost:8443
ACME_EMAIL=smoke@example.com
API_DOMAIN=localhost
BACKUP_BUCKET=unused-locally
WEB_CONCURRENCY=2
DATABASE_URL=postgres://cidb@postgres:5432/cidb
IMAGE_TAG=local
EOF

say "Starting Postgres"
if ! dc up -d postgres; then
  bad "could not start postgres"
  exit 1
fi
# A fresh volume runs initdb first, which takes several seconds.
for _ in $(seq 1 60); do
  dc exec -T postgres pg_isready -U cidb -d cidb >/dev/null 2>&1 && break
  sleep 2
done
if dc exec -T postgres pg_isready -U cidb -d cidb >/dev/null 2>&1; then
  ok "postgres healthy"
else
  bad "postgres never became healthy"
  exit 1
fi

say "Applying migrations (the step deploy.sh runs before cutover)"
if dc run --rm web python cidb/manage.py migrate --noinput >/dev/null 2>&1; then
  ok "migrations apply to an empty database"
else
  bad "migrations failed"
  dc run --rm web python cidb/manage.py migrate --noinput || true
  exit 1
fi

say "Starting the full stack"
dc up -d >/dev/null 2>&1
healthy=false
for _ in $(seq 1 40); do
  if dc exec -T web python -c \
    'import urllib.request;urllib.request.urlopen("http://localhost:8000/core/healthcheck/")' \
    >/dev/null 2>&1; then
    healthy=true
    break
  fi
  sleep 2
done
if [ "$healthy" = true ]; then
  ok "gunicorn starts and the healthcheck passes"
else
  bad "the healthcheck never passed - container logs follow"
  dc logs web --no-log-prefix --tail 40
  exit 1
fi

say "Checking behaviour through Caddy over TLS"

check_status() {
  local path="$1" expected="$2" label="$3" actual
  # A refused connection must fail this assertion, not abort the run under set -e.
  actual="$(curl -sk -o /dev/null -w '%{http_code}' "${BASE_URL}${path}" || true)"
  if [ "$actual" = "$expected" ]; then
    ok "$label ($actual)"
  else
    bad "$label: expected $expected, got $actual"
  fi
}

check_status /core/healthcheck/ 200 "healthcheck responds"
check_status /api/v1/incidents/search 200 "API search responds"
check_status /api/v1/nope 404 "unrouted API path returns 404, not 500"
check_status /admin/login/ 200 "Django admin loads"
check_status /api/v1/openapi.json 200 "OpenAPI schema served"

if curl -sk -D- -o /dev/null "${BASE_URL}/api/v1/incidents/search" |
  grep -qi 'set-cookie:.*cidb_visitor.*Secure'; then
  ok "visitor cookie is Secure behind the proxy (SECURE_PROXY_SSL_HEADER)"
else
  bad "visitor cookie is missing the Secure flag behind TLS"
fi

css_path="$(curl -sk "${BASE_URL}/admin/login/" | grep -o '/static/[^"]*\.css' | head -1 || true)"
if [ -n "$css_path" ] &&
  [ "$(curl -sk -o /dev/null -w '%{http_code}' "${BASE_URL}${css_path}")" = "200" ]; then
  ok "admin static assets served by whitenoise"
else
  bad "admin static assets not served - /static/* would be broken"
fi

schema="$(curl -sk "${BASE_URL}/api/v1/openapi.json" || true)"
for route in /api/v1/auth/login /api/v1/staff/feedback/; do
  if printf '%s' "$schema" | grep -q "$route"; then
    ok "route present: $route"
  else
    bad "route missing: $route"
  fi
done

say "Result"
printf '  %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
