from algoliasearch_django import AlgoliaIndex
from algoliasearch_django.decorators import register

from .models import Incident


@register(Incident)
class IncidentIndex(AlgoliaIndex):
    fields = (
        "date",
        "cave",
        "get_state_display",
        "county",
        "get_country_display",
        "incident_report",
        "incident_analysis",
        "incident_summary",
    )

    settings = {
        "searchableAttributes": [
            "cave",
            "get_state_display",
            "county",
            "get_country_display",
            "incident_report",
            "incident_analysis",
        ],
    }
