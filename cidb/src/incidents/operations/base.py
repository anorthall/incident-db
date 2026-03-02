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
    name: str
    version: str
    description: str
    requires_llm: bool = True
    model: str = "openai:gpt-4o-mini"

    @abstractmethod
    async def should_run(self, incident: Incident) -> bool: ...

    @abstractmethod
    async def process(self, incident: Incident) -> OperationResult: ...

    async def run(self, incident: Incident) -> OperationResult:
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
