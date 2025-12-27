"""Management command to run data operations on incidents.

Usage:
    # Run all operations on all incidents
    python manage.py run_data_operations

    # Run specific operations only
    python manage.py run_data_operations --ops whitespace,titles

    # Dry run (preview changes)
    python manage.py run_data_operations --dry-run

    # Process specific incident(s)
    python manage.py run_data_operations --incident-ids 1,2,3

    # Reprocess already processed incidents
    python manage.py run_data_operations --reprocess

    # Force re-run even if already processed
    python manage.py run_data_operations --force
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import structlog
from django.core.management.base import BaseCommand, CommandParser
from django.db.models import QuerySet

from cidb.src.incidents.models import DataOperationLog, Incident, OperationStatus
from cidb.src.incidents.operations import get_all_operations, get_operation, list_operations

if TYPE_CHECKING:
    from cidb.src.incidents.operations.base import DataOperation, OperationResult

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = "Run data operations on incidents to clean and enhance data"

    def __init__(self) -> None:
        super().__init__()
        self.dry_run = False
        self.verbose = False
        self.stats: dict[str, dict[str, int]] = {}

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--ops",
            type=str,
            help="Comma-separated list of operations to run (default: all)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without saving",
        )
        parser.add_argument(
            "--incident-ids",
            type=str,
            help="Comma-separated list of incident IDs to process",
        )
        parser.add_argument(
            "--reprocess",
            action="store_true",
            help="Process incidents again, even if already processed by an operation",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force re-run even if already processed",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="List all available operations and exit",
        )
        parser.add_argument(
            "--concurrency",
            type=int,
            default=50,
            help="Number of incidents to process concurrently (default: 50)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if options.get("list"):
            self._list_operations()
            return

        self.dry_run = bool(options.get("dry_run", False))
        self.verbose = int(options.get("verbosity", 1)) > 1

        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no changes will be saved"))

        operations = self._get_operations(options.get("ops"))
        if not operations:
            self.stdout.write(self.style.ERROR("No operations to run"))
            return

        self.stdout.write(f"Running {len(operations)} operation(s):")
        for op in operations:
            self.stdout.write(f"  - {op.name} v{op.version}: {op.description}")

        incidents = list(self._get_incidents(options))
        total = len(incidents)
        self.stdout.write(f"\nProcessing {total} incident(s)...")

        for op in operations:
            self.stats[op.name] = {
                "success": 0,
                "skipped": 0,
                "error": 0,
                "no_change": 0,
            }

        reprocess = bool(options.get("reprocess", False))
        force = bool(options.get("force", False))
        concurrency = int(options.get("concurrency", 50))

        self.stdout.write(f"Concurrency: {concurrency} parallel incidents")

        self._process_incidents(
            incidents=incidents,
            operations=operations,
            skip_processed=not reprocess,
            force=force,
            concurrency=concurrency,
        )

        self._print_summary()

    def _list_operations(self) -> None:
        self.stdout.write("Available operations:")
        for name in list_operations():
            op = get_operation(name)
            llm_marker = "" if op.requires_llm else " [programmatic]"
            self.stdout.write(f"  {op.name} v{op.version}{llm_marker}")
            self.stdout.write(f"    {op.description}")

    def _get_operations(self, ops_str: str | None) -> list[DataOperation]:
        if ops_str:
            names = [n.strip() for n in ops_str.split(",")]
            return [get_operation(name) for name in names]
        return get_all_operations()

    def _get_incidents(self, options: dict[str, Any]) -> QuerySet[Incident]:
        queryset = Incident.objects.select_related("cave", "cave__location", "source_extract")
        queryset = queryset.prefetch_related("references", "tags")

        incident_ids_str = options.get("incident_ids")
        if incident_ids_str:
            ids = [int(i.strip()) for i in incident_ids_str.split(",")]
            queryset = queryset.filter(pk__in=ids)

        return queryset.order_by("id")

    def _process_incidents(
        self,
        incidents: list[Incident],
        operations: list[DataOperation],
        skip_processed: bool,
        force: bool,
        concurrency: int,
    ) -> None:
        asyncio.run(
            self._process_incidents_async(
                incidents=incidents,
                operations=operations,
                skip_processed=skip_processed,
                force=force,
                concurrency=concurrency,
            )
        )

    async def _process_incidents_async(
        self,
        incidents: list[Incident],
        operations: list[DataOperation],
        skip_processed: bool,
        force: bool,
        concurrency: int,
    ) -> None:
        semaphore = asyncio.Semaphore(concurrency)
        processed_count = 0
        total = len(incidents)
        lock = asyncio.Lock()

        async def process_single_incident(incident: Incident, index: int) -> None:
            nonlocal processed_count
            async with semaphore:
                if self.verbose:
                    title = incident.title[:50]
                    self.stdout.write(f"\n[{index}/{total}] Incident {incident.id}: {title}...")

                for operation in operations:
                    await self._run_operation_async(
                        incident=incident,
                        operation=operation,
                        skip_processed=skip_processed,
                        force=force,
                    )

                async with lock:
                    processed_count += 1
                    if processed_count % 100 == 0:
                        self.stdout.write(
                            f"Progress: {processed_count}/{total} incidents processed"
                        )

        async with asyncio.TaskGroup() as tg:
            for i, incident in enumerate(incidents, 1):
                tg.create_task(process_single_incident(incident, i))

    async def _run_operation_async(
        self,
        incident: Incident,
        operation: DataOperation,
        skip_processed: bool,
        force: bool,
    ) -> None:
        if not force and skip_processed:
            existing = await DataOperationLog.objects.filter(
                incident=incident,
                operation_name=operation.name,
                operation_version=operation.version,
                status=OperationStatus.SUCCESS,
            ).aexists()

            if existing:
                if self.verbose:
                    self.stdout.write(f"    {operation.name}: skipped (already processed)")
                self.stats[operation.name]["skipped"] += 1
                return

        should_run = await operation.should_run(incident)
        if not should_run:
            if self.verbose:
                self.stdout.write(f"    {operation.name}: skipped (should_run=False)")
            self.stats[operation.name]["skipped"] += 1
            return

        try:
            if self.dry_run:
                result = await operation.process(incident)
                await self._handle_result(incident, operation, result)
            else:
                result = await operation.process(incident)
                await self._handle_result(incident, operation, result)

        except Exception as e:
            logger.exception(f"Error running {operation.name} on incident {incident.id}")
            await self._record_error(incident, operation, str(e))

    async def _handle_result(
        self,
        incident: Incident,
        operation: DataOperation,
        result: OperationResult,
    ) -> None:
        status = result.status.name.lower()

        if self.verbose:
            if result.has_changes:
                self.stdout.write(f"    {operation.name}: {len(result.changes)} change(s)")
                for field, change in result.changes.items():
                    old_preview = (
                        (change["old"][:50] + "...") if len(change["old"]) > 50 else change["old"]
                    )
                    new_preview = (
                        (change["new"][:50] + "...") if len(change["new"]) > 50 else change["new"]
                    )
                    self.stdout.write(f"      {field}: '{old_preview}' -> '{new_preview}'")
            else:
                self.stdout.write(f"    {operation.name}: {status}")

        self.stats[operation.name][status] += 1

        if not self.dry_run:
            if result.has_changes:
                await incident.asave()

            await DataOperationLog.objects.acreate(
                incident=incident,
                operation_name=operation.name,
                operation_version=operation.version,
                status=status,
                changes_made=result.changes,
                error_message=result.error or "",
            )

    async def _record_error(
        self,
        incident: Incident,
        operation: DataOperation,
        error_message: str,
    ) -> None:
        self.stats[operation.name]["error"] += 1
        self.stdout.write(self.style.ERROR(f"    {operation.name}: ERROR - {error_message[:100]}"))

        if not self.dry_run:
            await DataOperationLog.objects.acreate(
                incident=incident,
                operation_name=operation.name,
                operation_version=operation.version,
                status=OperationStatus.ERROR,
                changes_made={},
                error_message=error_message,
            )

    def _print_summary(self) -> None:
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("Summary:")
        self.stdout.write("=" * 50)

        for op_name, stats in self.stats.items():
            total = sum(stats.values())
            self.stdout.write(f"\n{op_name}:")
            self.stdout.write(f"  Total processed: {total}")
            self.stdout.write(f"  Success:   {stats['success']}")
            self.stdout.write(f"  No change: {stats['no_change']}")
            self.stdout.write(f"  Skipped:   {stats['skipped']}")
            if stats["error"] > 0:
                self.stdout.write(self.style.ERROR(f"  Errors:    {stats['error']}"))

        if self.dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN - no changes were saved"))
