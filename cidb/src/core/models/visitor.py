from __future__ import annotations

from django.contrib.postgres.fields import ArrayField
from django.db import models

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
        if ip and ip not in self.ip_addresses:
            self.ip_addresses.append(ip)
            self.save(update_fields=["ip_addresses", "updated_at"])

    def add_email(self, email: str) -> None:
        normalized = email.strip().lower()
        if normalized and normalized not in [e.lower() for e in self.emails]:
            self.emails.append(normalized)
            self.save(update_fields=["emails", "updated_at"])
