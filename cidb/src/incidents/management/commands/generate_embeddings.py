from __future__ import annotations

from typing import Any

import structlog
from django.core.management.base import BaseCommand, CommandParser
from openai import OpenAI

from cidb.src.incidents.models import Incident, IncidentEmbedding

logger = structlog.get_logger(__name__)

MODEL = "text-embedding-3-small"
BATCH_SIZE = 100


class Command(BaseCommand):
    help = "Generate embeddings for all incidents"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--force",
            action="store_true",
            help="Regenerate embeddings even if they already exist",
        )
        parser.add_argument(
            "--incident-ids",
            type=str,
            help="Comma-separated list of incident IDs to process",
        )

    def handle(self, *args: str, **options: Any) -> None:
        force = bool(options.get("force", False))
        client = OpenAI()

        queryset = Incident.objects.all()

        incident_ids_str: str | None = options.get("incident_ids")
        if incident_ids_str:
            ids = [int(i.strip()) for i in incident_ids_str.split(",")]
            queryset = queryset.filter(pk__in=ids)

        if not force:
            existing_ids = set(IncidentEmbedding.objects.values_list("incident_id", flat=True))
            queryset = queryset.exclude(pk__in=existing_ids)

        incidents = list(queryset.order_by("id"))
        total = len(incidents)

        if total == 0:
            self.stdout.write("No incidents need embeddings generated.")
            return

        self.stdout.write(f"Generating embeddings for {total} incidents...")

        created = 0
        updated = 0
        errors = 0

        for i in range(0, total, BATCH_SIZE):
            batch = incidents[i : i + BATCH_SIZE]
            texts = [self._get_text_for_embedding(inc) for inc in batch]

            try:
                response = client.embeddings.create(model=MODEL, input=texts)

                for j, inc in enumerate(batch):
                    embedding_data = response.data[j].embedding

                    obj, was_created = IncidentEmbedding.objects.update_or_create(
                        incident=inc,
                        defaults={
                            "embedding": embedding_data,
                            "model_version": MODEL,
                        },
                    )
                    if was_created:
                        created += 1
                    else:
                        updated += 1

                self.stdout.write(f"  Processed {min(i + BATCH_SIZE, total)}/{total}")

            except Exception as e:
                logger.exception(f"Error processing batch starting at {i}")
                self.stdout.write(self.style.ERROR(f"  Error at batch {i}: {e}"))
                errors += len(batch)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Created: {created}"))
        self.stdout.write(self.style.SUCCESS(f"Updated: {updated}"))
        if errors > 0:
            self.stdout.write(self.style.ERROR(f"Errors: {errors}"))

    def _get_text_for_embedding(self, incident: Incident) -> str:
        parts = []

        if incident.title:
            parts.append(f"Title: {incident.title}")

        if incident.cave:
            parts.append(f"Cave: {incident.cave.name}")

        if incident.report:
            parts.append(f"Report: {incident.report[:6000]}")

        if incident.analysis:
            parts.append(f"Analysis: {incident.analysis[:1000]}")

        text = "\n\n".join(parts)
        return text[:8000]
