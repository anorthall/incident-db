from __future__ import annotations

import re
from typing import TYPE_CHECKING

from . import register_operation
from .base import DataOperation, OperationResult

if TYPE_CHECKING:
    from cidb.src.incidents.models import Incident


@register_operation
class NormalizeWhitespaceOperation(DataOperation):
    name = "normalize_whitespace"
    version = "1.0"
    description = "Normalize whitespace in all text fields"
    requires_llm = False

    INCIDENT_FIELDS = ("title", "report", "analysis", "summary")
    REFERENCE_FIELDS = ("author", "title", "source", "raw_citation")

    async def should_run(self, incident: Incident) -> bool:
        return True

    async def process(self, incident: Incident) -> OperationResult:
        changes: dict[str, dict[str, str]] = {}

        for field_name in self.INCIDENT_FIELDS:
            old_value = getattr(incident, field_name) or ""
            if old_value:
                new_value = self._normalize(old_value)
                if new_value != old_value:
                    changes[field_name] = {"old": old_value, "new": new_value}
                    setattr(incident, field_name, new_value)

        async for ref in incident.references.all():
            for field_name in self.REFERENCE_FIELDS:
                old_value = getattr(ref, field_name) or ""
                if old_value:
                    new_value = self._normalize(old_value)
                    if new_value != old_value:
                        key = f"reference_{ref.index}_{field_name}"
                        changes[key] = {"old": old_value, "new": new_value}
                        setattr(ref, field_name, new_value)
                        await ref.asave()

        return OperationResult(changes=changes)

    def _normalize(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" +$", "", text, flags=re.MULTILINE)
        return re.sub(r"\n{3,}", "\n\n", text)
