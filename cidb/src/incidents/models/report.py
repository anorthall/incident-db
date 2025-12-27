from django.db import models
from django.db.models import TextChoices

from cidb.src.core.models import Visitor
from cidb.src.core.models.generic import TimestampModel
from cidb.src.incidents.models.incident import Incident


class ReportStatus(TextChoices):
    PENDING = "pending", "Pending Review"
    REVIEWED = "reviewed", "Reviewed"
    RESOLVED = "resolved", "Resolved"
    DISMISSED = "dismissed", "Dismissed"


class ReportReason(TextChoices):
    INACCURATE = "inaccurate", "Inaccurate Information"
    INCOMPLETE = "incomplete", "Missing Information"
    DUPLICATE = "duplicate", "Duplicate Entry"
    TYPO = "typo", "Typographical Error"
    FORMATTING = "formatting", "Formatting Error"
    PRIVACY = "privacy", "Privacy Concern"
    OFFENSIVE = "offensive", "Offensive Content"
    OTHER = "other", "Other"


class ContentReport(TimestampModel):
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name="content_reports",
        null=True,
        blank=True,
    )
    reporter = models.ForeignKey(
        Visitor,
        null=True,
        on_delete=models.SET_NULL,
        related_name="content_reports",
    )
    url = models.URLField(
        max_length=2000,
        blank=True,
    )
    reason = models.CharField(
        choices=ReportReason,
    )
    description = models.TextField(
        help_text="Detailed description of the issue",
    )
    status = models.CharField(
        choices=ReportStatus,
        default=ReportStatus.PENDING,
    )
    reviewer_notes = models.TextField(
        blank=True,
        help_text="Internal notes from reviewer",
    )

    def __str__(self) -> str:
        if self.incident:
            return f"Report on {self.incident}: {self.reason}"
        return f"General feedback: {self.reason}"
