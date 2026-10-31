# CIDB production deployment on AWS — design

**Date:** 2026-09-27
**Status:** approved in discussion; awaiting written review
**Target:** `incidents.caves.org` on the NSS AWS account (us-west-2)

## 1. Goal

Run CIDB v2 (the current `main`) in production on the NSS AWS account at
`incidents.caves.org`, deployed automatically from GitHub on every merge to
`main`, at the lowest cost and operational burden consistent with keeping an
irreplaceable dataset safe.

### In scope

- Terraform for all AWS resources, reworking the existing `tf/` directory.
- Scripts that provision, deploy to, back up and restore the application server.
- GitHub Actions workflows that build, test and deploy backend and frontend.
- The application changes required for the app to run correctly in this
  environment.
- A runbook for routine operation and a first-deploy sequence.

### Out of scope (deferred, deliberately)

- Migrating the live data from the Hetzner box (`api.cidb.dev`, `tide.caver.dev`).
  This is a manual step using the restore tooling this design provides.
- The future of `cidb.dev` and the Hetzner server. Both are left untouched.
- RDS. Priced in §16 as an upgrade; NSS's call.
- Running `terraform apply` from CI.
- API rate limiting / WAF.

## 2. Context

### What exists today

- **`cidb.dev`** (the live site): CloudFront → S3 for the SPA (bundle dated
  2025-12-29), `api.cidb.dev` → a Hetzner server behind Caddy. Both are a
  pre-merge build from ~December 2025 — the v2 merge (2026-03-02) has never
  been deployed anywhere.
- **`incidents.caves.org`** (NSS AWS, described by `tf/`): CloudFront, ACM
  wildcard certificate, Route53 zone, four S3 buckets and an `m8g.large` EC2
  instance are provisioned. Nothing has ever been deployed: `/` → 404,
  `/api/v1/*` → 502, the CDN bucket is empty.
- **CI** builds and pushes `ghcr.io/anorthall/incident-db` on push to `main`.
  Nothing consumes the image.

### Defects in the existing setup that this design fixes

| Defect | Where | Consequence |
|---|---|---|
| Image built for amd64 only | `.github/workflows/container.yaml` | Cannot run on the Graviton (arm64) instance |
| `/admin/*` behaviour strips the `/admin` prefix before forwarding | `tf/cloudfront.tf` | Django admin can never load through CloudFront |
| No `/static/*` behaviour | `tf/cloudfront.tf` | Admin CSS/JS would fall through to the SPA bucket |
| Origin request policy omits `X-CSRFToken` and `Referer` | `tf/cloudfront.tf` | Every CSRF-protected POST (login, reports, feedback) fails with 403 |
| Three cache/origin-request policies defined but unused; behaviours use legacy `forwarded_values` | `tf/cloudfront.tf` | Dead code; deprecated configuration |
| Static IAM access key for the app | `tf/iam.tf` | Long-lived credential to rotate; the instance role can do this |
| Secrets Manager secrets created, never populated, never read | `tf/secrets.tf` | $0.40/secret/month for nothing |
| `run.sh start` never runs `migrate` | `cidb/conf/run.sh` | Deploys cannot apply migrations |
| Healthcheck probes `/healthcheck/` | `compose.prod.example.yml` | Route is `/core/healthcheck/`; the check always fails |
| Unrouted paths return 500, not 404 | **deployed build only** — not `main` (see §18) | CDN and monitoring cannot distinguish "missing" from "broken" |
| `AWS_S3_ACCESS_KEY_ID` defaults to `""` | `cidb/conf/settings.py` | Prevents boto3 falling back to the instance role |
| Eleven `https://cidb.dev/cdn/assets/…` URLs hard-coded | `frontend/cidb/src/constants.ts`, `index.html` | caves.org would load its branding from cidb.dev |
| Valkey configured as the Django cache | `cidb/conf/settings.py`, compose | No code calls the cache; sessions are DB-backed. Pure overhead |
| `just mypy` red (12 errors); CI lint runs ruff only | `pyproject.toml`, `lint.yaml` | Type errors accumulate unnoticed |

### What the application needs

| Need | Evidence | Implication |
|---|---|---|
| One small WSGI container | gunicorn, stateless, 11k LOC | Any container host; no autoscaling |
| Small Postgres with full-text search | `SearchVectorField`; embeddings are `ArrayField(FloatField)`, not pgvector; last dump 1.1 MB compressed | Stock `postgres:18`; restores in seconds |
| No cache service | Zero `cache.*` calls; sessions in DB | Drop Valkey; `LocMemCache` satisfies Django |
| No queue or workers | LLM operations are management commands run by hand | No Celery, no scheduler |
| Object storage for media | `Publication.image` / `.pdf` via django-storages | S3 behind CloudFront |
| Static SPA, same-origin API | Vite bundle; no `VITE_API_URL` | S3 + CloudFront |
| Django admin through the CDN | `/admin/` + whitenoise `/static/` | Two CloudFront behaviours; cookies and CSRF headers forwarded |
| Outbound to OpenAI, Sentry, Logfire | pydantic-ai, SDKs | Cheap internet egress; anything forcing a NAT gateway is disqualified |
| An operator shell | `run_data_operations`, `generate_embeddings`, `merge_duplicates` | Must be trivial to `exec` into the running container |

## 3. Options considered

Approximate us-west-2 on-demand monthly costs; verify in the AWS pricing
calculator before quoting.

| Option | ≈ $/mo | Operating it | Verdict |
|---|---|---|---|
| **A. One Graviton EC2 (`t4g.small`), Docker Compose: web + postgres + Caddy** | **~21** (~16 with a 1-yr no-upfront savings plan; ~33 on `t4g.medium`) | One box, one compose file; `manage.py` one SSM session away; self-managed Postgres with daily dumps to S3 and weekly volume snapshots | **Chosen** |
| A+. As A, plus RDS `db.t4g.micro` | ~35–47 | Managed backups, PITR, major-version upgrades | Available upgrade; deferred to NSS |
| B. App Runner + RDS | ~30–45 **+ ~32 NAT** | A VPC connector routes all egress through the VPC, so OpenAI/Sentry need a NAT gateway or RDS must be public; no exec for `manage.py` | Rejected: hidden NAT cost, awkward ops |
| C. ECS Fargate + ALB + RDS | ~57+ | Cluster, task definitions, service, ALB, target groups, ECR, log groups; ALB alone ~$16 plus two IPv4 addresses | Rejected: most moving parts for the least benefit at this scale |
| D. Lightsail containers + Lightsail DB | ~27 | Cheap and managed, but a walled garden: weak Terraform/IAM/VPC integration, no exec | Viable fallback; not chosen for an account NSS must own long-term |
| E. Lambda (Web Adapter) + RDS/Aurora | ~14–45 | Cold starts, container packaging, `manage.py` from a laptop against a public DB; Aurora Serverless cannot idle under crawler traffic | Rejected: wrong shape for Django with hands-on data operations |

**Why A:** it is the cheapest by a margin, the simplest to hand over ("a
Docker Compose file on one server" needs no explanation), and the only option
that keeps the data-operations workflow trivial. Its weakness — one box with
self-managed Postgres — is mitigated by the SPA staying up from S3/CloudFront
when the box is down, a database that restores in seconds, and versioned
backups to a bucket that already exists.

## 4. Architecture

```
incidents.caves.org  (Route53 alias → CloudFront, ACM wildcard cert)
│
├─ /              → S3  nss-incidents-frontend   (OAC; viewer-request function
│                                                 rewrites extension-less paths
│                                                 to /index.html)
├─ /cdn/*         → S3  nss-incidents-cdn        (OAC; strip-cdn-prefix function;
│                                                 Django media under media/)
├─ /api/v1/*  ┐
├─ /admin/*   ├→ api.incidents.caves.org  (EIP → EC2)
└─ /static/*  ┘
                        EC2 t4g.small, Amazon Linux 2023 arm64
                        ┌──────────────────────────────────────────┐
                        │ caddy:2      :80/:443, Let's Encrypt     │
                        │   └─ reverse_proxy web:8000              │
                        │ web          ghcr.io/anorthall/incident-db│
                        │              :sha-<short>, gunicorn ×3   │
                        │ postgres:18                              │
                        │ data volume  /opt/cidb/data  (10 GB gp3, │
                        │              survives instance replacement)│
                        └──────────────────────────────────────────┘
                              │ instance role
                              ├─ S3 cdn (rw), data (ro), backups (rw)
                              ├─ SSM Parameter Store /cidb/prod/* (ro)
                              └─ SSM agent (Session Manager, Run Command)

GitHub Actions ──OIDC──► deploy role ──► ssm:SendCommand  deploy.sh <sha>
                                     ──► s3 sync (frontend), CreateInvalidation
```

## 5. Edge: CloudFront, S3, ACM, Route53

**Unchanged:** the Route53 zone and delegation set, the `incidents` and `api`
records, the ACM wildcard certificate (`acm.tf`), the `strip_cdn_prefix`
function, the `cdn`, `data`, `backups` and `tfstate` buckets.

**New bucket** `nss-incidents-frontend`: private, `BucketOwnerEnforced`,
versioning on, noncurrent versions expire after 30 days. Same module and
conventions as the existing buckets.

**Origin access:** both S3 origins use Origin Access Control. The CDN bucket
migrates from the legacy OAI to OAC now, while it is empty and the change is
risk-free. The OAI resource is deleted. Bucket policies grant
`s3:GetObject` to `cloudfront.amazonaws.com` conditioned on the
distribution's ARN.

**Distribution changes:**

| Behaviour | Origin | Cache policy | Origin request policy | Functions |
|---|---|---|---|---|
| default | frontend bucket | managed `CachingOptimized` | — | viewer-request `spa_rewrite` |
| `/cdn/*` | cdn bucket | managed `CachingOptimized` | — | viewer-request `strip_cdn_prefix` |
| `/api/v1/*` | api origin | `api_cache` (TTL 0/0/86400, no cookies in key) | `api_origin` | — |
| `/admin/*` | api origin | `api_cache` | `api_origin` | — |
| `/static/*` | api origin | `api_cache` | `api_origin` | — |

- `spa_rewrite` (new CloudFront Function): if the last path segment contains
  no `.`, set the URI to `/index.html`. This is attached to the default
  behaviour only, so API 404s are never rewritten. No `custom_error_response`
  blocks are used — they apply distribution-wide and would turn API 404s into
  the SPA.
- `strip_admin_prefix` is deleted, with its association.
- `api_origin` headers whitelist becomes: `Origin`, `Accept`, `Content-Type`,
  `X-CSRFToken`, `Referer`. Cookies: all. Query strings: all.
- `default_with_query_strings` cache policy is deleted (unused after this
  change).
- All legacy `forwarded_values` blocks are removed.
- `price_class` becomes `PriceClass_100`.
- The `HTTP-NSSIncidentDB` origin, the `origin_domain_name` variable and the
  `origin_dns_records` are deleted.

**Media URLs:** the app sets `AWS_S3_CUSTOM_DOMAIN=incidents.caves.org/cdn`,
so `MEDIA_URL` resolves to `https://incidents.caves.org/cdn/media/` and
`strip_cdn_prefix` maps it onto the `media/` prefix in the CDN bucket.

## 6. Compute

- **Instance:** `t4g.small` (2 vCPU, 2 GB, arm64). Variable, so `t4g.medium`
  is a one-line change.
- **AMI:** latest Amazon Linux 2023 arm64, via the public SSM parameter
  `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64`.
  Chosen over Debian because the SSM agent and AWS CLI are preinstalled,
  `dnf-automatic` handles security updates and kernel live patching avoids
  reboots.
- **Root volume:** 20 GB gp3, destroyed with the instance.
- **Data volume:** 10 GB gp3, separate `aws_ebs_volume` with
  `prevent_destroy`, attached at `/dev/sdf`, mounted at `/opt/cidb/data`.
  Holds Postgres data and Caddy certificates. Survives instance replacement.
- **Elastic IP:** the existing resource, reassociated on replacement; DNS does
  not change.
- **Security group:** inbound TCP 80, TCP 443, UDP 443 from `0.0.0.0/0` and
  `::/0`. **No port 22.** All egress.
- **Instance profile:** created by the EC2 module; policies in §7.
- **`user_data`:** rendered from `deploy/cloud-init.yaml` by `templatefile()`;
  `user_data_replace_on_change = true`, so editing cloud-init deliberately
  replaces the instance.
- **Snapshots:** Data Lifecycle Manager policy on the data volume (tag
  `Backup=cidb-data`), weekly, retain 4.

## 7. Identity and secrets

**Instance role** (attached via the EC2 module's `iam_role_policies`):

- `AmazonSSMManagedInstanceCore` (Session Manager, Run Command).
- `cidb-app` policy: cdn bucket read/write; data bucket read; backups bucket
  read/write; `ssm:GetParametersByPath`, `ssm:GetParameters` on
  `arn:aws:ssm:us-west-2:*:parameter/cidb/prod/*`; `kms:Decrypt` on the
  account's `aws/ssm` key.

**GitHub OIDC:** `aws_iam_openid_connect_provider` for
`token.actions.githubusercontent.com`, and a `cidb-github-deploy` role trusted
for `sub = repo:anorthall/incident-db:environment:production`,
`aud = sts.amazonaws.com`. Permissions:

- `s3:ListBucket`, `s3:PutObject`, `s3:DeleteObject` on the frontend bucket.
- `cloudfront:CreateInvalidation` on the distribution.
- `ssm:SendCommand` on the instance ARN and on
  `arn:aws:ssm:*::document/AWS-RunShellScript`; `ssm:GetCommandInvocation`,
  `ssm:ListCommands`.

**Deleted:** `aws_iam_user.app`, `aws_iam_access_key.app` and their outputs;
all of `secrets.tf`.

**Parameter Store** (`/cidb/prod/<KEY>`), declared in Terraform with
`ignore_changes = [value]`; values set once by CLI and never stored in state
or the repo:

| Key | Type |
|---|---|
| `SECRET_KEY`, `POSTGRES_PASSWORD`, `SENTRY_DSN`, `LOGFIRE_TOKEN`, `OPENAI_API_KEY`, `SENTRY_CRON_URL` | SecureString |
| `DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, `AWS_S3_CUSTOM_DOMAIN`, `ACME_EMAIL`, `WEB_CONCURRENCY` | String |

`DATABASE_URL` is not stored; `deploy.sh` composes
`postgres://cidb:${POSTGRES_PASSWORD}@postgres:5432/cidb`.

Two constraints on this list:

- **Never add `DJANGO_SETTINGS_MODULE`.** Compose's `env_file` overrides the
  image's `ENV`, so a parameter of that name would silently take precedence
  over the Dockerfile and could reintroduce the dual-import split that §10
  removed. `cidb/manage.py` sets no default of its own, so the container
  environment is the only thing deciding it.
- **Values are not quoted.** `prod.env` is read three ways — `source`,
  `--env-file` and compose's `env_file` — which disagree about quoting and
  escaping. The current values are all simple, but a value containing spaces,
  quotes or `#` needs checking against all three before it is set.

## 8. The server

### Division of labour

Terraform **provisions** (instance, volume, EIP, security group, role,
parameters). cloud-init **bootstraps** once. `deploy.sh` **converges** the
application to a git SHA. `backup.sh` and `restore.sh` **move data**. Nothing
on the box exists outside the repo or Parameter Store; a rebuild is
`tofu apply` plus one deploy.

### Files

```
deploy/
  cloud-init.yaml                 rendered by terraform; runs once on first boot
  compose.yml                     web + postgres + caddy
  Caddyfile
  deploy.sh                       deploy.sh <sha> — the only thing CI calls
  backup.sh                       pg_dump -Fc → s3://nss-incidents-backups/postgres/
  restore.sh                      restore.sh <s3-key|latest>; manual; confirms first
  systemd/cidb-backup.service
  systemd/cidb-backup.timer
```

On the box:

```
/opt/cidb/
  compose.yml Caddyfile deploy.sh backup.sh restore.sh
  prod.env                        mode 0600, rendered by deploy.sh
  data/                           ← separate EBS volume
    postgres/
    caddy/
```

### `cloud-init.yaml`

1. `dnf install docker`; enable and start it.
2. Install the Docker Compose CLI plugin as a pinned arm64 release binary into
   `/usr/local/lib/docker/cli-plugins/` (AL2023 does not package it). The
   version is pinned in the file and bumped deliberately.
3. Enable `dnf-automatic` (security updates) and `kpatch` (kernel live
   patching).
4. If the data volume has no filesystem, create ext4 on it. Add an fstab entry
   by UUID and mount at `/opt/cidb/data`.
5. Create `/opt/cidb`; fetch `deploy/deploy.sh` at `main` from
   `raw.githubusercontent.com`; install the systemd timer.
6. Run `deploy.sh main`.

### `deploy.sh <sha>`

`set -euo pipefail`; logs to stdout (captured by SSM into the CI job) and
`/var/log/cidb-deploy.log`. Idempotent. Steps, each aborting on failure:

1. Resolve `<sha>` (or `main`) to a full commit via the GitHub API; derive
   `IMAGE_TAG=sha-<7 chars>`.
2. Fetch `deploy/{compose.yml,Caddyfile,backup.sh,restore.sh}` at that commit
   into `/opt/cidb/`, so the compose file always matches the image. Also fetch
   `deploy/systemd/*` into `/etc/systemd/system/`, and only when a unit has
   actually changed, `daemon-reload` and reload the timer — so the backup
   schedule can be changed by a deploy rather than an instance replacement.
3. Render `prod.env` from `aws ssm get-parameters-by-path --path /cidb/prod
   --with-decryption`, add `IMAGE_TAG`, `GIT_SHA`, `DATABASE_URL`. Record the
   previously deployed tag as `PREVIOUS_IMAGE_TAG`.
4. `docker compose pull`.
5. `docker compose up -d postgres`; wait for `pg_isready`.
6. `docker compose run --rm web python cidb/manage.py migrate --noinput`.
   Failure here leaves the running site untouched.
7. `docker compose up -d`; poll `/core/healthcheck/` inside the `web`
   container for up to 60 s.
8. **On healthcheck failure:** `IMAGE_TAG=$PREVIOUS_IMAGE_TAG docker compose up
   -d web`, then exit 1. Migrations are not reversed — a known limit, which is
   why step 6 runs first and separately.
9. `docker image prune -af --filter until=168h`.

Rollback at any other time is `deploy.sh <older-sha>`.

### `compose.yml`

- `web`: `ghcr.io/anorthall/incident-db:${IMAGE_TAG}`, `env_file: prod.env`,
  no host ports, healthcheck on `/core/healthcheck/`, `depends_on: postgres:
  condition: service_healthy`.
- `postgres`: `postgres:18`, `POSTGRES_DB=cidb`, `POSTGRES_USER=cidb`,
  password from env, data on `/opt/cidb/data/postgres`, no host ports,
  `pg_isready` healthcheck.
- `caddy`: `caddy:2`, ports `80:80`, `443:443`, `443:443/udp`, `Caddyfile`
  mounted read-only, `/opt/cidb/data/caddy` for certificates, `ACME_EMAIL`
  from env.
- All services: `restart: unless-stopped`; logging driver `json-file` with
  `max-size: 10m`, `max-file: 5`.
- No Valkey.

### `Caddyfile`

```
{
  email {$ACME_EMAIL}
}
api.incidents.caves.org {
  reverse_proxy web:8000
}
```

Caddy sets `X-Forwarded-Proto`, which the app trusts (§10).

### `backup.sh`

Run by `cidb-backup.timer` daily at 03:00 UTC, `Persistent=true`.

1. Sentry Crons check-in: `in_progress`.
2. `docker compose exec -T postgres pg_dump -U cidb -Fc cidb | aws s3 cp -
   s3://nss-incidents-backups/postgres/cidb-<UTC timestamp>.dump`.
3. `aws s3api head-object` to confirm the object exists and is non-empty.
4. Sentry Crons check-in: `ok`, or `error` on any failure (the script exits
   non-zero; systemd records the failure).

Backups bucket lifecycle: current objects expire after 90 days; noncurrent
after 30. Versioning stays on.

### `restore.sh <s3-key|latest>`

1. Download the named dump, or the newest under `postgres/`.
2. Print the key, size and timestamp; require a typed `yes`.
3. `docker compose stop web`.
4. `pg_restore --clean --if-exists --no-owner -U cidb -d cidb`.
5. `docker compose up -d web`; wait for the healthcheck.

Used for the Hetzner migration, disaster recovery, and a quarterly restore
drill (restore into a scratch database, count rows, drop it).

### Operator access

`aws ssm start-session --target <instance-id>`. IAM-gated and audited; no
SSH, no keys. Two `justfile` recipes wrap it, reading the instance ID from
`CIDB_PROD_INSTANCE_ID` in `secrets.env`:

- `just prod-shell` — interactive session.
- `just prod-manage <args>` — `docker compose exec web python cidb/manage.py
  <args>`.

## 9. CI

**Rule:** GitHub holds no AWS secrets. OIDC replaces access keys, GHCR uses
`GITHUB_TOKEN`, and everything else lives as plain variables on a
`production` environment: `AWS_DEPLOY_ROLE_ARN`, `EC2_INSTANCE_ID`,
`CLOUDFRONT_DISTRIBUTION_ID`, `FRONTEND_BUCKET`, `VITE_SENTRY_DSN`,
`VITE_TAG_MANAGER_ID`. Both deploy jobs declare `environment: production`,
which is what the OIDC trust policy in §7 matches on. Required reviewers can
be enabled on the environment later; off by default.

### `deploy-backend.yaml` (replaces `container.yaml`)

Triggers: push to `main` ignoring `frontend/**`, `docs/**`, `*.md`;
`workflow_dispatch` with optional `sha` input. `concurrency: deploy-backend`,
no cancellation.

1. `backend-tests` and `lint` (reusable workflows; lint now includes mypy).
2. `build` on `ubuntu-24.04-arm`: `platforms: linux/arm64`, tags
   `sha-<short>` and `latest`, GHA layer cache.
3. `deploy` (`if: vars.EC2_INSTANCE_ID != ''`; `permissions: id-token:
   write`): assume the OIDC role; `aws ssm send-command --document-name
   AWS-RunShellScript --instance-ids $EC2_INSTANCE_ID --parameters
   commands="/opt/cidb/deploy.sh $SHA"`; poll `get-command-invocation` until
   terminal; print stdout/stderr; fail unless `Success`. 10-minute timeout.

### `deploy-frontend.yaml`

Triggers: push to `main` touching `frontend/**`; `workflow_dispatch`.

1. `frontend-tests` (existing reusable workflow).
2. `deploy` (`if: vars.FRONTEND_BUCKET != ''`): `pnpm build` with the two
   `VITE_*` variables; assume the OIDC role; then in this order so any failure
   leaves a working site:
   1. `s3 sync dist/assets/ s3://$BUCKET/assets/ --cache-control
      "public, max-age=31536000, immutable"` — no `--delete`.
   2. `s3 cp` each root file (`index.html`, favicons, manifest,
      `img/`) with `--cache-control "no-cache"`.
   3. `cloudfront create-invalidation --paths "/index.html" "/"`.
   4. `s3 sync dist/assets/ s3://$BUCKET/assets/ --delete` — cleanup only.

### Pull requests

Existing `backend-tests`, `frontend-tests`, `lint` (now with mypy), plus:

- `tofu fmt -check` and `tofu validate` when `tf/**` changes.
- `shellcheck deploy/*.sh` when `deploy/**` changes.

### Not in CI

`tofu apply` — run manually with the `cidb-nss` profile.

## 10. Application changes

| Change | File(s) |
|---|---|
| `CACHES` → `django.core.cache.backends.locmem.LocMemCache`; remove `django-valkey` from dependencies; remove `VALKEY_URL` | `cidb/conf/settings.py`, `pyproject.toml`, `uv.lock` |
| `AWS_S3_ACCESS_KEY_ID`, `AWS_S3_SECRET_ACCESS_KEY` default to `None`; add `AWS_QUERYSTRING_AUTH = False`, `AWS_DEFAULT_ACL = None` | `cidb/conf/settings.py` |
| `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`; `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` = `not DEBUG` | `cidb/conf/settings.py` |
| Visitor cookie `secure` flag uses `request.is_secure()` instead of the `SERVER_NAME` check | `cidb/src/core/middleware.py` |
| Gunicorn worker count from `WEB_CONCURRENCY` (default 4; production sets 3) | `cidb/conf/run.sh` |
| Add regression tests asserting unknown paths return 404 with `DEBUG=False` (no code fix needed — see §18) | `cidb/src/core/tests/test_http_errors.py` |
| Fix the 12 mypy errors (`api/schemas/feedback.py`, `conf/settings.py`) | as listed |
| Move the eleven brand assets into `frontend/cidb/public/` (`favicon.svg`, `favicon.ico`, `favicon-96x96.png`, `apple-touch-icon.png`, `site.webmanifest`, `img/*.png`); reference them root-relative | `frontend/cidb/index.html`, `src/constants.ts` |
| Delete `compose.prod.example.yml` (superseded by `deploy/compose.yml`); remove `valkey` from `docker-compose.yml` | repo root |
| `justfile`: `prod-shell`, `prod-manage` | `justfile` |
| README deployment section rewritten to point at this spec and `deploy/` | `README.md` |

## 11. Terraform changes

**Keep:** `providers.tf`, `acm.tf`, `vpc.tf`; the Route53 zone, delegation
set, `frontend_dns_records`, `api_dns_records`; the four existing buckets;
`policies.tf`'s `s3_read`/`s3_write` documents and policies; the
distribution resource; `strip_cdn_prefix`; `api_cache`; `api_origin`.

**Change:**

- `ec2.tf`: instance type, AMI data source, root volume 20 GB, `user_data`,
  `user_data_replace_on_change`, security group without port 22,
  `iam_role_policies`; add the data volume and attachment; add the DLM policy.
- `cloudfront.tf`: as §5.
- `iam.tf`: OIDC provider and deploy role replace the user and key.
- `s3.tf`: add the frontend bucket; OAC bucket policies for frontend and cdn;
  backups bucket lifecycle (90-day current expiry, 30-day noncurrent).
- `variables.tf`: remove `origin_domain_name`; add `instance_type`
  (default `t4g.small`).
- New `parameters.tf`: the Parameter Store entries.
- New `outputs.tf`: `instance_id`, `deploy_role_arn`,
  `cloudfront_distribution_id`, `frontend_bucket`.

**Delete:** `secrets.tf`; the `HTTP-NSSIncidentDB` origin; `strip_admin_prefix`;
`default_with_query_strings`; the OAI; `origin_dns_records`;
`aws_iam_user.app`; `aws_iam_access_key.app`.

## 12. First deploy

1. **Repo.** Merge one branch containing §10, `deploy/`, and §9's workflows.
   The deploy jobs are guarded on environment variables, so merging is safe
   before infrastructure exists.
2. **Terraform.** `terraform init` against the existing state; read the plan
   carefully. Expected: instance replaced; data volume, frontend bucket, OAC,
   OIDC provider, deploy role, parameters, DLM policy created; IAM user, access
   key, secrets, OAI, one origin, one function, one cache policy destroyed;
   distribution updated in place. Apply.
3. **Parameters.** `aws ssm put-parameter` for each key in §7; the Hetzner
   box's `prod.env` is the source for most values.
4. **First boot fails at the placeholder guard — this is expected.** cloud-init
   runs `deploy.sh main`, which refuses to start because every parameter still
   holds Terraform's literal `placeholder` value. Serving traffic with a
   publicly known `SECRET_KEY` would mean forgeable sessions, so the deploy
   dies loudly instead. Set the real values (step 3), then re-run the deploy —
   either the GitHub workflow or `/opt/cidb/deploy.sh main` over SSM.
   Steps 3 and 4 are therefore in this order only on paper; in practice the
   apply, the failed first boot, the parameter values and the re-run all
   happen in one sitting.
5. **GitHub.** Create the `production` environment; set the six variables from
   Terraform outputs; run both workflows once via `workflow_dispatch`.
6. **Verify** (§13).
7. **Data** (manual, out of scope): `pg_dump -Fc` on Hetzner → upload under
   `postgres/` in the backups bucket → `restore.sh <key>`; `aws s3 sync` the
   media prefix into `nss-incidents-cdn`.

## 13. Verification checklist

Each item proves the layer the next one depends on:

1. `curl` `/core/healthcheck/` inside the `web` container → `OK`.
2. `https://api.incidents.caves.org/core/healthcheck/` → 200 (Caddy + cert).
3. `https://incidents.caves.org/api/v1/incidents/search` → 200 JSON
   (CloudFront → origin).
4. `https://incidents.caves.org/` → SPA; `/incidents/1` → SPA, not 403
   (`spa_rewrite`).
5. `https://incidents.caves.org/admin/login/` renders **with styling**
   (`/admin/*` and `/static/*` behaviours).
6. Staff login from the SPA succeeds (cookies + `X-CSRFToken` + `Referer`
   through CloudFront; `SECURE_PROXY_SSL_HEADER`).
7. A feedback submission succeeds and appears under `/staff/feedback`.
8. `https://incidents.caves.org/api/v1/nope` → **404** JSON.
9. `systemctl list-timers` shows `cidb-backup.timer`; `systemctl start
   cidb-backup.service` produces an object in the bucket and a Sentry cron
   check-in.
10. `just prod-manage showmigrations` works from a laptop.

## 14. Runbook

| Task | How |
|---|---|
| Deploy | merge to `main` |
| Roll back | Actions → Deploy backend → Run workflow → `sha` |
| Shell on the box | `just prod-shell` |
| Run a data operation | `just prod-manage run_data_operations …` |
| Logs | `docker compose logs -f web` from the shell; Logfire for history |
| Backup now | `sudo systemctl start cidb-backup.service` |
| Restore | `sudo /opt/cidb/restore.sh latest`. If `pg_restore` fails, `web` is deliberately left stopped rather than serving a half-restored database — fix the cause and re-run, or `docker compose up -d web` to accept the current state |
| Restore drill (quarterly) | restore into a scratch database, count rows, drop it |
| Rebuild the server | **Stop the stack first** over SSM (`cd /opt/cidb && docker compose --env-file prod.env -f compose.yml down`), then `tofu apply -replace=module.nss_incidents_ec2.aws_instance.this[0]`; data volume reattaches; ~10 min. Stopping first avoids a dirty force-detach of a mounted filesystem with Postgres mid-write — `aws_volume_attachment` is destroyed before the instance terminates, and `stop_instance_before_detaching` cannot be set because `disable_api_stop = true`. |
| Rotate a secret | `aws ssm put-parameter --overwrite`, then re-run the deploy workflow |
| Resize | change `instance_type`, apply; the data volume survives |
| Disk full | log rotation and image pruning prevent it; `docker system df` if not |

## 15. Failure modes

| Failure | Behaviour |
|---|---|
| Tests or build fail in CI | Nothing deployed |
| `migrate` fails | Running site untouched; CI red with the transcript |
| New image fails healthcheck | `deploy.sh` restores the previous image; CI red |
| SSM command times out | CI red; box state is whatever `deploy.sh` left, which is always a running image |
| Frontend deploy fails mid-way | Old `index.html` still references old assets, which are not yet deleted |
| Backup fails or is missed | Sentry Crons alerts by email |
| Instance dies | SPA still served from S3/CloudFront; `tofu apply` builds a new instance on the same data volume |
| Data volume not attached at boot | cloud-init waits ~120s for the device, then **fails the boot loudly** rather than letting Postgres write to the `delete_on_termination` root volume. `deploy.sh` re-asserts the mountpoint before starting Postgres, and a `docker.service` drop-in carries `RequiresMountsFor=/opt/cidb/data` so a reboot without the volume cannot start the stack either. Recover by mounting the volume and re-running `deploy.sh main`. Note this race recurs on **every** instance replacement, not just first boot, because `user_data_replace_on_change = true` means any cloud-init edit replaces the instance |
| Data volume lost | Restore from the newest S3 dump (≤ 24 h old) or DLM snapshot (≤ 7 days) |
| Certificate issuance fails | Caddy retries; `api.*` returns TLS errors, CloudFront 502s; uptime check alerts |

**Uptime check:** one monitor on
`https://incidents.caves.org/api/v1/incidents/search`, using Sentry's uptime
monitoring (free tier) or a Route53 health check (~$1/month), emailing the
maintainer.

## 16. Cost

Approximate us-west-2 on-demand, per month.

| Item | Recommended | Existing `tf/` |
|---|---|---|
| EC2 | `t4g.small` ~12.3 (savings plan ~8) | `m8g.large` ~65 |
| EBS | 20 + 10 GB gp3 ~2.4 | 200 GB gp3 ~16 |
| Public IPv4 | ~3.7 | ~3.7 |
| Route53 | ~1 | ~1 |
| S3 | ~1 | ~1 |
| CloudFront | ~0 (within always-free tier) | ~0 |
| Secrets Manager | 0 | ~1.6 |
| Snapshots | ~0.5 | 0 |
| **Total** | **~21** (~16 reserved; ~33 on `t4g.medium`) | **~89** |
| Optional RDS `db.t4g.micro` | +~14 | — |

## 17. Success criteria

- A push to `main` updates `incidents.caves.org` — backend and frontend — with
  no manual step.
- Admin, staff login, report submission and feedback resolution all work
  through CloudFront.
- Unrouted paths return 404.
- A dump lands in `nss-incidents-backups` every night and its absence would be
  noticed.
- Every routine operation in §14 is a single command.
- The monthly bill is within a few dollars of §16.

## 18. Corrections to earlier findings

- **The 404-renders-as-500 bug is not in `main`.** Verified against a real
  database on 2026-09-27: `/nonexistent-xyz`, `/core/nope` and `/api/v1/nope`
  all return 404, and `/api/v1/incidents/<non-integer>` returns 422, which is
  correct django-ninja path-parameter validation. The 500s observed on
  `api.cidb.dev` come from the December 2025 build deployed there; the defect
  was fixed somewhere in the v2 work. §10 therefore asks only for regression
  tests, not a fix.
- **The GHCR package is publicly pullable.** Confirmed by an anonymous token
  pull listing tags `latest` and `sha-c534099`, so the server needs no
  registry credentials, as §8 assumes.

- `frontend/cidb/pnpm-workspace.yaml` does **not** contain a broken
  placeholder in the repo. The `allowBuilds:` lines observed locally were
  written by pnpm 11 during a local install and have been reverted. The real
  issue is a local/CI pnpm major-version mismatch (11 vs 10.30.3); adding a
  `packageManager` field to `package.json` resolves it and is a small
  follow-up outside this design.
