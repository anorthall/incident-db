from typing import Any

from django.conf import settings
from django.http import HttpRequest


def google_tag_manager(_: HttpRequest) -> dict[str, Any]:
    """Add the Google Tag Manager ID to the context."""
    return {"GOOGLE_GTM_TAG": settings.GOOGLE_GTM_TAG}


def algolia_search_key(_: HttpRequest) -> dict[str, Any]:
    """Add the Algolia search key to the context."""
    return {
        "ALGOLIA_APPLICATION_ID": settings.ALGOLIA_APPLICATION_ID,
        "ALGOLIA_SEARCH_KEY": settings.ALGOLIA_SEARCH_KEY,
        "ALGOLIA_ENABLED": settings.ALGOLIA_ENABLED,
    }
