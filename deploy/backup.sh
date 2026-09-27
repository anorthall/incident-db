#!/bin/bash
set -euo pipefail

APP_DIR="/opt/cidb"
cd "$APP_DIR"
set -a
# shellcheck disable=SC1091
source prod.env
set +a

BUCKET="${BACKUP_BUCKET:?BACKUP_BUCKET not set}"
KEY="postgres/cidb-$(date -u +%Y%m%dT%H%M%SZ).dump"
CRON="${SENTRY_CRON_URL:-}"

checkin() {
  if [ -n "$CRON" ]; then
    curl -fsS -m 10 "${CRON}?status=$1" >/dev/null 2>&1 || true
  fi
}

fail() {
  echo "backup failed: $*" >&2
  checkin error
  exit 1
}

checkin in_progress

docker compose --env-file prod.env -f compose.yml exec -T postgres \
  pg_dump -U cidb -Fc cidb | aws s3 cp - "s3://${BUCKET}/${KEY}" \
  || fail "pg_dump or upload failed"

SIZE="$(aws s3api head-object --bucket "$BUCKET" --key "$KEY" \
  --query ContentLength --output text)" || fail "uploaded object not found"
[ "$SIZE" -gt 1000 ] || fail "uploaded dump is only ${SIZE} bytes"

echo "backup ok: s3://${BUCKET}/${KEY} (${SIZE} bytes)"
checkin ok
