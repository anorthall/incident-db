from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from django.core.management.base import BaseCommand, CommandParser
from django.db import models, transaction

from cidb.src.incidents.models import (
    DuplicateGroup,
    DuplicateStatus,
    IncidentPerson,
)

if TYPE_CHECKING:
    from cidb.src.incidents.models import Incident


class Command(BaseCommand):
    help = "Review and merge duplicate incident groups"

    def add_arguments(self, parser: CommandParser) -> None:
        subparsers = parser.add_subparsers(dest="action", help="Action to perform")

        # List pending groups
        list_parser = subparsers.add_parser("list", help="List pending duplicate groups")
        list_parser.add_argument(
            "--all",
            action="store_true",
            help="Show all groups, not just pending",
        )

        # Show details of a specific group
        show_parser = subparsers.add_parser("show", help="Show details of a duplicate group")
        show_parser.add_argument("group_id", type=int, help="Group ID to show")

        # Merge a group
        merge_parser = subparsers.add_parser("merge", help="Merge a duplicate group")
        merge_parser.add_argument("group_id", type=int, nargs="?", help="Group ID to merge")
        merge_parser.add_argument(
            "--all",
            action="store_true",
            help="Merge all pending groups",
        )
        merge_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview merge without making changes",
        )

        # Reject a group (mark as not duplicate)
        reject_parser = subparsers.add_parser("reject", help="Reject a group as not duplicate")
        reject_parser.add_argument("group_id", type=int, help="Group ID to reject")

        # Set primary incident for a group
        primary_parser = subparsers.add_parser("set-primary", help="Set the primary incident")
        primary_parser.add_argument("group_id", type=int, help="Group ID")
        primary_parser.add_argument("incident_id", type=int, help="Incident ID to set as primary")

    def handle(self, *args: str, **options: object) -> None:
        action = options.get("action")

        if action == "list":
            self._list_groups(show_all=bool(options.get("all")))
        elif action == "show":
            self._show_group(int(str(options["group_id"])))
        elif action == "merge":
            group_id = options.get("group_id")
            merge_all = bool(options.get("all"))
            dry_run = bool(options.get("dry_run"))

            if merge_all:
                self._merge_all(dry_run=dry_run)
            elif group_id:
                self._merge_group(int(str(group_id)), dry_run=dry_run)
            else:
                self.stderr.write(self.style.ERROR("Specify --all or a group_id"))
        elif action == "reject":
            self._reject_group(int(str(options["group_id"])))
        elif action == "set-primary":
            self._set_primary(
                int(str(options["group_id"])),
                int(str(options["incident_id"])),
            )
        else:
            self.stdout.write("Usage: merge_duplicates <list|show|merge|reject|set-primary>")
            self.stdout.write("\nRun with --help for more information")

    def _list_groups(self, show_all: bool = False) -> None:
        queryset = DuplicateGroup.objects.prefetch_related(
            "members__incident__cave"
        ).select_related("primary_incident__cave")

        if not show_all:
            queryset = queryset.filter(status=DuplicateStatus.PENDING)

        groups = list(queryset.order_by("-created_at"))

        if not groups:
            self.stdout.write("No duplicate groups found.")
            return

        self.stdout.write(f"\n{'ID':<6} {'Status':<12} {'Primary':<40} {'Members':<8}")
        self.stdout.write("-" * 70)

        for group in groups:
            primary = group.primary_incident
            primary_str = (
                f"{primary.title[:37]}..."
                if primary and len(primary.title) > 40
                else (primary.title if primary else "None")
            )
            member_count = group.members.count()

            def identity(x: str) -> str:
                return x

            style_map: dict[str, Callable[[str], str]] = {
                DuplicateStatus.PENDING: self.style.WARNING,
                DuplicateStatus.CONFIRMED: self.style.SUCCESS,
                DuplicateStatus.REJECTED: self.style.ERROR,
                DuplicateStatus.MERGED: self.style.SUCCESS,
            }
            status_style = style_map.get(group.status, identity)

            self.stdout.write(
                f"{group.id:<6} {status_style(group.status.ljust(12))} "
                f"{primary_str:<40} {member_count:<8}"
            )

        self.stdout.write(f"\nTotal: {len(groups)} group(s)")

    def _show_group(self, group_id: int) -> None:
        try:
            group = (
                DuplicateGroup.objects.prefetch_related(
                    "members__incident__cave",
                    "members__incident__tags",
                )
                .select_related("primary_incident__cave")
                .get(pk=group_id)
            )
        except DuplicateGroup.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Group {group_id} not found"))
            return

        self.stdout.write(f"\n{'=' * 80}")
        self.stdout.write(f"Duplicate Group #{group.id}")
        self.stdout.write(f"Status: {group.status}")
        self.stdout.write(f"Primary: {group.primary_incident_id}")
        if group.notes:
            self.stdout.write(f"Notes: {group.notes}")
        self.stdout.write(f"{'=' * 80}\n")

        for member in group.members.all():
            incident = member.incident
            is_primary = incident.id == group.primary_incident_id

            self.stdout.write(f"{'[PRIMARY] ' if is_primary else ''}Incident #{incident.id}")
            self.stdout.write(f"  Title: {incident.title}")
            self.stdout.write(f"  Cave: {incident.cave.name if incident.cave else 'Unknown'}")
            self.stdout.write(f"  Date: {incident.date}")
            self.stdout.write(f"  Similarity: {member.similarity_score:.3f}")
            self.stdout.write(f"  LLM Confidence: {member.llm_confidence}%")

            if incident.report:
                preview = incident.report[:200].replace("\n", " ")
                self.stdout.write(f"  Report: {preview}...")

            if incident.tags.exists():
                tags = ", ".join(t.name for t in incident.tags.all())
                self.stdout.write(f"  Tags: {tags}")

            self.stdout.write(f"  LLM Reasoning: {member.llm_reasoning}")
            self.stdout.write("")

    def _merge_group(self, group_id: int, dry_run: bool = False) -> None:
        try:
            group = (
                DuplicateGroup.objects.prefetch_related(
                    "members__incident__cave",
                    "members__incident__tags",
                    "members__incident__references",
                    "members__incident__persons_involved",
                )
                .select_related("primary_incident")
                .get(pk=group_id)
            )
        except DuplicateGroup.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Group {group_id} not found"))
            return

        if group.status == DuplicateStatus.MERGED:
            self.stderr.write(self.style.WARNING(f"Group {group_id} already merged"))
            return

        if group.status == DuplicateStatus.REJECTED:
            self.stderr.write(self.style.WARNING(f"Group {group_id} was rejected"))
            return

        primary = group.primary_incident
        if not primary:
            self.stderr.write(self.style.ERROR("No primary incident set. Use set-primary first."))
            return

        duplicates = [m.incident for m in group.members.all() if m.incident_id != primary.id]

        if not duplicates:
            self.stderr.write(self.style.WARNING("No duplicates to merge"))
            return

        self.stdout.write(f"\nMerging group #{group_id}")
        self.stdout.write(f"  Primary: #{primary.id} - {primary.title}")
        self.stdout.write(f"  Duplicates: {[d.id for d in duplicates]}")

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN - showing what would happen:\n"))
            self._preview_merge(primary, duplicates)
            self.stdout.write(self.style.WARNING("\nNo changes made (dry run)"))
            return

        try:
            with transaction.atomic():
                self._execute_merge(primary, duplicates, group)
            self.stdout.write(
                self.style.SUCCESS(f"\nMerged {len(duplicates)} duplicate(s) into #{primary.id}")
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"\nMerge failed: {e}"))
            self.stderr.write("All changes have been rolled back.")

    def _preview_merge(self, primary: Incident, duplicates: list[Incident]) -> None:
        all_tags = set(primary.tags.all())
        for dup in duplicates:
            all_tags.update(dup.tags.all())
        if len(all_tags) > primary.tags.count():
            self.stdout.write(f"  + Adding {len(all_tags) - primary.tags.count()} tags")

        total_views = primary.view_count + sum(d.view_count for d in duplicates)
        if total_views > primary.view_count:
            self.stdout.write(f"  + Combining view count: {primary.view_count} -> {total_views}")

        for dup in duplicates:
            ref_count = dup.references.count()
            if ref_count > 0:
                self.stdout.write(f"  + Moving {ref_count} references from #{dup.id}")

        for dup in duplicates:
            for person_link in dup.persons_involved.all():
                if not IncidentPerson.objects.filter(
                    incident=primary, person=person_link.person
                ).exists():
                    self.stdout.write(f"  + Moving person {person_link.person_id} from #{dup.id}")

        for dup in duplicates:
            if dup.report and dup.report.strip() != primary.report.strip():
                self.stdout.write(f"  + Appending report from #{dup.id}")

        for dup in duplicates:
            self.stdout.write(f"  - Deleting duplicate #{dup.id}")

    def _execute_merge(
        self,
        primary: Incident,
        duplicates: list[Incident],
        group: DuplicateGroup,
    ) -> None:
        # Merge tags
        all_tags = set(primary.tags.all())
        for dup in duplicates:
            all_tags.update(dup.tags.all())
        if len(all_tags) > primary.tags.count():
            self.stdout.write(f"  + Adding {len(all_tags) - primary.tags.count()} tags")
            primary.tags.set(all_tags)

        # Merge view counts
        total_views = primary.view_count + sum(d.view_count for d in duplicates)
        if total_views > primary.view_count:
            self.stdout.write(f"  + Combining view count: {primary.view_count} -> {total_views}")
            primary.view_count = total_views

        # Collect all report appendages first
        report_additions = []
        for dup in duplicates:
            if dup.report and dup.report.strip() != primary.report.strip():
                self.stdout.write(f"  + Appending report from #{dup.id}")
                report_additions.append(
                    f"\n\n---\n[Merged from incident #{dup.id}]\n\n{dup.report}"
                )

        if report_additions:
            primary.report = primary.report + "".join(report_additions)

        # Save primary once with all changes
        primary.save(update_fields=["view_count", "report"])

        # Reassign references
        for dup in duplicates:
            ref_count = dup.references.count()
            if ref_count > 0:
                self.stdout.write(f"  + Moving {ref_count} references from #{dup.id}")
                max_idx = primary.references.aggregate(m=models.Max("index"))["m"] or 0
                for ref in dup.references.all():
                    max_idx += 1
                    ref.incident = primary
                    ref.index = max_idx
                    ref.save()

        # Reassign persons involved
        for dup in duplicates:
            for person_link in dup.persons_involved.all():
                if not IncidentPerson.objects.filter(
                    incident=primary, person=person_link.person
                ).exists():
                    self.stdout.write(f"  + Moving person {person_link.person_id} from #{dup.id}")
                    person_link.incident = primary
                    person_link.save()

        # Delete duplicates
        for dup in duplicates:
            self.stdout.write(f"  - Deleting duplicate #{dup.id}")
            dup.delete()

        # Update group status
        group.status = DuplicateStatus.MERGED
        group.save(update_fields=["status"])

    def _merge_all(self, dry_run: bool = False) -> None:
        groups = DuplicateGroup.objects.filter(status=DuplicateStatus.PENDING)
        count = groups.count()

        if count == 0:
            self.stdout.write("No pending groups to merge.")
            return

        self.stdout.write(f"Merging {count} pending group(s)...")

        for group in groups:
            self._merge_group(group.id, dry_run=dry_run)
            self.stdout.write("")

    def _reject_group(self, group_id: int) -> None:
        try:
            group = DuplicateGroup.objects.get(pk=group_id)
        except DuplicateGroup.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Group {group_id} not found"))
            return

        group.status = DuplicateStatus.REJECTED
        group.save(update_fields=["status"])

        self.stdout.write(self.style.SUCCESS(f"Rejected group #{group_id}"))

    def _set_primary(self, group_id: int, incident_id: int) -> None:
        try:
            group = DuplicateGroup.objects.prefetch_related("members").get(pk=group_id)
        except DuplicateGroup.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Group {group_id} not found"))
            return

        member_ids = [m.incident_id for m in group.members.all()]
        if incident_id not in member_ids:
            self.stderr.write(
                self.style.ERROR(f"Incident {incident_id} is not a member of group {group_id}")
            )
            return

        group.primary_incident_id = incident_id
        group.save(update_fields=["primary_incident_id"])

        self.stdout.write(self.style.SUCCESS(f"Set primary incident to #{incident_id}"))
