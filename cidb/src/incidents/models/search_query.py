from __future__ import annotations

from datetime import UTC, datetime

from django.db import IntegrityError, models
from django.db.models import F
from django.utils import timezone
from django_stubs_ext.db.models import TypedModelMeta


class SearchQuery(models.Model):
    query = models.CharField(
        unique=True,
        max_length=500,
        help_text="Normalized (lowercase, stripped) search query",
    )
    query_count = models.PositiveBigIntegerField(
        default=1,
        help_text="Number of times this query has been searched",
    )
    last_queried_at = models.DateTimeField(
        default=timezone.now,
        help_text="When this query was last searched",
    )

    class Meta(TypedModelMeta):
        verbose_name = "search query"
        verbose_name_plural = "search queries"

    def __str__(self) -> str:
        return f"{self.query} ({self.query_count})"

    @classmethod
    def record_search(cls, query: str) -> None:
        if cls._update_search_count(query) == 0:
            try:
                cls.objects.create(query=cls._normalise_query(query))
            except IntegrityError:
                cls._update_search_count(query)

    @classmethod
    def _update_search_count(cls, query: str) -> int:
        if not (normalized := cls._normalise_query(query)):
            return 0

        return cls.objects.filter(query=normalized).update(
            query_count=F("query_count") + 1,
            last_queried_at=datetime.now(UTC),
        )

    @classmethod
    def _normalise_query(cls, query: str) -> str:
        return query.lower().strip()
