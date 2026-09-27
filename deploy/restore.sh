#!/bin/bash
set -euo pipefail

APP_DIR="/opt/cidb"
cd "$APP_DIR"
set -a
# shellcheck disable=SC1091
source prod.env
set +a

BUCKET="${BACKUP_BUCKET:?BACKUP_BUCKET not set}"
WHICH="${1:?usage: restore.sh <s3-key|latest>}"

if [ "$WHICH" = "latest" ]; then
  KEY="$(aws s3api list-objects-v2 --bucket "$BUCKET" --prefix postgres/ \
    --query 'sort_by(Contents,&LastModified)[-1].Key' --output text)"
else
  KEY="$WHICH"
fi

if [ -z "$KEY" ] || [ "$KEY" = "None" ]; then
  echo "no backup found under s3://${BUCKET}/postgres/" >&2
  exit 1
fi

aws s3api head-object --bucket "$BUCKET" --key "$KEY" \
  --query '[ContentLength,LastModified]' --output text

echo
echo "About to CLEAN and restore the cidb database from s3://${BUCKET}/${KEY}"
echo "This destroys all current data. Type yes to continue."
read -r confirm
[ "$confirm" = "yes" ] || { echo "aborted"; exit 1; }

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
aws s3 cp "s3://${BUCKET}/${KEY}" "$TMP"

dc() { docker compose --env-file prod.env -f compose.yml "$@"; }
dc stop web
dc exec -T postgres pg_restore --clean --if-exists --no-owner -U cidb -d cidb < "$TMP"
dc up -d web
echo "restore complete"
