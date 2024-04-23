from db.models import Incident
from django.conf import settings
from django.db import models


class EditLogEntry(models.Model):
    ADDED = "added"
    EDITED = "edited"
    DELETED = "deleted"
    VERB_CHOICES = (
        (ADDED, ADDED),
        (EDITED, EDITED),
        (DELETED, DELETED),
    )

    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    incident = models.ForeignKey(
        Incident, on_delete=models.SET_NULL, blank=True, null=True
    )
    incident_name = models.CharField(max_length=200)
    verb = models.CharField(max_length=20, choices=VERB_CHOICES, default=EDITED)
    message = models.CharField(max_length=200)

    def __str__(self):
        if self.incident:
            return f"{self.user} {self.verb} {self.incident}: {self.message}"

        return f"{self.user} {self.verb}: {self.message}"

    def save(self, *args, **kwargs):
        if self.incident:
            self.incident_name = str(self.incident)
        super().save(*args, **kwargs)
