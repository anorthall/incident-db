from django.db import models
from django_stubs_ext.db.models import TypedModelMeta

from cidb.src.core.models.generic import TimestampModel


class OperationStatus(models.TextChoices):
    SUCCESS = "success", "Success"
    SKIPPED = "skipped", "Skipped"
    ERROR = "error", "Error"
    NO_CHANGE = "no_change", "No Change"


class DataOperationLog(TimestampModel):
    incident = models.ForeignKey(
        "Incident",
        on_delete=models.CASCADE,
        related_name="operation_logs",
    )
    operation_name = models.CharField(max_length=100)
    operation_version = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20,
        choices=OperationStatus.choices,
        default=OperationStatus.SUCCESS,
    )
    changes_made = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    class Meta(TypedModelMeta):
        indexes = [
            models.Index(fields=["incident", "operation_name"]),
            models.Index(fields=["operation_name", "created_at"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.operation_name} v{self.operation_version} on {self.incident_id} ({self.status})"
        )
