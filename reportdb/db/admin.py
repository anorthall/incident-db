from dataclasses import dataclass

from django.contrib import admin
from import_export import resources
from import_export.admin import ExportActionMixin
from reversion.admin import VersionAdmin

from .models import Incident, InjuredCaver, Publication

# Set admin site header
admin.site.site_header = "ACA DB"
admin.site.site_title = "ACA DB"


@admin.register(Publication)
class PublicationAdmin(VersionAdmin):
    list_display = ("name", "created", "updated")
    search_fields = ("name",)
    ordering = ("-created",)


@admin.register(InjuredCaver)
class InjuredCaverAdmin(VersionAdmin):
    list_display = ("first_name", "surname", "incident")
    search_fields = ("first_name", "surname", "injuries")
    list_display_links = ("first_name", "surname")
    autocomplete_fields = ("incident",)
    ordering = ("incident",)


class InjuredCaverInline(admin.TabularInline):
    model = InjuredCaver
    view_on_site = False
    extra = 1


@dataclass
class InjuredCaver:
    name: str
    age: str
    sex: str
    injuries: str
    injury_areas: str

    def __str__(self):
        result_str = f"Name: {self.name}"
        result_str += f"\nAge: {self.age}" if self.age else ""
        result_str += f"\nSex: {self.sex}" if self.sex else ""
        result_str += f"\nInjuries: {self.injuries}" if self.injuries else ""
        result_str += (
            f"\nInjury areas: {self.injury_areas}" if self.injury_areas else ""
        )
        return result_str


class IncidentResource(resources.ModelResource):
    injured_cavers = resources.Field()
    human_incident_type = resources.Field(column_name="incident_type")
    human_incident_cause = resources.Field(column_name="incident_cause")
    published_in = resources.Field(column_name="publication")

    class Meta:
        model = Incident
        exclude = (
            "created",
            "updated",
            "editing_notes",
            "approximate_date",
            "keywords",
            "updated_by",
            "incident_type",
            "incident_type_2",
            "incident_type_3",
            "primary_cause",
            "secondary_cause",
            "publication_page",
            "publication",
        )

        export_order = (
            "id",
            "date",
            "published_in",
            "cave",
            "state",
            "county",
            "country",
            "category",
            "human_incident_type",
            "human_incident_cause",
            "group_type",
            "group_size",
            "aid_type",
            "incident_report",
            "incident_analysis",
            "incident_summary",
            "injured_cavers",
            "source",
            "incident_notes",
            "incident_references",
            "aid_type",
            "fatality",
            "injury",
            "multiple_incidents",
            "rescue_over_24_hours",
            "vertical",
            "spar",
            "approved",
        )

    def dehydrate_published_in(self, incident):
        result = incident.publication.name
        if incident.publication_page:
            result += f" p. {incident.publication_page}"
        return result

    def dehydrate_human_incident_type(self, incident):
        type1 = incident.get_incident_type_display()
        type2 = incident.get_incident_type_2_display()
        type3 = incident.get_incident_type_3_display()

        incident_type = type1
        if type2 != "None":
            incident_type += f", {type2.lower()}"
        if type3 != "None":
            incident_type += f", {type3.lower()}"

        return incident_type

    def dehydrate_human_incident_cause(self, incident):
        cause1 = incident.primary_cause
        cause2 = incident.secondary_cause

        cause = cause1
        if cause2 and cause2 != "None" and cause2 != "Unknown":
            cause += f", {cause2.lower()}"

        return cause

    def dehydrate_publication(self, incident):
        return incident.publication.name

    def dehydrate_aid_type(self, incident):
        if incident.aid_type != "None":
            return incident.aid_type
        else:
            return "Unknown"

    def dehydrate_date(self, incident):
        date_format = "%B %-d, %Y"
        date = incident.date
        if incident.approximate_date:
            if date.month == 1 and date.day == 1:
                return f"{date.year}"
            elif date.day == 1:
                return f"{date.strftime('%B')} {date.year}"
            else:
                return f"{date.strftime(date_format)}"
        else:
            return date.strftime(date_format)

    def dehydrate_injured_cavers(self, incident):
        injured_cavers = []

        for caver in incident.injured_cavers.all():
            name = "Unknown"
            if caver.first_name or caver.surname:
                name = f"{caver.first_name} {caver.surname}".strip()

            injured_cavers.append(
                InjuredCaver(
                    name=name,
                    age=caver.age,
                    sex=caver.sex,
                    injuries=caver.injuries,
                    injury_areas=caver.injury_areas,
                )
            )

        return "\n\n".join([str(caver) for caver in injured_cavers])


@admin.register(Incident)
class IncidentAdmin(ExportActionMixin, VersionAdmin):
    inlines = (InjuredCaverInline,)
    resource_classes = [IncidentResource]
    list_display = (
        "date",
        "publication",
        "cave",
        "state",
        "country",
        "category",
        "incident_type",
    )
    ordering = ("-date",)
    list_filter = (
        "approved",
        "publication",
        "state",
        "country",
        "date",
        "incident_type",
        "category",
        "fatality",
        "injury",
    )
    search_fields = (
        "cave",
        "state",
        "county",
        "country",
        "incident_type",
        "primary_cause",
        "secondary_cause",
        "editing_notes",
        "incident_report",
        "incident_analysis",
    )
    autocomplete_fields = ("publication",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "publication",
                    "publication_page",
                    "date",
                    "approximate_date",
                )
            },
        ),
        (
            "Location",
            {
                "fields": (
                    "cave",
                    "state",
                    "county",
                    "country",
                )
            },
        ),
        (
            "Incident",
            {
                "fields": (
                    "category",
                    "incident_type",
                    "incident_type_2",
                    "incident_type_3",
                    "primary_cause",
                    "secondary_cause",
                    "aid_type",
                    "group_type",
                    "group_size",
                )
            },
        ),
        (
            "Data collection flags",
            {
                "fields": (
                    "fatality",
                    "injury",
                    "multiple_incidents",
                    "rescue_over_24_hours",
                    "vertical",
                    "spar",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "incident_report",
                    "incident_analysis",
                    "incident_summary",
                    "incident_notes",
                    "incident_references",
                    "original_text",
                )
            },
        ),
        (
            "Editing",
            {
                "fields": (
                    "data_input_source",
                    "editing_notes",
                    "approved",
                    "created",
                    "updated",
                )
            },
        ),
    )
    readonly_fields = (
        "approved",
        "created",
        "updated",
        "original_text",
        "data_input_source",
    )
