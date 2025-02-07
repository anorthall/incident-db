from dataclasses import dataclass

from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import Incident, InjuredCaver, Publication

admin.site.site_header = "Incident DB"
admin.site.site_title = "Incident DB"


@admin.register(Publication)
class PublicationAdmin(ModelAdmin[Publication]):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)
    ordering = ("-created_at",)


@admin.register(InjuredCaver)
class InjuredCaverAdmin(ModelAdmin[InjuredCaver]):
    list_display = ("first_name", "surname", "incident")
    search_fields = ("first_name", "surname", "injuries")
    list_display_links = ("first_name", "surname")
    autocomplete_fields = ("incident",)
    ordering = ("incident",)


class InjuredCaverInline(admin.TabularInline[InjuredCaver, InjuredCaver]):
    model = InjuredCaver
    view_on_site = False
    extra = 1


@dataclass
class InjuredCaverDTO:
    name: str
    age: str
    sex: str
    injuries: str
    injury_areas: str

    def __str__(self) -> str:
        result_str = f"Name: {self.name}"
        result_str += f"\nAge: {self.age}" if self.age else ""
        result_str += f"\nSex: {self.sex}" if self.sex else ""
        result_str += f"\nInjuries: {self.injuries}" if self.injuries else ""
        result_str += f"\nInjury areas: {self.injury_areas}" if self.injury_areas else ""
        return result_str


@admin.register(Incident)
class IncidentAdmin(ModelAdmin[Incident]):
    inlines = (InjuredCaverInline,)
    list_display = (
        "date",
        "publication",
        "cave",
        "country",
        "category",
        "incident_type",
        "updated_at",
    )
    ordering = ("-updated_at",)
    list_filter = (
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
                    "us_state",
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
                    "self_rescue",
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
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "original_text",
        "data_input_source",
    )
