from __future__ import annotations

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import F, Func, Value

from cidb.src.core.models.generic import TimestampModel, UUIDPKModel


class Visitor(TimestampModel, UUIDPKModel):
    user = models.OneToOneField(
        "core.ACAUser",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="visitor_sessions",
        help_text="Linked authenticated user, if any",
    )
    emails = ArrayField(
        models.EmailField(),
        default=list,
        editable=False,
        help_text="Email addresses associated with this visitor",
    )
    ip_addresses = ArrayField(
        models.GenericIPAddressField(),
        default=list,
        editable=False,
        help_text="IP addresses this visitor has used",
    )
    request_count = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="Total number of requests from this visitor",
    )
    last_seen_at = models.DateTimeField(
        null=True,
        editable=False,
        help_text="When this visitor was last seen",
    )

    def __str__(self) -> str:
        if self.emails:
            return f"{self.emails[0]} ({str(self.id)})"
        return str(self.id)

    def add_ip_address(self, ip: str) -> None:
        if not ip:
            return
        Visitor.objects.filter(id=self.id).exclude(ip_addresses__contains=[ip]).update(
            ip_addresses=Func(F("ip_addresses"), Value(ip), function="array_append"),
        )

    def add_email(self, email: str) -> None:
        normalized = email.strip().lower()
        if not normalized:
            return
        Visitor.objects.filter(id=self.id).exclude(emails__contains=[normalized]).update(
            emails=Func(F("emails"), Value(normalized), function="array_append"),
        )
