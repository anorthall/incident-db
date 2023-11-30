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
The `data/` directory contains the archive of ACA Journals in a number of formats with varied levels of
processing.

The original PDFs of the journals are contained in `data/pdf/`. These PDF files were run
through Amazon AWS Textract, and processed with a simple script, to generate the text files within
`data/processed/txt`. These text files were then further processed by hand to generate the ones contained
within the `data/processed/txt-split/` directory, where non-incident report text has been removed and each
incident report separated by three dashes (`---`) within the text file to allow easier machine separation
of incidents.

The files from `data/processed/txt-split/` were then processed using the OpenAI API by means of the script
contained within the `data/openai-formatter/` directory. This script produces JSON arrays of each incident,
with relevant metadata (such as the cave name, date, incident report, cavers involved) separated. The results
from this are contained in the `data/json/` directory.

These JSON files are the final stage of processing before the data is added to the Django web application,
which is then used by volunteers to check the work of the AI formatter before making the incident available
for all to view online.

# Contributing
Contributions are welcome - both in terms of code, and volunteering to help edit incidents on
the production Django app. For more information, please join
[our Discord server](https://discord.gg/bUCYsmghVs).

# Licence
This project is licensed under the GNU GPL v3.0. For more information see the LICENCE file.
