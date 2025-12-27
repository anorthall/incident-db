from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from cidb.src.incidents.models import Incident

logger = structlog.get_logger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


async def build_references_string(incident: Incident) -> str:
    """Build a formatted string of references for an incident.

    Args:
        incident: The incident with prefetched references.

    Returns:
        A formatted string with one reference per line, or "N/A" if none.
    """
    refs = []
    async for ref in incident.references.all():
        if ref.raw_citation:
            refs.append(ref.raw_citation)
        else:
            parts = [ref.author, ref.title, ref.source]
            refs.append(", ".join(p for p in parts if p))
    return "\n".join(f"- {r}" for r in refs) if refs else "N/A"


def load_prompt(name: str) -> str:
    prompt_file = PROMPTS_DIR / f"{name}.txt"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    return prompt_file.read_text()


class OperationResultStatus(Enum):
    ERROR = auto()
    SKIPPED = auto()
    SUCCESS = auto()
    NO_CHANGE = auto()


@dataclass(frozen=True, slots=True)
class OperationResult:
    changes: dict[str, dict[str, str]] = field(default_factory=dict)
    skipped: bool = False
    error: str | None = None

    @property
    def has_changes(self) -> bool:
        return bool(self.changes) and not self.skipped and not self.error

    @property
    def status(self) -> OperationResultStatus:
        if self.error:
            return OperationResultStatus.ERROR
        if self.skipped:
            return OperationResultStatus.SKIPPED
        if self.changes:
            return OperationResultStatus.SUCCESS
        return OperationResultStatus.NO_CHANGE


class DataOperation(ABC):
    """Base class for all data operations.

    Data operations are modular units that can be run on incidents to clean,
    transform, or enhance their data. Each operation has a name, version, and
    description, and can optionally use an LLM for processing.
    """

    name: str
    version: str
    description: str
    requires_llm: bool = True
    model: str = "openai:gpt-4o-mini"

    @abstractmethod
    async def should_run(self, incident: Incident) -> bool:
        """Determine if this operation should process the given incident.

        Args:
            incident: The incident to check.

        Returns:
            True if the operation should run on this incident.
        """

    @abstractmethod
    async def process(self, incident: Incident) -> OperationResult:
        """Process the incident and return the result.

        This method should make changes to the incident object directly.
        The caller is responsible for saving the incident after processing.

        Args:
            incident: The incident to process.

        Returns:
            OperationResult with details about what changed.
        """

    async def run(self, incident: Incident) -> OperationResult:
        """Run the operation with logging."""
        logger.info(
            "operation_started",
            operation=self.name,
            version=self.version,
            incident_id=incident.id,
        )
        try:
            result = await self.process(incident)
            logger.info(
                "operation_completed",
                operation=self.name,
                incident_id=incident.id,
                status=result.status.name,
                has_changes=result.has_changes,
            )
            return result
        except Exception:
            logger.exception(
                "operation_failed",
                operation=self.name,
                incident_id=incident.id,
            )
            raise

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"
