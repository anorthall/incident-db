from __future__ import annotations

from django.db import models
from django_stubs_ext.db.models import TypedModelMeta


class SearchClick(models.Model):
    query = models.CharField(
        max_length=500,
        help_text="The search query that led to this click",
    )
    incident = models.ForeignKey(
        "Incident",
        on_delete=models.CASCADE,
        related_name="search_clicks",
    )
    position = models.PositiveSmallIntegerField(
        help_text="Position in search results (1-indexed)",
    )
    clicked_at = models.DateTimeField(auto_now_add=True)

    class Meta(TypedModelMeta):
        verbose_name = "search click"
        verbose_name_plural = "search clicks"
        indexes = [
            models.Index(fields=["query"], name="incidents_searchclick_query"),
            models.Index(fields=["clicked_at"], name="incidents_searchclick_time"),
        ]

    def __str__(self) -> str:
        return f"{self.query} → {self.incident.id} (pos {self.position})"

    @classmethod
    def record_click(cls, query: str, incident_id: int, position: int) -> None:
        SearchClick.objects.create(
            query=query.lower().strip(),
            incident_id=incident_id,
            position=position,
        )
