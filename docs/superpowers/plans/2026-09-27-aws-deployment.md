# AWS Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make CIDB v2 deployable to the NSS AWS account at `incidents.caves.org` from GitHub CI, on a single Graviton EC2 instance with the SPA on S3 behind the existing CloudFront distribution.

**Architecture:** One `t4g.small` Amazon Linux 2023 arm64 instance runs three containers (Caddy → gunicorn, plus Postgres) via Docker Compose, with Postgres data and Caddy certificates on a separate EBS volume that survives instance replacement. The SPA is built in CI and synced to a new private S3 bucket served by the existing CloudFront distribution. GitHub Actions authenticates with OIDC and deploys by sending one SSM command; no SSH, no long-lived AWS keys, no secrets in the repo.

**Tech Stack:** Terraform 1.14.3 / AWS provider 6.28.0, Docker Compose, Caddy 2, Postgres 18, Django 6 + django-ninja, React 19 + Vite, GitHub Actions, AWS SSM Parameter Store + Session Manager + Run Command.

**Spec:** `docs/superpowers/specs/2026-09-27-aws-deployment-design.md`

## Global Constraints

- Python typing: modern built-in generics only — `list[int]`, `dict[str, X]`, `X | None`. Never `Dict`, `List`, `Optional`, `Union`.
- Never use `Any` from `typing` unless strictly necessary. **Never** use `# type: ignore`.
- Never leave comments or docstrings that are not strictly necessary for understanding.
- `just lint` (ruff format + ruff check + mypy) must pass with zero errors before any commit.
- Ruff line length 100. All code must be ruff-formatted.
- Terraform: `terraform fmt` clean, `terraform validate` passes. Provider pinned at 6.28.0, Terraform at 1.14.3.
- Shell scripts: `#!/bin/bash` + `set -euo pipefail`, and must pass `shellcheck` with no warnings.
- Region is `us-west-2`. Domain is `incidents.caves.org`. API host is `api.incidents.caves.org`.
- Image is `ghcr.io/anorthall/incident-db`, tagged `sha-<7 chars>` — verified publicly pullable anonymously, so the box needs no registry credentials.
- Instance architecture is **arm64**. Any image the box runs must be built for `linux/arm64`.
- Commit messages end with the two attribution lines given in this session's environment.

## Test Environment

Docker is running and a throwaway Postgres is already up on port **55432**. Every backend test command in this plan assumes this environment:

```bash
export DEBUG=true SECRET_KEY=testkey
export PYTHONPATH="$PWD:$PWD/cidb"
export DATABASE_URL="postgres://postgres:postgres@127.0.0.1:55432/postgres"  # pragma: allowlist secret
```

If the container is gone, recreate it:

```bash
docker run -d --rm --name cidb-test-pg -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres -e POSTGRES_DB=postgres -p 55432:5432 postgres:18
```

Baseline at plan time: **72 backend tests pass, 32 frontend tests pass, ruff clean, mypy 12 errors** (Task 5 fixes those).

## Review Focus

Input classes the spec implies but no task's tests naturally exercise. Each has its test assigned to the owning task.

1. **An unrouted URL under `/api/v1/` must return 404, not 500.** The deployed Dec-2025 build returns 500; `main` returns 404. Without a regression test nothing stops it coming back. → Task 6.
2. **A request arriving over HTTP-forwarded-as-HTTPS must set `Secure` cookies and pass CSRF.** Behind Caddy, `request.is_secure()` is false unless `SECURE_PROXY_SSL_HEADER` is set, which silently downgrades cookie security. → Task 3.
3. **Media URLs must resolve through CloudFront, not a private S3 hostname.** The bucket is private; a direct S3 URL 403s for every viewer. → Task 2.
4. **`deploy.sh` re-run with the same SHA must be a no-op, and with a bad SHA must leave the site running.** Idempotence and rollback are the whole safety story for a single box. → Task 9.
5. **`backup.sh` must fail loudly on an empty or missing dump.** A backup script that exits 0 having written nothing is worse than none. → Task 10.

---

## File Structure

**Created:**
- `deploy/compose.yml` — the three-service production stack
- `deploy/Caddyfile` — TLS termination and reverse proxy
- `deploy/deploy.sh` — converge the box to a git SHA (the only thing CI calls)
- `deploy/backup.sh` — nightly `pg_dump` to S3 with Sentry cron check-ins
- `deploy/restore.sh` — interactive restore from S3
- `deploy/systemd/cidb-backup.service`, `deploy/systemd/cidb-backup.timer`
- `deploy/cloud-init.yaml` — first-boot bootstrap, rendered by Terraform
- `tf/parameters.tf` — SSM Parameter Store declarations
- `tf/outputs.tf` — values CI and the operator need
- `.github/workflows/deploy-backend.yaml`, `.github/workflows/deploy-frontend.yaml`
- `.github/workflows/infra-checks.yaml` — terraform fmt/validate + shellcheck on PRs
- `frontend/cidb/public/` — brand assets fetched from the live CDN
- `cidb/src/core/tests/test_http_errors.py` — 404 regression tests

**Modified:**
- `cidb/conf/settings.py` — cache, storage, proxy/TLS settings
- `cidb/src/core/middleware.py` — visitor cookie `secure` flag
- `cidb/conf/run.sh` — `WEB_CONCURRENCY`
- `cidb/src/incidents/api/schemas/feedback.py` — mypy fixes
- `frontend/cidb/index.html`, `frontend/cidb/src/constants.ts` — root-relative assets
- `tf/ec2.tf`, `tf/cloudfront.tf`, `tf/iam.tf`, `tf/s3.tf`, `tf/variables.tf`
- `.github/workflows/lint.yaml` — add mypy
- `pyproject.toml`, `uv.lock` — drop `django-valkey`
- `justfile`, `README.md`, `docker-compose.yml`

**Deleted:**
- `tf/secrets.tf`, `compose.prod.example.yml`, `.github/workflows/container.yaml`

---

## Task 1: Remove Valkey

No code calls the Django cache and sessions are DB-backed, so the Valkey service, dependency and settings are pure overhead.

**Files:**
- Modify: `cidb/conf/settings.py:85-97`, `pyproject.toml`, `uv.lock`, `docker-compose.yml`
- Test: `cidb/src/core/tests/test_http_errors.py` (created in Task 6 — for this task, the full suite is the test)

**Interfaces:**
- Consumes: nothing.
- Produces: `CACHES["default"]["BACKEND"] == "django.core.cache.backends.locmem.LocMemCache"`. No `VALKEY_URL` setting exists after this task.

- [ ] **Step 1: Confirm nothing uses the cache**

```bash
grep -rn "cache\.\(get\|set\|delete\|get_or_set\|incr\|add\)\|cache_page\|VALKEY" cidb/src --include='*.py' | grep -v mypy_cache
```

Expected: no output. If there IS output, stop — the premise is wrong; report it and do not proceed.

- [ ] **Step 2: Replace the cache backend**

In `cidb/conf/settings.py`, delete the `VALKEY_URL` line and replace the whole `CACHES` block with:

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "cidb",
        "TIMEOUT": 3600,
    }
}
```

- [ ] **Step 3: Drop the dependency**

Remove `"django-valkey>=0.4.0",` from `dependencies` in `pyproject.toml`, then:

```bash
uv lock
```

- [ ] **Step 4: Remove the dev compose service**

In `docker-compose.yml`, delete the `valkey:` service block, the `- valkey` entry under `web.depends_on`, and the `valkey:` entry under top-level `volumes:`.

- [ ] **Step 5: Run the full suite**

```bash
uv run pytest -q
```

Expected: `72 passed`.

- [ ] **Step 6: Lint and commit**

```bash
just lint
git add -A && git commit -m "refactor: remove unused Valkey cache

Nothing in the application calls the Django cache and sessions are
database-backed, so the Valkey service, dependency and settings were
overhead only."
```

---

## Task 2: S3 storage for the instance role and CloudFront media

Boto3 must fall back to instance-metadata credentials, and `MEDIA_URL` must point at CloudFront because the bucket is private.

**Files:**
- Modify: `cidb/conf/settings.py:114-133`
- Test: `cidb/src/core/tests/test_settings_storage.py` (create)

**Interfaces:**
- Consumes: nothing.
- Produces: `AWS_S3_ACCESS_KEY_ID` / `AWS_S3_SECRET_ACCESS_KEY` are `str | None` and `None` when unset; `MEDIA_URL` is `https://{AWS_S3_CUSTOM_DOMAIN}/media/`.

- [ ] **Step 1: Write the failing test**

Create `cidb/src/core/tests/test_settings_storage.py`:

```python
from django.conf import settings


def test_s3_credentials_are_none_when_unset() -> None:
    assert settings.AWS_S3_ACCESS_KEY_ID is None
    assert settings.AWS_S3_SECRET_ACCESS_KEY is None


def test_media_url_uses_custom_domain() -> None:
    assert settings.MEDIA_URL.startswith("https://")
    assert settings.MEDIA_URL.endswith("/media/")


def test_querystring_auth_disabled() -> None:
    assert settings.AWS_QUERYSTRING_AUTH is False
```

- [ ] **Step 2: Run it to verify it fails**

```bash
uv run pytest cidb/src/core/tests/test_settings_storage.py -q
```

Expected: FAIL — `AWS_S3_ACCESS_KEY_ID` is `""`, not `None`; `AWS_QUERYSTRING_AUTH` does not exist.

- [ ] **Step 3: Implement**

In `cidb/conf/settings.py`, replace the four credential/domain lines with:

```python
AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME", default="us-west-2")
AWS_S3_ACCESS_KEY_ID = env.str("AWS_S3_ACCESS_KEY_ID", default=None) or None
AWS_S3_SECRET_ACCESS_KEY = env.str("AWS_S3_SECRET_ACCESS_KEY", default=None) or None
AWS_S3_CUSTOM_DOMAIN = env.str(
    "AWS_S3_CUSTOM_DOMAIN",
    default=f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com",
)
AWS_QUERYSTRING_AUTH = False
AWS_DEFAULT_ACL = None
```

Leave `MEDIA_LOCATION`, `MEDIA_URL` and `STORAGES` exactly as they are.

- [ ] **Step 4: Run tests**

```bash
uv run pytest cidb/src/core/tests/test_settings_storage.py -q && uv run pytest -q
```

Expected: new tests PASS, `75 passed` overall.

- [ ] **Step 5: Lint and commit**

```bash
just lint
git add -A && git commit -m "fix: let boto3 use the EC2 instance role for S3

Empty-string credentials stopped boto3 falling back to instance
metadata. Defaulting them to None restores the fallback, and
AWS_QUERYSTRING_AUTH=False keeps media URLs unsigned so CloudFront
can cache them."
```

---

## Task 3: Proxy-aware TLS and cookie security

Behind Caddy, Django sees HTTP. Without `SECURE_PROXY_SSL_HEADER`, `request.is_secure()` is false, cookies lose `Secure`, and CSRF referer checks fail.

**Files:**
- Modify: `cidb/conf/settings.py` (after the `CSRF_COOKIE_HTTPONLY` line), `cidb/src/core/middleware.py:118`
- Test: `cidb/src/core/tests/test_middleware.py` (append)

**Interfaces:**
- Consumes: nothing.
- Produces: `settings.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")`; the visitor cookie's `secure` flag derives from `request.is_secure()`.

- [ ] **Step 1: Write the failing test**

Append to `cidb/src/core/tests/test_middleware.py`:

```python
def test_visitor_cookie_secure_behind_tls_proxy(client: Client) -> None:
    response = client.get("/api/v1/incidents/search", HTTP_X_FORWARDED_PROTO="https")
    assert response.cookies["cidb_visitor"]["secure"] is True


def test_visitor_cookie_not_secure_over_plain_http(client: Client) -> None:
    response = client.get("/api/v1/incidents/search")
    assert not response.cookies["cidb_visitor"]["secure"]
```

If `Client` is not already imported in that file, add `from django.test import Client` and add a `client` fixture use consistent with the file's existing style — check the existing tests first and match them.

- [ ] **Step 2: Run it to verify it fails**

```bash
uv run pytest cidb/src/core/tests/test_middleware.py -q
```

Expected: FAIL — the cookie is secure based on `SERVER_NAME`, not the forwarded proto.

- [ ] **Step 3: Implement the settings**

In `cidb/conf/settings.py`, immediately after `CSRF_COOKIE_HTTPONLY = True`, add:

```python
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
```

- [ ] **Step 4: Implement the middleware change**

In `cidb/src/core/middleware.py`, in `VisitorTrackingMiddleware.__call__`, replace:

```python
            secure=not request.META.get("SERVER_NAME", "").startswith("localhost"),
```

with:

```python
            secure=request.is_secure(),
```

- [ ] **Step 5: Run tests**

```bash
uv run pytest -q
```

Expected: `77 passed`.

- [ ] **Step 6: Lint and commit**

```bash
just lint
git add -A && git commit -m "fix: trust the reverse proxy for TLS detection

Behind Caddy, Django sees plain HTTP. Without SECURE_PROXY_SSL_HEADER
the visitor cookie lost its Secure flag and CSRF referer checks would
fail in production."
```

---

## Task 4: Configurable gunicorn concurrency

The `t4g.small` has 2 vCPU and 2 GB; four preloaded workers is too many. Make it an environment variable rather than a hard-coded 4.

**Files:**
- Modify: `cidb/conf/run.sh`

**Interfaces:**
- Consumes: nothing.
- Produces: `run.sh start` honours `WEB_CONCURRENCY`, defaulting to 4.

- [ ] **Step 1: Implement**

In `cidb/conf/run.sh`, inside the `if [ "$1" = "start" ]` block, replace `--workers 4 \` with `--workers "${WEB_CONCURRENCY:-4}" \`.

- [ ] **Step 2: Verify the script still parses**

```bash
bash -n cidb/conf/run.sh && shellcheck -S warning cidb/conf/run.sh || true
```

Expected: `bash -n` produces no output. Pre-existing shellcheck warnings in this file are acceptable; do not refactor it.

- [ ] **Step 3: Commit**

```bash
git add cidb/conf/run.sh
git commit -m "feat: make gunicorn worker count configurable

WEB_CONCURRENCY defaults to 4; production sets 3 to suit a 2 vCPU
instance."
```

---

## Task 5: Fix the 12 mypy errors

`just lint` is red and CI never ran mypy, so this rotted. Fix it so Task 16 can gate on it.

**Files:**
- Modify: `cidb/src/incidents/api/schemas/feedback.py:40-80`, `cidb/conf/settings.py:18,21`

**Interfaces:**
- Consumes: nothing.
- Produces: `just mypy` exits 0.

- [ ] **Step 1: Reproduce**

```bash
uv run dmypy run -- ./ 2>&1 | tail -20
```

Expected: `Found 12 errors in 2 files`. Ten are `Argument 1 to "FeedbackListItemSchema" has incompatible type "**dict[str, object]"`; two are `Module has no attribute "Env"` in `settings.py`.

- [ ] **Step 2: Fix the schema errors**

The cause is `_base_kwargs` returning an untyped `dict[str, object]` that is then `**`-unpacked into a typed constructor. Replace the `_base_kwargs` + `from_report` pattern with direct construction so mypy can check each field. In `cidb/src/incidents/api/schemas/feedback.py`, replace the `_base_kwargs` classmethod and both `from_report` classmethods with:

```python
    @classmethod
    def from_report(cls, report: ContentReport) -> FeedbackListItemSchema:
        return cls(
            id=report.id,
            incident=_incident_of(report),
            url=report.url,
            reason=report.reason,
            reason_display=ReportReason(report.reason).label,
            description=report.description,
            status=report.status,
            status_display=ReportStatus(report.status).label,
            reporter=_reporter_of(report),
            created_at=report.created_at,
            updated_at=report.updated_at,
        )
```

and for `FeedbackDetailSchema`:

```python
    @classmethod
    def from_report(cls, report: ContentReport) -> FeedbackDetailSchema:
        return cls(
            id=report.id,
            incident=_incident_of(report),
            url=report.url,
            reason=report.reason,
            reason_display=ReportReason(report.reason).label,
            description=report.description,
            status=report.status,
            status_display=ReportStatus(report.status).label,
            reporter=_reporter_of(report),
            created_at=report.created_at,
            updated_at=report.updated_at,
            reviewer_notes=report.reviewer_notes,
        )
```

Extract the `incident` and `reporter` derivation currently inside `_base_kwargs` into two module-level helpers with explicit return types:

```python
def _incident_of(report: ContentReport) -> IncidentMinimalSchema | None:
    ...


def _reporter_of(report: ContentReport) -> ReporterSchema | None:
    ...
```

Read the existing `_base_kwargs` body first and move its logic verbatim into these helpers — do not invent new behaviour. The API responses must be byte-identical.

- [ ] **Step 3: Fix the settings errors**

`django-environ` ships no type information, and the `ignore_missing_imports` override makes the module `Any`-typed in a way that still fails attribute access on `environ.Env`. Replace the import and the two `environ.Env` references:

```python
from environ import Env
```

then `env = Env()` and `default="insecure-secret-key" if DEBUG else Env.NOTSET`.

If that still errors, add a minimal stub at `stubs/environ/__init__.pyi` following the pattern already used in `stubs/treebeard/`, declaring only what is used: `class Env` with `NOTSET`, `__init__`, `str`, `bool`, `list`, `db`. Do not add `# type: ignore` under any circumstances.

- [ ] **Step 4: Verify mypy is clean**

```bash
uv run dmypy stop; uv run dmypy run -- ./
```

Expected: `Success: no issues found in 126 source files`.

- [ ] **Step 5: Verify behaviour is unchanged**

```bash
uv run pytest cidb/src/incidents/tests/test_feedback_api.py -q && uv run pytest -q
```

Expected: `12 passed` then `77 passed`.

- [ ] **Step 6: Lint and commit**

```bash
just lint
git add -A && git commit -m "fix: resolve all mypy errors

Constructing feedback schemas field-by-field instead of unpacking an
untyped dict lets mypy check them, and importing Env directly fixes
the django-environ attribute errors."
```

---

## Task 6: HTTP error regression tests

**Verified at plan time:** `main` already returns 404 correctly; the 500s seen on `api.cidb.dev` come from the old deployed build. This task pins the behaviour so it cannot regress — it is not expected to require a code fix.

**Files:**
- Create: `cidb/src/core/tests/test_http_errors.py`

**Interfaces:**
- Consumes: nothing.
- Produces: nothing other tasks use.

- [ ] **Step 1: Write the test**

Create `cidb/src/core/tests/test_http_errors.py`:

```python
import pytest
from django.test import Client


@pytest.mark.parametrize(
    "path",
    ["/nonexistent-xyz", "/core/nope", "/api/v1/nope", "/api/v1/auth/nope"],
)
@pytest.mark.django_db
def test_unknown_path_returns_404(settings, path: str) -> None:
    settings.DEBUG = False
    settings.ALLOWED_HOSTS = ["testserver"]

    response = Client(raise_request_exception=False).get(path)

    assert response.status_code == 404


@pytest.mark.django_db
def test_non_integer_incident_id_returns_422(settings) -> None:
    settings.DEBUG = False
    settings.ALLOWED_HOSTS = ["testserver"]

    response = Client(raise_request_exception=False).get("/api/v1/incidents/not-an-int")

    assert response.status_code == 422
```

Type the `settings` parameter to match the project's existing pytest-django usage — check another test file first; if others leave fixtures untyped, match that, since mypy must stay clean.

- [ ] **Step 2: Run it**

```bash
uv run pytest cidb/src/core/tests/test_http_errors.py -q
```

Expected: `5 passed`. **If any 404 test fails with 500**, the bug IS present on `main` — stop and report before changing anything, because the fix (the catch-all `@api.exception_handler(Exception)` in `cidb/src/incidents/api/router.py` swallowing ninja's own `Http404` handling) is a behaviour change that needs its own review.

- [ ] **Step 3: Full suite, lint, commit**

```bash
uv run pytest -q && just lint
git add -A && git commit -m "test: pin HTTP error status codes

Unrouted paths must return 404, not 500 — the build currently deployed
to api.cidb.dev returns 500 and nothing stopped that regressing."
```

---

## Task 7: Ship the SPA's own brand assets

Eleven URLs hard-code `https://cidb.dev/cdn/assets/...`, so `incidents.caves.org` would load its branding from the Hetzner-backed domain.

**Files:**
- Create: `frontend/cidb/public/` (7 files)
- Modify: `frontend/cidb/index.html:41-54`, `frontend/cidb/src/constants.ts:24-30`

**Interfaces:**
- Consumes: nothing.
- Produces: assets served root-relative from the SPA origin. Constants keep their exported names (`CIDBLogoForLightMode`, `CIDBLogoForDarkMode`, `CIDBIconForDarkMode`, `CIDBIconForLightMode`, `DiscordIconForLightMode`, `DiscordIconForDarkMode`) — only their values change.

- [ ] **Step 1: Fetch the assets**

```bash
cd frontend/cidb && mkdir -p public/img
for f in favicon.svg favicon.ico favicon-96x96.png apple-touch-icon.png site.webmanifest; do
  curl -fsS -o "public/$f" "https://cidb.dev/cdn/assets/$f" || echo "FAILED: $f"
done
for f in cidb-light-transparent-md.png cidb-dark-transparent-md.png cidb-dark-icon.png \
         cidb-light-icon.png discord-icon-light.png discord-icon-dark.png; do
  curl -fsS -o "public/img/$f" "https://cidb.dev/cdn/assets/img/$f" || echo "FAILED: $f"
done
ls -la public public/img
```

Every file must be non-empty. If any says FAILED, stop and report which — do not substitute a placeholder image.

- [ ] **Step 2: Point index.html at them**

In `frontend/cidb/index.html`, replace each `https://cidb.dev/cdn/assets/X` with `/X`. The five links become `href="/favicon-96x96.png"`, `href="/favicon.svg"`, `href="/favicon.ico"`, `href="/apple-touch-icon.png"`, `href="/site.webmanifest"`.

- [ ] **Step 3: Point constants.ts at them**

In `frontend/cidb/src/constants.ts`, change the six constants to `/img/<filename>.png` — for example:

```ts
export const CIDBLogoForLightMode = "/img/cidb-light-transparent-md.png";
```

- [ ] **Step 4: Verify no references remain**

```bash
cd frontend/cidb && grep -rn "cidb\.dev" src index.html | grep -v "mailto\|feedback@"
```

Expected: no output.

- [ ] **Step 5: Build and test**

```bash
cd frontend/cidb && ./node_modules/.bin/vitest run && ./node_modules/.bin/tsc -b && ./node_modules/.bin/vite build
ls dist/ dist/img/
```

Expected: 32 tests pass; build succeeds; `dist/` contains the seven asset files copied from `public/`.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "fix: serve the SPA's brand assets from its own origin

The favicons and logos were hard-coded to cidb.dev, so a deployment at
incidents.caves.org would depend on the Hetzner-backed domain."
```

---

## Task 8: Production compose stack and Caddyfile

**Files:**
- Create: `deploy/compose.yml`, `deploy/Caddyfile`
- Delete: `compose.prod.example.yml`

**Interfaces:**
- Consumes: nothing.
- Produces: services named exactly `web`, `postgres`, `caddy`. `deploy.sh` (Task 9) calls `docker compose ... run --rm web`, `exec -T postgres`, and `up -d`. Env file is `/opt/cidb/prod.env`. Data lives under `/opt/cidb/data/{postgres,caddy}`.

- [ ] **Step 1: Write `deploy/compose.yml`**

```yaml
name: cidb

x-logging: &logging
  driver: json-file
  options:
    max-size: "10m"
    max-file: "5"

services:
  web:
    image: ghcr.io/anorthall/incident-db:${IMAGE_TAG}
    restart: unless-stopped
    env_file: [prod.env]
    logging: *logging
    healthcheck:
      test:
        - CMD
        - python
        - -c
        - import urllib.request;urllib.request.urlopen("http://localhost:8000/core/healthcheck/")
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 20s
    depends_on:
      postgres:
        condition: service_healthy

  postgres:
    image: postgres:18
    restart: unless-stopped
    environment:
      POSTGRES_DB: cidb
      POSTGRES_USER: cidb
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - /opt/cidb/data/postgres:/var/lib/postgresql
    logging: *logging
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cidb -d cidb"]
      interval: 10s
      timeout: 5s
      retries: 5

  caddy:
    image: caddy:2
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
    environment:
      ACME_EMAIL: ${ACME_EMAIL}
      API_DOMAIN: ${API_DOMAIN}
    volumes:
      - /opt/cidb/Caddyfile:/etc/caddy/Caddyfile:ro
      - /opt/cidb/data/caddy:/data
    logging: *logging
    depends_on: [web]
```

Note `web` publishes **no** host ports — only Caddy is reachable from outside.

- [ ] **Step 2: Write `deploy/Caddyfile`**

```
{
	email {$ACME_EMAIL}
}

{$API_DOMAIN} {
	encode zstd gzip
	reverse_proxy web:8000
}
```

Caddy sets `X-Forwarded-Proto` automatically, which Task 3's `SECURE_PROXY_SSL_HEADER` depends on.

- [ ] **Step 3: Validate the compose file**

```bash
cd deploy && IMAGE_TAG=latest POSTGRES_PASSWORD=x ACME_EMAIL=x@y.z API_DOMAIN=api.example.com \
  docker compose -f compose.yml config >/dev/null && echo "compose OK"
```

Expected: `compose OK`.

- [ ] **Step 4: Remove the superseded example**

```bash
git rm compose.prod.example.yml
```

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: production compose stack and Caddyfile

Three services on one box: Caddy terminates TLS and proxies to
gunicorn, Postgres keeps its data on the separate EBS volume. Replaces
compose.prod.example.yml, whose healthcheck probed the wrong path."
```

---

## Task 9: `deploy.sh`

The only thing CI invokes. Converges the box to one git SHA, applies migrations separately from the cutover, and rolls the image back if the new one fails its healthcheck.

**Files:**
- Create: `deploy/deploy.sh` (mode 0755)

**Interfaces:**
- Consumes: `deploy/compose.yml`, `deploy/Caddyfile` from Task 8; SSM parameters under `/cidb/prod/` from Task 15.
- Produces: `/opt/cidb/deploy.sh <sha|main>`; exits 0 on success, non-zero on any failure. Writes `/opt/cidb/prod.env` (0600) and `/opt/cidb/.deployed-tag`.

- [ ] **Step 1: Write the script**

```bash
#!/bin/bash
set -euo pipefail

REPO="anorthall/incident-db"
APP_DIR="/opt/cidb"
IMAGE="ghcr.io/${REPO}"
REF="${1:-main}"
LOG="/var/log/cidb-deploy.log"

log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }

log "deploy starting: ref=${REF}"

SHA="$(curl -fsSL "https://api.github.com/repos/${REPO}/commits/${REF}" \
  -H "Accept: application/vnd.github.sha" )"
SHORT="${SHA:0:7}"
TAG="sha-${SHORT}"
log "resolved ${REF} -> ${SHA} (tag ${TAG})"

PREVIOUS_TAG="$(cat "${APP_DIR}/.deployed-tag" 2>/dev/null || echo "")"

for f in compose.yml Caddyfile backup.sh restore.sh; do
  curl -fsSL -o "${APP_DIR}/${f}" \
    "https://raw.githubusercontent.com/${REPO}/${SHA}/deploy/${f}"
done
chmod +x "${APP_DIR}/backup.sh" "${APP_DIR}/restore.sh"
log "fetched deploy files at ${SHORT}"

umask 077
{
  aws ssm get-parameters-by-path --path /cidb/prod --with-decryption --recursive \
    --query 'Parameters[].[Name,Value]' --output text \
  | while IFS=$'\t' read -r name value; do echo "${name##*/}=${value}"; done
  echo "IMAGE_TAG=${TAG}"
  echo "GIT_SHA=${SHA}"
} > "${APP_DIR}/prod.env"

POSTGRES_PASSWORD="$(grep '^POSTGRES_PASSWORD=' "${APP_DIR}/prod.env" | cut -d= -f2-)"
echo "DATABASE_URL=postgres://cidb:${POSTGRES_PASSWORD}@postgres:5432/cidb" \
  >> "${APP_DIR}/prod.env"
log "rendered prod.env ($(wc -l < "${APP_DIR}/prod.env") vars)"

cd "${APP_DIR}"
dc() { docker compose --env-file prod.env -f compose.yml "$@"; }

dc pull
dc up -d postgres
for _ in $(seq 1 30); do
  dc exec -T postgres pg_isready -U cidb -d cidb >/dev/null 2>&1 && break
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
    dc up -d web
  fi
  exit 1
fi

echo "$TAG" > "${APP_DIR}/.deployed-tag"
docker image prune -af --filter until=168h >/dev/null 2>&1 || true
log "deploy complete: ${TAG}"
```

Migrations run before the cutover deliberately: a failure at that step leaves the running site untouched. The rollback restores the previous **image** only — it does not reverse migrations.

- [ ] **Step 2: Shellcheck**

```bash
shellcheck deploy/deploy.sh && echo "shellcheck clean"
```

Expected: `shellcheck clean`. Fix any warning rather than suppressing it.

- [ ] **Step 3: Test idempotence and rollback locally**

This exercises Review Focus item 4 without an AWS account. Create `deploy/tests/test_deploy_sh.bats`-style coverage is overkill here; instead verify the two properties by inspection and a dry parse:

```bash
bash -n deploy/deploy.sh && echo "parses OK"
grep -c 'PREVIOUS_TAG' deploy/deploy.sh   # expect 3
grep -q 'exit 1' deploy/deploy.sh && echo "fails closed"
```

Expected: `parses OK`, `3`, `fails closed`. Confirm by reading that (a) re-running with the same SHA re-pulls and re-ups the same tag, which Docker Compose treats as a no-op, and (b) every failure path exits non-zero so the CI job goes red.

- [ ] **Step 4: Commit**

```bash
chmod +x deploy/deploy.sh
git add -A && git commit -m "feat: deploy script

Converges the box to one git SHA: fetches the matching compose file,
renders env from Parameter Store, migrates separately from the
cutover, and restores the previous image if the healthcheck fails."
```

---

## Task 10: Backup, restore and the systemd timer

**Files:**
- Create: `deploy/backup.sh`, `deploy/restore.sh` (mode 0755), `deploy/systemd/cidb-backup.service`, `deploy/systemd/cidb-backup.timer`

**Interfaces:**
- Consumes: `deploy/compose.yml` service names from Task 8; `BACKUP_BUCKET` and `SENTRY_CRON_URL` from `prod.env`.
- Produces: `s3://<BACKUP_BUCKET>/postgres/cidb-<UTC>.dump`; `restore.sh <s3-key|latest>`.

- [ ] **Step 1: Write `deploy/backup.sh`**

```bash
#!/bin/bash
set -euo pipefail

APP_DIR="/opt/cidb"
cd "$APP_DIR"
# shellcheck disable=SC1091
set -a; source prod.env; set +a

BUCKET="${BACKUP_BUCKET:?BACKUP_BUCKET not set}"
KEY="postgres/cidb-$(date -u +%Y%m%dT%H%M%SZ).dump"
CRON="${SENTRY_CRON_URL:-}"

checkin() { [ -n "$CRON" ] && curl -fsS -m 10 "${CRON}?status=$1" >/dev/null 2>&1 || true; }
fail() { echo "backup failed: $*" >&2; checkin error; exit 1; }

checkin in_progress

docker compose --env-file prod.env -f compose.yml exec -T postgres \
  pg_dump -U cidb -Fc cidb | aws s3 cp - "s3://${BUCKET}/${KEY}" \
  || fail "pg_dump or upload failed"

SIZE="$(aws s3api head-object --bucket "$BUCKET" --key "$KEY" \
  --query ContentLength --output text 2>/dev/null)" || fail "uploaded object not found"
[ "$SIZE" -gt 1000 ] || fail "uploaded dump is only ${SIZE} bytes"

echo "backup ok: s3://${BUCKET}/${KEY} (${SIZE} bytes)"
checkin ok
```

The `head-object` size check is Review Focus item 5: a pipeline whose `pg_dump` half fails can still create an empty object and exit 0 without it.

- [ ] **Step 2: Write `deploy/restore.sh`**

```bash
#!/bin/bash
set -euo pipefail

APP_DIR="/opt/cidb"
cd "$APP_DIR"
# shellcheck disable=SC1091
set -a; source prod.env; set +a

BUCKET="${BACKUP_BUCKET:?BACKUP_BUCKET not set}"
WHICH="${1:?usage: restore.sh <s3-key|latest>}"

if [ "$WHICH" = "latest" ]; then
  KEY="$(aws s3api list-objects-v2 --bucket "$BUCKET" --prefix postgres/ \
    --query 'sort_by(Contents,&LastModified)[-1].Key' --output text)"
else
  KEY="$WHICH"
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
```

- [ ] **Step 3: Write the systemd units**

`deploy/systemd/cidb-backup.service`:

```ini
[Unit]
Description=CIDB Postgres backup to S3
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/opt/cidb/backup.sh
```

`deploy/systemd/cidb-backup.timer`:

```ini
[Unit]
Description=Nightly CIDB Postgres backup

[Timer]
OnCalendar=*-*-* 03:00:00 UTC
Persistent=true

[Install]
WantedBy=timers.target
```

- [ ] **Step 4: Shellcheck both scripts**

```bash
shellcheck deploy/backup.sh deploy/restore.sh && echo "shellcheck clean"
```

Expected: `shellcheck clean`.

- [ ] **Step 5: Verify the size guard logic**

```bash
bash -n deploy/backup.sh deploy/restore.sh && echo "parse OK"
grep -q 'SIZE" -gt 1000' deploy/backup.sh && echo "empty-dump guard present"
grep -q 'confirm" = "yes"' deploy/restore.sh && echo "restore confirms"
```

Expected: all three lines print.

- [ ] **Step 6: Commit**

```bash
chmod +x deploy/backup.sh deploy/restore.sh
git add -A && git commit -m "feat: backup and restore scripts with a nightly timer

pg_dump streams straight to S3, the upload is size-checked so an empty
dump fails loudly, and Sentry Crons alerts on a missed or failed run."
```

---

## Task 11: cloud-init bootstrap

**Files:**
- Create: `deploy/cloud-init.yaml`

**Interfaces:**
- Consumes: `deploy/deploy.sh` from Task 9, systemd units from Task 10.
- Produces: a template with `${api_domain}` and `${compose_version}` placeholders for Terraform's `templatefile()` in Task 14. First boot ends with a deployed, running stack.

- [ ] **Step 1: Write `deploy/cloud-init.yaml`**

```yaml
#cloud-config
package_update: true
packages:
  - docker
  - dnf-automatic
  - git

write_files:
  - path: /etc/dnf/automatic.conf
    content: |
      [commands]
      upgrade_type = security
      apply_updates = yes
    append: false

runcmd:
  - systemctl enable --now docker
  - mkdir -p /usr/local/lib/docker/cli-plugins
  - curl -fsSL -o /usr/local/lib/docker/cli-plugins/docker-compose
    "https://github.com/docker/compose/releases/download/${compose_version}/docker-compose-linux-aarch64"
  - chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
  - systemctl enable --now dnf-automatic.timer
  - |
    if ! blkid /dev/sdf; then mkfs.ext4 -L cidb-data /dev/sdf; fi
  - mkdir -p /opt/cidb/data
  - |
    grep -q 'LABEL=cidb-data' /etc/fstab || \
      echo 'LABEL=cidb-data /opt/cidb/data ext4 defaults,nofail 0 2' >> /etc/fstab
  - mount -a
  - mkdir -p /opt/cidb/data/postgres /opt/cidb/data/caddy
  - curl -fsSL -o /opt/cidb/deploy.sh
    "https://raw.githubusercontent.com/anorthall/incident-db/main/deploy/deploy.sh"
  - chmod +x /opt/cidb/deploy.sh
  - curl -fsSL -o /etc/systemd/system/cidb-backup.service
    "https://raw.githubusercontent.com/anorthall/incident-db/main/deploy/systemd/cidb-backup.service"
  - curl -fsSL -o /etc/systemd/system/cidb-backup.timer
    "https://raw.githubusercontent.com/anorthall/incident-db/main/deploy/systemd/cidb-backup.timer"
  - systemctl daemon-reload
  - systemctl enable --now cidb-backup.timer
  - /opt/cidb/deploy.sh main
```

The device name is `/dev/sdf` to match the attachment in Task 14. On Nitro instances the kernel may expose it as `/dev/nvme1n1`; the `blkid`/`LABEL=` approach tolerates either because the label is what fstab mounts — but verify on first boot and adjust if `mount -a` fails.

- [ ] **Step 2: Validate the YAML**

```bash
uv run python -c "
import sys, yaml
d = yaml.safe_load(open('deploy/cloud-init.yaml'))
assert d['packages'], 'no packages'
assert any('deploy.sh main' in str(c) for c in d['runcmd']), 'no first deploy'
print('cloud-init YAML OK')
"
```

Expected: `cloud-init YAML OK`. If PyYAML is unavailable, `uv run --with pyyaml python -c ...`.

- [ ] **Step 3: Confirm the template placeholders**

```bash
grep -c '\${' deploy/cloud-init.yaml
```

Expected: `2` — `${compose_version}` and `${api_domain}`. If `${api_domain}` is not yet referenced, that is fine: Task 14 passes it and it may be unused in this file; remove it from the `templatefile()` call there instead of adding a fake reference here.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: cloud-init bootstrap for the application server

Installs Docker and the compose plugin, enables unattended security
updates, mounts the persistent data volume by label, installs the
backup timer and runs the first deploy."
```

---

## Task 12: Terraform — frontend bucket, OAC and lifecycle

**Files:**
- Modify: `tf/s3.tf`

**Interfaces:**
- Consumes: nothing.
- Produces: `module.frontend_bucket` (bucket `nss-incidents-frontend`), `aws_cloudfront_origin_access_control.s3` — both referenced by Task 13.

- [ ] **Step 1: Add the frontend bucket**

Append to `tf/s3.tf`, following the conventions of the existing modules exactly (same source, same version `5.10.0`):

```hcl
module "frontend_bucket" {
  source           = "terraform-aws-modules/s3-bucket/aws"
  bucket           = "nss-incidents-frontend"
  object_ownership = "BucketOwnerEnforced"
  attach_policy    = true
  policy           = data.aws_iam_policy_document.frontend_bucket_cloudfront_access.json
  version          = "5.10.0"

  versioning = {
    enabled = true
  }

  lifecycle_rule = [
    {
      id      = "DeleteOldVersions"
      enabled = true
      filter  = { prefix = "" }
      noncurrent_version_expiration = {
        days = 30
      }
    },
  ]
}
```

- [ ] **Step 2: Add the backups lifecycle**

In the existing `module "backup_bucket"`, add a current-version expiry to the existing rule list:

```hcl
    {
      id      = "ExpireOldBackups"
      enabled = true
      filter  = { prefix = "postgres/" }
      expiration = {
        days = 90
      }
    },
```

and change the existing `DeleteOldVersions` rule's `noncurrent_version_expiration.days` from `365` to `30`.

- [ ] **Step 3: Add the shared OAC and both bucket policies**

In `tf/cloudfront.tf` (kept with the distribution it serves), replace `aws_cloudfront_origin_access_identity.cdn` with:

```hcl
resource "aws_cloudfront_origin_access_control" "s3" {
  name                              = "cidb-s3-oac"
  description                       = "OAC for CIDB S3 origins"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}
```

In `tf/policies.tf`, replace `data.aws_iam_policy_document.cdn_bucket_cloudfront_access_policy` with two documents that grant `s3:GetObject` to the `cloudfront.amazonaws.com` service principal, conditioned on `AWS:SourceArn` equal to `aws_cloudfront_distribution.cdn.arn`:

```hcl
data "aws_iam_policy_document" "cdn_bucket_cloudfront_access_policy" {
  statement {
    sid       = "AllowCloudFrontCDNGetObject"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${module.cdn_bucket.s3_bucket_arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.cdn.arn]
    }
  }
}
```

and an identical `frontend_bucket_cloudfront_access` document against `module.frontend_bucket.s3_bucket_arn`.

- [ ] **Step 4: Format and validate**

```bash
cd tf && terraform fmt -check -recursive && terraform init -backend=false && terraform validate
```

Expected: `Success! The configuration is valid.` Do **not** run `terraform init` with the S3 backend (no credentials, and it would touch real state).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: frontend S3 bucket and Origin Access Control

Adds the private bucket the SPA is served from and moves both S3
origins to OAC, replacing the legacy OAI while the CDN bucket is still
empty and the change is risk-free."
```

---

## Task 13: Terraform — CloudFront rework

**Files:**
- Modify: `tf/cloudfront.tf`, `tf/variables.tf`, `tf/dns.tf`

**Interfaces:**
- Consumes: `module.frontend_bucket`, `aws_cloudfront_origin_access_control.s3` from Task 12.
- Produces: `aws_cloudfront_distribution.cdn` with five behaviours; `aws_cloudfront_distribution.cdn.id` consumed by Task 15's outputs.

- [ ] **Step 1: Add the SPA rewrite function**

```hcl
resource "aws_cloudfront_function" "spa_rewrite" {
  name    = "spa-rewrite"
  runtime = "cloudfront-js-2.0"
  publish = true
  code    = <<-EOF
    function handler(event) {
      var request = event.request;
      var last = request.uri.split('/').pop();
      if (last.indexOf('.') === -1) {
        request.uri = '/index.html';
      }
      return request;
    }
  EOF
}
```

This is attached to the default behaviour only, so API 404s are never rewritten into the SPA. Do **not** use `custom_error_response` — it applies distribution-wide and would break the API.

- [ ] **Step 2: Delete `strip_admin_prefix`**

Remove the `aws_cloudfront_function.strip_admin_prefix` resource and its `function_association` in the `/admin/*` behaviour. Django serves the admin at `/admin/`; stripping the prefix guarantees a 404.

- [ ] **Step 3: Fix the origin request policy**

In `aws_cloudfront_origin_request_policy.api_origin`, change the headers list to:

```hcl
    headers {
      items = ["Origin", "Accept", "Content-Type", "X-CSRFToken", "Referer"]
    }
```

Django's CSRF middleware needs both `X-CSRFToken` and `Referer` over HTTPS; without them every CSRF-protected POST fails with a 403 that looks nothing like a CDN problem.

- [ ] **Step 4: Rewrite the origins**

Replace the three `origin` blocks with two: the frontend bucket and the cdn bucket, both using `origin_access_control_id = aws_cloudfront_origin_access_control.s3.id` and no `s3_origin_config`; plus the existing api custom origin. Delete the `HTTP-NSSIncidentDB` origin entirely, and update `locals` so `frontend_origin_id` refers to the frontend S3 bucket.

- [ ] **Step 5: Rewrite the behaviours**

Five behaviours, all using policies instead of `forwarded_values`:

| Behaviour | Origin | `cache_policy_id` | `origin_request_policy_id` | Function |
|---|---|---|---|---|
| default | frontend S3 | managed `CachingOptimized` | — | `spa_rewrite` |
| `/cdn/*` | cdn S3 | managed `CachingOptimized` | — | `strip_cdn_prefix` |
| `/api/v1/*` | api | `api_cache` | `api_origin` | — |
| `/admin/*` | api | `api_cache` | `api_origin` | — |
| `/static/*` | api | `api_cache` | `api_origin` | — |

Look up the managed policy with a data source:

```hcl
data "aws_cloudfront_cache_policy" "caching_optimized" {
  name = "Managed-CachingOptimized"
}
```

`/api/v1/*`, `/admin/*` and `/static/*` need `allowed_methods = ["GET","HEAD","OPTIONS","PUT","POST","PATCH","DELETE"]`; the two S3 behaviours need only `["GET","HEAD","OPTIONS"]`. All five keep `viewer_protocol_policy = "redirect-to-https"` and `compress = true`. Remove every `forwarded_values` block and the now-unused `aws_cloudfront_cache_policy.default_with_query_strings`.

The `/static/*` behaviour is new and essential: without it the admin's CSS and JS fall through to the SPA bucket and the admin renders unstyled.

- [ ] **Step 6: Set the price class**

Change `price_class` from `"PriceClass_All"` to `"PriceClass_100"`.

- [ ] **Step 7: Remove the retired origin's DNS and variable**

In `tf/dns.tf`, delete `resource "aws_route53_record" "origin_dns_records"`. In `tf/variables.tf`, delete `variable "origin_domain_name"`.

- [ ] **Step 8: Format and validate**

```bash
cd tf && terraform fmt -recursive && terraform validate
```

Expected: valid. Then confirm the cleanup:

```bash
grep -c "forwarded_values" tf/cloudfront.tf     # expect 0
grep -c "strip_admin_prefix" tf/cloudfront.tf   # expect 0
grep -c "X-CSRFToken" tf/cloudfront.tf          # expect 1
grep -c "path_pattern" tf/cloudfront.tf         # expect 4
```

- [ ] **Step 9: Commit**

```bash
git add -A && git commit -m "feat: rework CloudFront for the S3-hosted SPA

Default behaviour now serves the frontend bucket with a viewer-request
function for deep links; adds the missing /static/* behaviour for admin
assets; forwards X-CSRFToken and Referer so CSRF works through the CDN;
removes the /admin prefix strip that made the admin unreachable; and
replaces the deprecated forwarded_values blocks with the cache and
origin request policies that were already defined but unused."
```

---

## Task 14: Terraform — right-sized instance and persistent data volume

**Files:**
- Modify: `tf/ec2.tf`, `tf/variables.tf`

**Interfaces:**
- Consumes: `deploy/cloud-init.yaml` from Task 11.
- Produces: `module.nss_incidents_ec2.id` consumed by Task 15's outputs and IAM scoping.

- [ ] **Step 1: Add the instance type variable**

In `tf/variables.tf`:

```hcl
variable "instance_type" {
  type        = string
  description = "EC2 instance type for the application server"
  default     = "t4g.small"
}
```

- [ ] **Step 2: Replace the AMI data source**

Replace the `data "aws_ami" "debian_13"` block with:

```hcl
data "aws_ssm_parameter" "al2023_arm64" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}
```

Amazon Linux 2023 ships the SSM agent and AWS CLI preinstalled, which the deploy path and operator access both depend on.

- [ ] **Step 3: Rework the instance module**

```hcl
module "nss_incidents_ec2" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "6.2.0"

  ami  = data.aws_ssm_parameter.al2023_arm64.value
  name = "nss-incidents"

  instance_type               = var.instance_type
  monitoring                  = true
  disable_api_stop            = true
  disable_api_termination     = true
  create_iam_instance_profile = true
  enable_primary_ipv6         = true
  ipv6_address_count          = 1

  iam_role_policies = {
    ssm = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
    app = aws_iam_policy.app.arn
  }

  subnet_id              = module.vpc.public_subnets[0]
  vpc_security_group_ids = [aws_security_group.nss_incidents_sg.id]

  user_data_replace_on_change = true
  user_data = templatefile("${path.module}/../deploy/cloud-init.yaml", {
    compose_version = "v2.40.3"
  })

  root_block_device = {
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }
}
```

Remove `key_name` and the `awscc_ec2_key_pair` resource — access is via Session Manager, so there is no SSH key to manage. `aws_iam_policy.app` is created in Task 15; if implementing this task first, add it there and validate then.

- [ ] **Step 4: Add the persistent data volume**

```hcl
resource "aws_ebs_volume" "data" {
  availability_zone = module.nss_incidents_ec2.availability_zone
  size              = 10
  type              = "gp3"
  encrypted         = true

  tags = {
    Name   = "nss-incidents-data"
    Backup = "cidb-data"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_volume_attachment" "data" {
  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.data.id
  instance_id = module.nss_incidents_ec2.id
}
```

`prevent_destroy` is what makes instance replacement safe: Postgres data and Caddy certificates survive.

- [ ] **Step 5: Remove SSH from the security group**

In `aws_security_group.nss_incidents_sg`, delete the port 22 ingress block and add UDP 443 for HTTP/3:

```hcl
  ingress {
    description      = "Allow HTTP/3"
    from_port        = 443
    to_port          = 443
    protocol         = "udp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
```

- [ ] **Step 6: Add the weekly snapshot policy**

```hcl
resource "aws_dlm_lifecycle_policy" "data_volume" {
  description        = "Weekly snapshots of the CIDB data volume"
  execution_role_arn = aws_iam_role.dlm.arn
  state              = "ENABLED"

  policy_details {
    resource_types = ["VOLUME"]
    target_tags    = { Backup = "cidb-data" }

    schedule {
      name = "weekly"

      create_rule {
        interval      = 168
        interval_unit = "HOURS"
        times         = ["04:00"]
      }

      retain_rule {
        count = 4
      }

      copy_tags = true
    }
  }
}
```

with a `aws_iam_role.dlm` trusting `dlm.amazonaws.com` and attaching `arn:aws:iam::aws:policy/service-role/AWSDataLifecycleManagerServiceRole`.

- [ ] **Step 7: Format and validate**

```bash
cd tf && terraform fmt -recursive && terraform validate
grep -c "from_port        = 22" ec2.tf   # expect 0
```

- [ ] **Step 8: Commit**

```bash
git add -A && git commit -m "feat: right-size the instance and add a persistent data volume

t4g.small on Amazon Linux 2023 replaces m8g.large on Debian, cutting
roughly \$65/month to \$12. Postgres data and Caddy certificates move to
a separate EBS volume with prevent_destroy so the instance can be
replaced freely, and SSH is removed in favour of Session Manager."
```

---

## Task 15: Terraform — IAM, Parameter Store and outputs

**Files:**
- Modify: `tf/iam.tf`
- Create: `tf/parameters.tf`, `tf/outputs.tf`
- Delete: `tf/secrets.tf`

**Interfaces:**
- Consumes: `module.nss_incidents_ec2.id`, `module.frontend_bucket`, `aws_cloudfront_distribution.cdn.id`.
- Produces: `aws_iam_policy.app` (used by Task 14); outputs `instance_id`, `deploy_role_arn`, `cloudfront_distribution_id`, `frontend_bucket` — these are the six GitHub environment variables in Task 17/18.

- [ ] **Step 1: Replace the IAM user with an instance policy**

Delete `aws_iam_user.app`, `aws_iam_user_policy_attachment.*`, `aws_iam_access_key.app` and both outputs. Add a single `aws_iam_policy.app` combining: cdn bucket read/write, data bucket read, backups bucket read/write, `ssm:GetParametersByPath` + `ssm:GetParameters` on `arn:aws:ssm:us-west-2:*:parameter/cidb/prod/*`, and `kms:Decrypt` on the account's `aws/ssm` key. Reuse the existing `aws_iam_policy.s3_read` / `s3_write` documents where they fit rather than duplicating their statements.

- [ ] **Step 2: Add the GitHub OIDC provider and deploy role**

```hcl
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]  # pragma: allowlist secret
}

data "aws_iam_policy_document" "github_deploy_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:anorthall/incident-db:environment:production"]
    }
  }
}
```

The role's inline policy allows exactly: `s3:ListBucket` on the frontend bucket, `s3:PutObject`/`s3:DeleteObject` on its objects, `cloudfront:CreateInvalidation` on the distribution ARN, `ssm:SendCommand` on the instance ARN **and** `arn:aws:ssm:us-west-2::document/AWS-RunShellScript`, plus `ssm:GetCommandInvocation` and `ssm:ListCommands` on `*` (neither supports resource-level permissions).

- [ ] **Step 3: Create `tf/parameters.tf`**

One `aws_ssm_parameter` per key. SecureString: `SECRET_KEY`, `POSTGRES_PASSWORD`, `SENTRY_DSN`, `LOGFIRE_TOKEN`, `OPENAI_API_KEY`, `SENTRY_CRON_URL`. String: `DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, `AWS_S3_CUSTOM_DOMAIN`, `ACME_EMAIL`, `API_DOMAIN`, `BACKUP_BUCKET`, `WEB_CONCURRENCY`.

Every parameter carries a placeholder value and:

```hcl
  lifecycle {
    ignore_changes = [value]
  }
```

so real values are set once by CLI and never enter state or the repo. Use a `for_each` over two maps (one per tier) rather than sixteen near-identical resources.

- [ ] **Step 4: Create `tf/outputs.tf`**

```hcl
output "instance_id" {
  description = "EC2 instance ID for SSM commands and sessions"
  value       = module.nss_incidents_ec2.id
}

output "deploy_role_arn" {
  description = "IAM role ARN that GitHub Actions assumes via OIDC"
  value       = aws_iam_role.github_deploy.arn
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID for invalidations"
  value       = aws_cloudfront_distribution.cdn.id
}

output "frontend_bucket" {
  description = "S3 bucket the SPA is synced to"
  value       = module.frontend_bucket.s3_bucket_id
}
```

- [ ] **Step 5: Delete the unused Secrets Manager entries**

```bash
git rm tf/secrets.tf
```

They were never populated and never read, and cost $0.40/secret/month.

- [ ] **Step 6: Format and validate**

```bash
cd tf && terraform fmt -recursive && terraform init -backend=false && terraform validate
grep -rc "aws_iam_access_key" . | grep -v ":0" || echo "no static access keys"
```

Expected: valid; `no static access keys`.

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "feat: instance role, GitHub OIDC and Parameter Store

Replaces the static IAM access key with the EC2 instance profile and
gives GitHub Actions a scoped OIDC role, so there is nothing to
rotate. Secrets move from unused Secrets Manager entries to Parameter
Store, declared in Terraform but with values set out of band."
```

---

## Task 16: Gate mypy and infrastructure checks in CI

**Files:**
- Modify: `.github/workflows/lint.yaml`
- Create: `.github/workflows/infra-checks.yaml`

**Interfaces:**
- Consumes: a clean mypy from Task 5, shellcheck-clean scripts from Tasks 9–10, valid terraform from Tasks 12–15.
- Produces: `lint.yaml` remains `workflow_call`-able by Task 17.

- [ ] **Step 1: Add mypy to `lint.yaml`**

After the existing `Ruff format` step, add a job (or step in the same job) that runs mypy with the environment Django needs:

```yaml
      - name: Mypy
        run: mypy ./
        env:
          DEBUG: "true"
          SECRET_KEY: "ci"  # pragma: allowlist secret
          PYTHONPATH: ${{ github.workspace }}:${{ github.workspace }}/cidb
          DJANGO_SETTINGS_MODULE: cidb.conf.settings
```

Use `mypy`, not `dmypy` — there is no daemon to reuse in CI.

- [ ] **Step 2: Create `.github/workflows/infra-checks.yaml`**

```yaml
name: Infra Checks

on:
  workflow_call:
  workflow_dispatch:
  pull_request:
    paths:
      - "tf/**"
      - "deploy/**"

jobs:
  terraform:
    name: Terraform
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.14.3
      - name: Format check
        run: terraform -chdir=tf fmt -check -recursive
      - name: Validate
        run: |
          terraform -chdir=tf init -backend=false
          terraform -chdir=tf validate

  shellcheck:
    name: Shellcheck
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - run: shellcheck deploy/*.sh
```

`-backend=false` keeps CI away from real state and needs no credentials.

- [ ] **Step 3: Validate the workflow syntax**

```bash
uv run --with pyyaml python -c "
import yaml
for f in ['.github/workflows/lint.yaml', '.github/workflows/infra-checks.yaml']:
    yaml.safe_load(open(f)); print(f, 'OK')
"
```

- [ ] **Step 4: Verify the checks pass locally**

```bash
cd tf && terraform fmt -check -recursive && terraform validate && cd ..
shellcheck deploy/*.sh
uv run mypy ./
```

Expected: all clean.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "ci: gate mypy, terraform and shellcheck

CI ran ruff only, which is how twelve mypy errors accumulated
unnoticed. Adds terraform fmt/validate and shellcheck for the new
infrastructure code."
```

---

## Task 17: Backend build and deploy workflow

**Files:**
- Create: `.github/workflows/deploy-backend.yaml`
- Delete: `.github/workflows/container.yaml`

**Interfaces:**
- Consumes: `deploy.sh` at `/opt/cidb/deploy.sh` (Task 9); environment variables `AWS_DEPLOY_ROLE_ARN`, `EC2_INSTANCE_ID` (Task 15 outputs).
- Produces: image tags `sha-<7>` and `latest` on `ghcr.io/anorthall/incident-db`.

- [ ] **Step 1: Write the workflow**

```yaml
name: Deploy Backend

on:
  push:
    branches: [main]
    paths-ignore:
      - "frontend/**"
      - "docs/**"
      - "**.md"
  workflow_dispatch:
    inputs:
      sha:
        description: "Commit SHA to deploy (defaults to the current commit)"
        required: false
        type: string

concurrency:
  group: deploy-backend
  cancel-in-progress: false

permissions:
  contents: read
  packages: write

jobs:
  backend-tests:
    uses: ./.github/workflows/backend-tests.yaml
  frontend-tests:
    uses: ./.github/workflows/frontend-tests.yaml
  lint:
    uses: ./.github/workflows/lint.yaml
  infra:
    uses: ./.github/workflows/infra-checks.yaml

  build:
    name: Build and Push Image
    needs: [backend-tests, frontend-tests, lint, infra]
    runs-on: ubuntu-24.04-arm
    steps:
      - uses: actions/checkout@v6
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=raw,value=latest
            type=sha,prefix=sha-,format=short
      - uses: docker/build-push-action@v6
        with:
          context: .
          platforms: linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    name: Deploy
    needs: [build]
    runs-on: ubuntu-latest
    environment: production
    if: vars.EC2_INSTANCE_ID != ''
    timeout-minutes: 10
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.AWS_DEPLOY_ROLE_ARN }}
          aws-region: us-west-2
      - name: Run deploy.sh via SSM
        run: |
          set -euo pipefail
          SHA="${{ inputs.sha || github.sha }}"
          CMD=$(aws ssm send-command \
            --instance-ids "${{ vars.EC2_INSTANCE_ID }}" \
            --document-name AWS-RunShellScript \
            --comment "deploy $SHA" \
            --parameters "commands=[\"/opt/cidb/deploy.sh $SHA\"]" \
            --query Command.CommandId --output text)
          echo "command: $CMD"
          for _ in $(seq 1 60); do
            STATUS=$(aws ssm get-command-invocation --command-id "$CMD" \
              --instance-id "${{ vars.EC2_INSTANCE_ID }}" \
              --query Status --output text 2>/dev/null || echo Pending)
            case "$STATUS" in
              Success|Failed|Cancelled|TimedOut) break ;;
            esac
            sleep 10
          done
          aws ssm get-command-invocation --command-id "$CMD" \
            --instance-id "${{ vars.EC2_INSTANCE_ID }}" \
            --query StandardOutputContent --output text
          aws ssm get-command-invocation --command-id "$CMD" \
            --instance-id "${{ vars.EC2_INSTANCE_ID }}" \
            --query StandardErrorContent --output text >&2
          echo "final status: $STATUS"
          [ "$STATUS" = "Success" ]
```

The `if: vars.EC2_INSTANCE_ID != ''` guard means this can merge safely before the infrastructure exists.

- [ ] **Step 2: Delete the superseded workflow**

```bash
git rm .github/workflows/container.yaml
```

- [ ] **Step 3: Validate**

```bash
uv run --with pyyaml python -c "
import yaml; d=yaml.safe_load(open('.github/workflows/deploy-backend.yaml'))
assert d['jobs']['build']['runs-on']=='ubuntu-24.04-arm'
assert 'linux/arm64' in str(d['jobs']['build']['steps'])
print('deploy-backend OK')
"
```

Expected: `deploy-backend OK`. The arm64 assertion matters — an amd64 image cannot run on the Graviton instance, which is the single hard blocker this whole plan exists to clear.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "ci: build arm64 and deploy via SSM

Builds natively on GitHub's arm64 runner so the image can run on the
Graviton instance, then deploys by sending one SSM command. No SSH key
and no AWS credentials are stored in GitHub."
```

---

## Task 18: Frontend deploy workflow

**Files:**
- Create: `.github/workflows/deploy-frontend.yaml`

**Interfaces:**
- Consumes: `FRONTEND_BUCKET`, `CLOUDFRONT_DISTRIBUTION_ID`, `AWS_DEPLOY_ROLE_ARN`, `VITE_SENTRY_DSN`, `VITE_TAG_MANAGER_ID`.
- Produces: the SPA in S3; an invalidation of `/index.html` and `/`.

- [ ] **Step 1: Write the workflow**

Triggers on push to `main` touching `frontend/**`, plus `workflow_dispatch`. After `frontend-tests`, a `deploy` job with `environment: production`, `if: vars.FRONTEND_BUCKET != ''`, `id-token: write`, that builds with pnpm 10.30.3 / Node 22 (matching `frontend-tests.yaml`) and then runs these four steps **in this order**:

```bash
aws s3 sync dist/assets/ "s3://$BUCKET/assets/" \
  --cache-control "public, max-age=31536000, immutable"

aws s3 sync dist/ "s3://$BUCKET/" --exclude "assets/*" \
  --cache-control "no-cache"

aws cloudfront create-invalidation --distribution-id "$DIST" \
  --paths "/index.html" "/"

aws s3 sync dist/assets/ "s3://$BUCKET/assets/" --delete
```

The order is the point: hashed assets are uploaded before the HTML that references them, and old assets are deleted only after the invalidation, so a failure at any step leaves a working site.

Pass the two `VITE_*` values as build env from `vars`.

- [ ] **Step 2: Validate**

```bash
uv run --with pyyaml python -c "
import yaml; d=yaml.safe_load(open('.github/workflows/deploy-frontend.yaml'))
s=str(d); assert 'create-invalidation' in s and '--delete' in s
print('deploy-frontend OK')
"
```

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "ci: build and deploy the SPA to S3

Uploads hashed assets before the HTML that references them and prunes
old assets only after the invalidation, so a failed deploy leaves a
working site."
```

---

## Task 19: Operator commands and documentation

**Files:**
- Modify: `justfile`, `README.md`

**Interfaces:**
- Consumes: `instance_id` from Task 15.
- Produces: `just prod-shell`, `just prod-manage <args>`.

- [ ] **Step 1: Add the justfile recipes**

```make
prod-shell:
    aws ssm start-session --target "$CIDB_PROD_INSTANCE_ID"

prod-manage +ARGS:
    aws ssm send-command \
      --instance-ids "$CIDB_PROD_INSTANCE_ID" \
      --document-name AWS-RunShellScript \
      --parameters 'commands=["cd /opt/cidb && docker compose --env-file prod.env -f compose.yml exec -T web python cidb/manage.py {{ ARGS }}"]' \
      --query Command.CommandId --output text
```

`CIDB_PROD_INSTANCE_ID` comes from `secrets.env`, which `.envrc` already sources and `.gitignore` already excludes.

- [ ] **Step 2: Rewrite the README deployment section**

Replace the "Django application" paragraph's claim that it runs "using docker-compose (or Dokku in production)" — that is no longer true. Describe: production runs on AWS at `incidents.caves.org`; deploys happen automatically on merge to `main`; the design is in `docs/superpowers/specs/2026-09-27-aws-deployment-design.md`; the server's configuration is `deploy/`; routine operations are the runbook table from the spec's §14.

- [ ] **Step 3: Verify the justfile parses**

```bash
just --list | grep -E "prod-shell|prod-manage"
```

Expected: both recipes listed.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "docs: operator commands and deployment documentation

Adds just prod-shell and prod-manage wrapping Session Manager, and
replaces the stale Dokku reference in the README."
```

---

## Final verification

After every task, from a clean tree:

- [ ] `uv run pytest -q` → all tests pass (77+)
- [ ] `cd frontend/cidb && ./node_modules/.bin/vitest run` → 32 pass
- [ ] `just lint` → ruff clean, mypy `Success: no issues found`
- [ ] `cd tf && terraform fmt -check -recursive && terraform validate` → valid
- [ ] `shellcheck deploy/*.sh` → clean
- [ ] `cd frontend/cidb && ./node_modules/.bin/vite build` → succeeds, `dist/` has the brand assets
- [ ] `grep -rn "cidb\.dev" frontend/cidb/src frontend/cidb/index.html | grep -v mailto` → no output
- [ ] `git grep -n "valkey\|Valkey" -- ':!uv.lock' ':!docs'` → no output

## Out of scope — manual steps for the operator

These need AWS credentials and are not part of this plan:

1. `terraform apply` with the `cidb-nss` profile, after reading the plan carefully.
2. `aws ssm put-parameter --overwrite` for each of the sixteen real values.
3. Create the GitHub `production` environment and set the six variables from the Terraform outputs.
4. The Hetzner → AWS data migration, using `restore.sh`.
5. Verification checklist §13 of the spec against the live site.
