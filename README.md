# Caving Incident Report DB

This is a project which aims to digitise the archive of
[National Speleological Society](https://caves.org/) *American Caving Accidents*
caving incident reports, which cover most caving incidents that have happened in the
United States of America and nearby countries since humans first entered caves for sport.

This repository consists of both a Django application to display and edit the digitised
incident reports, as well as code and data related to digitising them to enable them to be
uploaded to the Django application.

The Django application is running at [cidb.dev](https://cidb.dev/), should you wish
to take a look.

## Django application

This fairly straightforward application lives within `cidb/`, and is run locally using
docker-compose. The application allows a basic CRUD interface for
incident reports, and has management commands (`import_json` and `import_csv`) to enable the mass
import of incident reports from the processing scripts in `data/`.

## Deployment

Production runs on AWS at [incidents.caves.org](https://incidents.caves.org/): the React frontend
is served from S3 behind CloudFront, and the Django API runs in Docker on a single EC2 instance
behind Caddy. Merging to `main` deploys automatically — the backend and frontend have separate
workflows, so a UI change does not redeploy the API.

- **Design and rationale:** `docs/superpowers/specs/2026-09-27-aws-deployment-design.md`
- **Infrastructure:** `tf/` (OpenTofu; applied manually, not from CI)
- **Server configuration:** `deploy/` — the compose stack, Caddyfile, and the deploy, backup and
  restore scripts. Everything the server runs is in this directory, so rebuilding it is
  `tofu apply` followed by one deploy.

Routine operations:

| Task | How |
| --- | --- |
| Deploy | Merge to `main` |
| Roll back | Actions → Deploy Backend → Run workflow → enter a SHA |
| Shell on the server | `just prod-shell` |
| Run a management command | `just prod-manage <args>` |
| Back up now | `sudo systemctl start cidb-backup.service` |
| Restore | `sudo /opt/cidb/restore.sh latest` |
| Rebuild the server | Stop the stack over SSM first, then `tofu apply -replace=...` — see the spec's runbook |

Server access is via AWS Session Manager, so there is no SSH key and no open port 22. Both
`just prod-shell` and `just prod-manage` read `CIDB_PROD_INSTANCE_ID` from `secrets.env`.

The Django application allows web based editing and approval of incidents, easily enabling humans to check
the work of the AI formatter before marking an incident report as 'approved' and ready for consumption
by the public.

## Data and processing

The original data, including full ACA report PDF files, and the same in all sorts of different manually
and machine processed forms, are available in a public S3 bucket called `caving-incident-reports` in the
`eu-west-2` region. You can download the data from the bucket using the AWS CLI, or by any number of
graphical S3 clients. If you require any assistance in accessing the data, please join our
[Discord server](https://discord.gg/bUCYsmghVs) and ask for help.

# Contributing

Contributions are welcome - both in terms of code, and volunteering to help edit incidents on
the production Django app. For more information, please join
[our Discord server](https://discord.gg/bUCYsmghVs).

# Licence

This project is licensed under the GNU GPL v3.0. For more information see the LICENCE file.
