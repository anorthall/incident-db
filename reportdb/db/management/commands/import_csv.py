import csv
import datetime
import os

from db.models import Incident, InjuredCaver, Publication
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Import a CSV file of incident data"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.publication = None

    def add_arguments(self, parser):
        parser.add_argument("csv_file", nargs=1, type=str)
        parser.add_argument("publication", nargs=1, type=str)

    def handle(self, *args, **options):
        file = options["csv_file"][0]
        if not os.path.isfile(file):
            raise CommandError(f"File {file} does not exist")

        publication = options["publication"][0]
        try:
            self.publication = Publication.objects.get(name=publication)
        except Publication.DoesNotExist:
            raise CommandError(f"Publication {publication} does not exist.")

        with open(file, encoding="utf-8-sig") as csv_file:
            incidents = self.process_csv_file(csv_file)

        num_incidents = len(incidents)
        self.stdout.write(
            self.style.SUCCESS(f"Successfully imported {num_incidents} rows.")
        )

    def process_csv_file(self, csv_file):
        """Process a CSV file of incident data"""
        incidents = []
        reader = csv.DictReader(csv_file)
        for row in reader:
            incidents.append(self.process_row(row))
        return incidents

    def parse_date(self, row):
        year, month, day = row["Year"], row["Month"], row["Day"]
        if year and month and day:
            date = datetime.date(int(year), int(month), int(day))
        else:
            raise CommandError(f"Row {row} does not have a valid date.")

        if row["Approximate date"].strip().lower() == "true":
            approximate_date = True
        else:
            approximate_date = False

        return date, approximate_date

    def parse_country(self, row):
        country = row["Country"].strip().title()
        if country == "Usa" or country == "United States" or country == "Us":
            country = "USA"
        return country

    def parse_category(self, row):
        category = row["Category"].strip().lower()
        if category == "caving":
            category = Incident.CAVING
        elif category == "cave diving":
            category = Incident.DIVING
        elif category == "diving":
            category = Incident.DIVING
        elif category == "caving related":
            category = Incident.CAVING_RELATED
        elif category == "other":
            category = Incident.OTHER
        else:
            raise CommandError(f"Row {row} does not have a valid category.")
        return category

    def parse_injury(self, row):
        injury = row["Injury"].strip().lower()
        if injury == "yes":
            injury = True
            fatality = False
        elif injury == "no":
            injury = False
            fatality = False
        elif injury == "fatality":
            injury = True
            fatality = True
        else:
            injury = False
            fatality = False
        return injury, fatality

    def parse_int(self, row, int_name):
        value = row[int_name].strip()
        if value:
            result = int(value)
        else:
            result = None
        return result

    def parse_caver_sex(self, row):
        caver_sex = row["Caver sex"].strip().lower()
        if caver_sex == "m" or caver_sex == "male":
            caver_sex = "Male"
        elif caver_sex == "f" or caver_sex == "female":
            caver_sex = "Female"
        else:
            caver_sex = ""
        return caver_sex

    def parse_group_type(self, row):
        group_type = row["Group type"].strip().lower()
        if group_type == "cavers":
            group_type = Incident.CAVERS
        elif group_type == "novices":
            group_type = Incident.NOVICES
        elif group_type == "industry":
            group_type = Incident.INDUSTRY
        elif group_type == "club":
            group_type = Incident.CLUB
        elif group_type == "divers":
            group_type = Incident.DIVERS
        elif group_type == "military":
            group_type = Incident.MILITARY
        elif group_type == "college":
            group_type = Incident.COLLEGE
        else:
            group_type = Incident.OTHER
        return group_type

    def parse_aid(self, row):
        aid = row["Aid"].strip().lower()
        if aid == "outside":
            aid = Incident.AID_SURFACE
        elif aid == "inside":
            aid = Incident.AID_UNDERGROUND
        elif aid == "recovery":
            aid = Incident.AID_RECOVERY
        elif aid == "standby":
            aid = Incident.AID_STANDBY
        else:
            aid = Incident.UNKNOWN
        return aid

    def parse_yes_or_no(self, row, yes_or_no_name):
        value = row[yes_or_no_name].strip().lower()
        if value == "yes":
            result = True
        else:
            result = False
        return result

    def process_row(self, row):
        """Process a row of incident data"""
        date, approximate_date = self.parse_date(row)
        cave = row["Cave"].strip()
        state = row["State"].strip().title()
        county = row["County"].strip().title()
        country = self.parse_country(row)
        category = self.parse_category(row)
        injury, fatality = self.parse_injury(row)
        incident_type = row["Type"].strip().capitalize()
        primary_cause = row["Primary cause"].strip().capitalize()
        secondary_cause = row["Secondary cause"].strip().capitalize()
        caver_surname = row["Caver surname"].strip().title()
        caver_first_name = row["Caver firstname"].strip().title()
        caver_age = self.parse_int(row, "Caver age")
        caver_sex = self.parse_caver_sex(row)
        group_type = self.parse_group_type(row)
        aid = self.parse_aid(row)
        multiple_incidents = self.parse_yes_or_no(row, "Multiple incidents")
        rescue_over_24h = self.parse_yes_or_no(row, "Rescue over 24h")
        injuries = row["Injuries"].strip().capitalize()
        injury_areas = row["Injury areas"].strip().capitalize()
        publication_page = self.parse_int(row, "Page")
        spar = self.parse_yes_or_no(row, "SPAR")
        vertical = self.parse_yes_or_no(row, "Vertical")
        incident_notes = row["Notes"].strip()

        # Attempt to find duplicate incident
        try:
            incident = Incident.objects.get(
                date=date,
                approximate_date=approximate_date,
                publication=self.publication,
                publication_page=publication_page,
                cave=cave,
                state=state,
                county=county,
                country=country,
            )
            self.stdout.write(f"Duplicate incident found: {row['Cave']}")
        except Incident.DoesNotExist:
            incident = Incident.objects.create(
                date=date,
                approximate_date=approximate_date,
                publication=self.publication,
                publication_page=publication_page,
                cave=cave,
                state=state,
                county=county,
                country=country,
                category=category,
                incident_type=incident_type,
                primary_cause=primary_cause,
                secondary_cause=secondary_cause,
                group_type=group_type,
                aid_type=aid,
                fatality=fatality,
                injury=injury,
                multiple_incidents=multiple_incidents,
                vertical=vertical,
                rescue_over_24_hours=rescue_over_24h,
                spar=spar,
                incident_notes=incident_notes,
            )

        if caver_surname:
            InjuredCaver.objects.create(
                first_name=caver_first_name,
                surname=caver_surname,
                age=caver_age,
                sex=caver_sex,
                injuries=injuries,
                injury_areas=injury_areas,
                incident=incident,
            )

        incident.save()
        self.stdout.write(self.style.SUCCESS(f"Successfully imported {incident}."))
        return incident
