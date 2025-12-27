from __future__ import annotations

import math
from collections import defaultdict
from itertools import combinations

import structlog
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from cidb.src.incidents.models import (
    DuplicateGroup,
    DuplicateGroupMember,
    DuplicateStatus,
    Incident,
    IncidentEmbedding,
)
from cidb.src.incidents.operations.base import load_prompt

logger = structlog.get_logger(__name__)

MIN_SIMILARITY = 0.85
MIN_LLM_CONFIDENCE = 70


class DuplicateCheckOutput(BaseModel):
    is_duplicate: bool
    confidence: int = Field(ge=0, le=100)
    reasoning: str
    recommended_primary_id: int | None = None


class Command(BaseCommand):
    help = "Detect potential duplicate incidents"

    def __init__(self) -> None:
        super().__init__()
        self.dry_run = False
        self.stage1_only = False
        self.verbose = False
        self.threshold = MIN_SIMILARITY

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview candidates without saving",
        )
        parser.add_argument(
            "--stage1-only",
            action="store_true",
            help="Only run Stage 1 (similarity), skip LLM verification",
        )
        parser.add_argument(
            "--threshold",
            type=float,
            default=MIN_SIMILARITY,
            help=f"Similarity threshold (default: {MIN_SIMILARITY})",
        )
        parser.add_argument(
            "--cave-id",
            type=int,
            help="Only process incidents from this cave",
        )

    def handle(self, *args: str, **options: object) -> None:  # noqa: ANN401
        self.dry_run = bool(options.get("dry_run", False))
        self.stage1_only = bool(options.get("stage1_only", False))
        threshold = options.get("threshold")
        self.threshold = float(str(threshold)) if threshold is not None else MIN_SIMILARITY
        verbosity = options.get("verbosity")
        self.verbose = int(str(verbosity)) > 1 if verbosity is not None else False

        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no changes will be saved"))

        cave_id = options.get("cave_id")
        embeddings = self._load_embeddings(int(str(cave_id)) if cave_id else None)
        if not embeddings:
            self.stdout.write(
                self.style.ERROR("No embeddings found. Run generate_embeddings first.")
            )
            return

        self.stdout.write(f"Loaded {len(embeddings)} incident embeddings")

        blocks = self._create_blocks(embeddings)
        self.stdout.write(f"Created {len(blocks)} blocks for comparison")

        candidates = self._find_candidates(blocks, embeddings)
        self.stdout.write(
            f"Found {len(candidates)} candidate pairs (similarity > {self.threshold})"
        )

        if not candidates:
            self.stdout.write("No duplicate candidates found.")
            return

        if self.stage1_only:
            self._report_candidates(candidates)
            return

        duplicates = self._verify_with_llm(candidates)
        self.stdout.write(f"LLM confirmed {len(duplicates)} duplicate pairs")

        if duplicates and not self.dry_run:
            self._save_duplicate_groups(duplicates)

    def _load_embeddings(self, cave_id: int | None) -> dict[int, list[float]]:
        queryset = IncidentEmbedding.objects.select_related("incident__cave")

        if cave_id:
            queryset = queryset.filter(incident__cave_id=cave_id)

        return {emb.incident_id: emb.embedding for emb in queryset.iterator()}

    def _create_blocks(
        self, embeddings: dict[int, list[float]]
    ) -> dict[tuple[int, int], list[int]]:
        blocks: dict[tuple[int, int], list[int]] = defaultdict(list)

        incidents = Incident.objects.filter(pk__in=embeddings.keys()).select_related("cave")

        for incident in incidents.iterator():
            if incident.date is None:
                continue
            cave_id = incident.cave_id
            year = incident.date.year
            key = (cave_id, year)
            blocks[key].append(incident.id)

        return blocks

    def _find_candidates(
        self,
        blocks: dict[tuple[int, int], list[int]],
        embeddings: dict[int, list[float]],
    ) -> list[tuple[int, int, float]]:
        candidates = []

        for (_cave_id, _year), incident_ids in blocks.items():
            if len(incident_ids) < 2:
                continue

            for id_a, id_b in combinations(incident_ids, 2):
                emb_a = embeddings.get(id_a)
                emb_b = embeddings.get(id_b)

                if emb_a is None or emb_b is None:
                    continue

                similarity = self._cosine_similarity(emb_a, emb_b)

                if similarity >= self.threshold:
                    candidates.append((id_a, id_b, similarity))

                    if self.verbose:
                        self.stdout.write(f"  Candidate: {id_a} <-> {id_b} (sim={similarity:.3f})")

        return sorted(candidates, key=lambda x: -x[2])

    def _cosine_similarity(self, emb1: list[float], emb2: list[float]) -> float:
        dot_product = sum(a * b for a, b in zip(emb1, emb2, strict=True))
        norm1 = math.sqrt(sum(a * a for a in emb1))
        norm2 = math.sqrt(sum(b * b for b in emb2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _report_candidates(self, candidates: list[tuple[int, int, float]]) -> None:
        self.stdout.write("\nCandidate pairs (Stage 1 only):")
        for id_a, id_b, similarity in candidates[:50]:
            self.stdout.write(f"  {id_a} <-> {id_b}: similarity={similarity:.3f}")

        if len(candidates) > 50:
            self.stdout.write(f"  ... and {len(candidates) - 50} more")

    def _verify_with_llm(
        self, candidates: list[tuple[int, int, float]]
    ) -> list[tuple[int, int, float, DuplicateCheckOutput]]:
        agent = Agent(
            "openai:gpt-4o-mini",
            system_prompt=load_prompt("detect_duplicates"),
            output_type=DuplicateCheckOutput,
        )
        user_prompt_template = load_prompt("detect_duplicates_user")

        incident_ids = set()
        for id_a, id_b, _ in candidates:
            incident_ids.add(id_a)
            incident_ids.add(id_b)

        incidents = {
            inc.id: inc
            for inc in Incident.objects.filter(pk__in=incident_ids).select_related("cave")
        }

        duplicates = []
        total = len(candidates)

        for i, (id_a, id_b, similarity) in enumerate(candidates, 1):
            inc_a = incidents.get(id_a)
            inc_b = incidents.get(id_b)

            if not inc_a or not inc_b:
                continue

            prompt = user_prompt_template.format(
                id_a=id_a,
                cave_a=inc_a.cave.name if inc_a.cave else "Unknown",
                date_a=str(inc_a.date) if inc_a.date else "Unknown",
                report_a=inc_a.report[:2000] if inc_a.report else "N/A",
                analysis_a=inc_a.analysis[:500] if inc_a.analysis else "N/A",
                id_b=id_b,
                cave_b=inc_b.cave.name if inc_b.cave else "Unknown",
                date_b=str(inc_b.date) if inc_b.date else "Unknown",
                report_b=inc_b.report[:2000] if inc_b.report else "N/A",
                analysis_b=inc_b.analysis[:500] if inc_b.analysis else "N/A",
            )

            try:
                import asyncio

                result = asyncio.run(agent.run(prompt))
                output = result.output

                if output.is_duplicate and output.confidence >= MIN_LLM_CONFIDENCE:
                    duplicates.append((id_a, id_b, similarity, output))
                    self.stdout.write(
                        f"  [{i}/{total}] {id_a} <-> {id_b}: DUPLICATE (conf={output.confidence})"
                    )
                elif self.verbose:
                    self.stdout.write(
                        f"  [{i}/{total}] {id_a} <-> {id_b}: "
                        f"not duplicate (conf={output.confidence})"
                    )

            except Exception as e:
                logger.exception(f"Error checking {id_a} <-> {id_b}")
                self.stdout.write(self.style.ERROR(f"  [{i}/{total}] Error: {e}"))

        return duplicates

    def _save_duplicate_groups(
        self, duplicates: list[tuple[int, int, float, DuplicateCheckOutput]]
    ) -> None:
        groups_created = 0
        members_created = 0
        skipped = 0

        incident_to_group: dict[int, DuplicateGroup] = {}

        # Load existing group memberships to avoid duplicates on rerun
        existing_memberships = DuplicateGroupMember.objects.select_related("group").filter(
            group__status__in=[DuplicateStatus.PENDING, DuplicateStatus.CONFIRMED]
        )
        for membership in existing_memberships:
            incident_to_group[membership.incident_id] = membership.group

        with transaction.atomic():
            for id_a, id_b, similarity, output in duplicates:
                # Check if both incidents are already in the same group
                group_a = incident_to_group.get(id_a)
                group_b = incident_to_group.get(id_b)

                if group_a and group_b and group_a.id == group_b.id:
                    skipped += 1
                    continue

                existing_group = group_a or group_b

                if existing_group:
                    group = existing_group
                else:
                    primary_id = output.recommended_primary_id
                    if primary_id not in (id_a, id_b):
                        primary_id = id_a

                    group = DuplicateGroup.objects.create(
                        status=DuplicateStatus.PENDING,
                        primary_incident_id=primary_id,
                    )
                    groups_created += 1

                for incident_id in (id_a, id_b):
                    if incident_id in incident_to_group:
                        continue

                    DuplicateGroupMember.objects.create(
                        group=group,
                        incident_id=incident_id,
                        similarity_score=similarity,
                        llm_confidence=output.confidence,
                        llm_reasoning=output.reasoning[:1000],
                    )
                    members_created += 1
                    incident_to_group[incident_id] = group

        self.stdout.write(self.style.SUCCESS(f"Created {groups_created} duplicate groups"))
        self.stdout.write(self.style.SUCCESS(f"Created {members_created} group members"))
        if skipped:
            self.stdout.write(f"Skipped {skipped} pairs (already in groups)")
