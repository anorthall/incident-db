import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import EditLogEntry

EditLog = logging.getLogger("edit_log")


@receiver(post_save)
def log_edit(sender, instance, created, **kwargs):
    if not sender == EditLogEntry or not created:
        return

    EditLog.info(str(instance))
