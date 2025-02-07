import datetime
import json
import re
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from db.models import Incident, InjuredCaver, Publication


class Command(BaseCommand):
    help: str = "Import a CSV file of incident data"

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.publication: Publication | None = None

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("json_file", type=str)
        parser.add_argument("publication", type=str)

    def handle(
        self,
        *args: Any,
        **options: Any,
    ) -> None:
        file_name = options["json_file"]
        if not Path(file_name).exists():
            raise CommandError(f"File {file_name} does not exist")

        publication = options["publication"]
        try:
            self.publication = Publication.objects.get(name=publication)
        except Publication.DoesNotExist as err:
            raise CommandError(f"Publication {publication} does not exist.") from err

        incidents = self.process_json_file(file_name)

        num_incidents = len(incidents)
        self.stdout.write(self.style.SUCCESS(f"Successfully imported {num_incidents} incidents."))

    def process_json_file(self, file_name: str) -> list[Incident]:
        """Process a JSON file of incident data."""
        incidents: list[Incident] = []
        with open(file_name) as json_file:
            data: list[dict[str, Any]] = json.load(json_file)

        for incident in data:
            incidents.append(self.process_incident(incident))

        return incidents

    def process_incident(self, incident: dict[str, Any]) -> Incident:
        """Process an incident and return the Incident object."""
        page = incident["page"]
        assert page > 0, f"Invalid page: {page}"
        date, approx = self.parse_date(incident["date"])
        category = self.parse_category(incident["category"])
        incident_type = self.parse_incident_type(incident["suggested_incident_type"], primary=True)
        incident_type_2 = self.parse_incident_type(incident["suggested_incident_type_secondary"])
        incident_type_3 = self.parse_incident_type(incident["suggested_incident_type_tertiary"])
        group_size = incident.get("group_size") if incident.get("group_size", 0) else None
        cavers = incident.get("cavers", [])

        incident_model = Incident.objects.create(
            publication=self.publication,
            publication_page=page,
            date=date,
            approximate_date=approx,
            cave=incident["cave"],
            state=incident.get("state", ""),
            country=incident.get("country", ""),
            county=incident.get("county", ""),
            category=category,
            fatality=incident["fatality"],
            injury=incident["injury"] if not incident["fatality"] else True,
            vertical=incident["vertical"],
            rescue_over_24_hours=incident["rescue_over_24"],
            group_size=group_size,
            incident_type=incident_type,
            incident_type_2=incident_type_2,
            incident_type_3=incident_type_3,
            incident_report=incident["incident_report"],
            incident_analysis=incident["incident_analysis"],
            incident_summary=incident.get("suggested_summary", ""),
            incident_references="\n".join(incident.get("incident_references", [])),
            original_text=incident.get("original_text", ""),
            data_input_source=Incident.DataInput.AI,
        )

        self.parse_cavers(incident_model, cavers)

        return incident_model

    def parse_cavers(self, incident: Incident, cavers: list[str]) -> None:
        for caver in cavers:
            first_name, surname = caver.split(" ", 1)
            age = None

            # Match "Surname (24)" to extract age
            age_match = re.search(r"^(.*)\S?\((\d{1,2})\)$", surname)
            if age_match:
                surname = age_match.group(1)
                age = int(age_match.group(2))
                assert age > 0, f"Invalid age: {age}"
                assert age < 100, f"Invalid age: {age}"

            InjuredCaver.objects.create(
                incident=incident,
                first_name=first_name,
                surname=surname,
                age=age,
            )

    def parse_date(self, date_str: str) -> tuple[datetime.date, bool]:
        """Parse the date and return a tuple of the date and approximate boolean."""
        if not date_str:
            raise ValueError("Date cannot be empty")

        # Date should be in format YYYY-MM-DD (or YYYY-MM or YYYY)
        date_split = date_str.strip().split("-")

        month, day = "01", "01"
        approximate = False

        if len(date_split) == 1:
            year = date_split[0]
            approximate = True
        elif len(date_split) == 2:
            year, month = date_split[0], date_split[1]
            approximate = True
        elif len(date_split) == 3:
            year, month, day = date_split[0], date_split[1], date_split[2]
        else:
            raise ValueError(f"Invalid date format: {date_str}")

        assert len(year) == 4, f"Invalid year: {year}"
        assert int(year) > 1850, f"Invalid year: {year}"
        assert int(year) < datetime.date.today().year, f"Invalid year: {year}"
        assert len(month) == 2, f"Invalid month: {month}"
        assert int(month) > 0, f"Invalid month: {month}"
        assert int(month) < 13, f"Invalid month: {month}"
        assert len(day) == 2, f"Invalid day: {day}"
        assert int(day) > 0, f"Invalid day: {day}"
        assert int(day) < 32, f"Invalid day: {day}"

        return datetime.date(int(year), int(month), int(day)), approximate

    def parse_category(self, category: str) -> str:
        for key, value in Incident.Category.choices:
            if category == value:
                return key
        else:
            return ""

    def parse_incident_type(self, incident_type: str, primary: bool = False) -> str:
        if primary:
            for key, value in Incident.PrimaryType.choices:
                if incident_type == value:
                    return key
            else:
                return Incident.PrimaryType.UNKNOWN

        for key, value in Incident.SecondaryType.choices:
            if incident_type == value:
                return key
        else:
            return Incident.SecondaryType.NONE
