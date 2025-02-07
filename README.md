# Caving Incident Report DB

This is a project which aims to digitise the archive of
[National Speleological Society](https://caves.org/) *American Caving Accidents*
caving incident reports, which cover most caving incidents that have happened in the
United States of America and nearby countries since humans first entered caves for sport.

This repository consists of both a Django application to display and edit the digitised
incident reports, as well as code and data related to digitising them to enable them to be
uploaded to the Django application.

The Django application is running at [aca.caver.dev](https://aca.caver.dev/), should you wish
to take a look. You may also wish to view the [about page](https://aca.caver.dev/about/) on
the website for more information about the project.

## Django application

This fairly straightforward application lives within the `reportdb/` and `etc/` folders, and is
run using docker-compose (or Dokku in production). The applications allows a basic CRUD interface for
incident reports, and has management commands (`import_json` and `import_csv`) to enable the mass
import of incident reports from the processing scripts in `data/`.

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
