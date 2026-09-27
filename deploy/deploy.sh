#!/bin/bash
set -euo pipefail

REPO="anorthall/incident-db"
APP_DIR="/opt/cidb"
IMAGE="ghcr.io/${REPO}"
REF="${1:-main}"
LOG="/var/log/cidb-deploy.log"

log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }

log "deploy starting: ref=${REF} image=${IMAGE}"

SHA="$(curl -fsSL "https://api.github.com/repos/${REPO}/commits/${REF}" \
  -H "Accept: application/vnd.github.sha")"
if [[ ! "$SHA" =~ ^[0-9a-f]{40}$ ]]; then
  log "FAILED: GitHub did not return a commit SHA for ${REF}"
  exit 1
fi
SHORT="${SHA:0:7}"
TAG="sha-${SHORT}"
log "resolved ${REF} -> ${SHA} (tag ${TAG})"

PREVIOUS_TAG="$(cat "${APP_DIR}/.deployed-tag" 2>/dev/null || echo "")"
log "previously deployed tag: ${PREVIOUS_TAG:-<none>}"

for f in compose.yml Caddyfile backup.sh restore.sh; do
  curl -fsSL -o "${APP_DIR}/${f}" \
    "https://raw.githubusercontent.com/${REPO}/${SHA}/deploy/${f}"
done
chmod +x "${APP_DIR}/backup.sh" "${APP_DIR}/restore.sh"

units_changed=false
for unit in cidb-backup.service cidb-backup.timer; do
  curl -fsSL -o "/tmp/${unit}" \
    "https://raw.githubusercontent.com/${REPO}/${SHA}/deploy/systemd/${unit}"
  if ! cmp -s "/tmp/${unit}" "/etc/systemd/system/${unit}"; then
    install -m 0644 "/tmp/${unit}" "/etc/systemd/system/${unit}"
    units_changed=true
  fi
  rm -f "/tmp/${unit}"
done

if [ "$units_changed" = true ]; then
  systemctl daemon-reload
  systemctl reenable cidb-backup.timer
  systemctl restart cidb-backup.timer
  log "systemd units updated and timer reloaded"
fi

log "fetched deploy files at ${SHORT}"

umask 077
{
  aws ssm get-parameters-by-path --path /cidb/prod --with-decryption --recursive \
    --query 'Parameters[].[Name,Value]' --output text \
  | while IFS=$'\t' read -r name value; do echo "${name##*/}=${value}"; done
  echo "IMAGE_TAG=${TAG}"
  echo "GIT_SHA=${SHA}"
} > "${APP_DIR}/prod.env"
chmod 600 "${APP_DIR}/prod.env"

for required in SECRET_KEY POSTGRES_PASSWORD ACME_EMAIL API_DOMAIN BACKUP_BUCKET; do
  grep -q "^${required}=." "${APP_DIR}/prod.env" || {
    log "FAILED: ${required} missing or empty in prod.env (check /cidb/prod in Parameter Store)"
    exit 1
  }
done

# Checked across every key, not a list: an unset SENTRY_DSN is merely absent,
# but one reading "placeholder" is truthy and raises BadDsn at settings import,
# crash-looping the container. Any key left at the placeholder is a failure.
unset_keys="$(grep -E '^[A-Za-z0-9_]+=placeholder$' "${APP_DIR}/prod.env" | cut -d= -f1 || true)"
if [ -n "$unset_keys" ]; then
  log "FAILED: these parameters still hold the Terraform placeholder value:"
  for k in $unset_keys; do log "    /cidb/prod/${k}"; done
  log "  Expected on a first boot: Terraform creates each parameter as 'placeholder'"
  log "  with ignore_changes, so real values are set out of band afterwards. Set them:"
  log "    aws ssm put-parameter --name /cidb/prod/<KEY> --value '<value>' --overwrite --type SecureString"
  log "  then re-run: /opt/cidb/deploy.sh main"
  exit 1
fi

POSTGRES_PASSWORD="$(grep '^POSTGRES_PASSWORD=' "${APP_DIR}/prod.env" | cut -d= -f2-)"
echo "DATABASE_URL=postgres://cidb:${POSTGRES_PASSWORD}@postgres:5432/cidb" \
  >> "${APP_DIR}/prod.env"
log "rendered prod.env ($(wc -l < "${APP_DIR}/prod.env") vars)"

cd "${APP_DIR}"
dc() { docker compose --env-file prod.env -f compose.yml "$@"; }

if ! command -v mountpoint >/dev/null 2>&1; then
  log "FAILED: mountpoint(1) unavailable, cannot verify the data volume - install util-linux"
  exit 1
fi

if ! mountpoint -q "${APP_DIR}/data"; then
  log "FAILED: ${APP_DIR}/data is not a mounted volume - refusing to start Postgres"
  log "Postgres would write to the ephemeral root disk. Check the EBS attachment and fstab."
  exit 1
fi

dc pull
dc up -d postgres
for _ in $(seq 1 30); do
  if dc exec -T postgres pg_isready -U cidb -d cidb >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
dc exec -T postgres pg_isready -U cidb -d cidb >/dev/null
log "postgres ready"

log "applying migrations"
dc run --rm web python cidb/manage.py migrate --noinput

dc up -d
log "containers up, waiting for healthcheck"

healthy=false
for _ in $(seq 1 30); do
  if dc exec -T web python -c \
    'import urllib.request;urllib.request.urlopen("http://localhost:8000/core/healthcheck/")' \
    >/dev/null 2>&1; then
    healthy=true
    break
  fi
  sleep 2
done

if [ "$healthy" != true ]; then
  log "HEALTHCHECK FAILED for ${TAG}"
  if [ -n "$PREVIOUS_TAG" ] && [ "$PREVIOUS_TAG" != "$TAG" ]; then
    log "rolling back to ${PREVIOUS_TAG}"
    sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=${PREVIOUS_TAG}/" "${APP_DIR}/prod.env"
    dc up -d web || log "ROLLBACK TO ${PREVIOUS_TAG} ALSO FAILED - site is down"
  else
    log "no previous tag recorded, leaving ${TAG} up for diagnosis"
  fi
  exit 1
fi

echo "$TAG" > "${APP_DIR}/.deployed-tag"
docker image prune -af --filter until=168h >/dev/null 2>&1 || true
log "deploy complete: ${TAG}"
