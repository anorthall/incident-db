from __future__ import annotations

import re
from typing import TYPE_CHECKING

from . import register_operation
from .base import DataOperation, OperationResult

if TYPE_CHECKING:
    from cidb.src.incidents.models import Incident


@register_operation
class CleanReferencesOperation(DataOperation):
    name = "clean_references"
    version = "1.0"
    description = "Clean and normalize reference text fields"
    requires_llm = False

    REFERENCE_FIELDS = ("author", "title", "source", "raw_citation")

    SIMPLE_HYPHEN_FIXES = [
        (r"\bth-e\b", "the"),
        (r"\bth-is\b", "this"),
        (r"\bth-at\b", "that"),
        (r"\bwh-en\b", "when"),
        (r"\bwh-ere\b", "where"),
        (r"\bwh-ich\b", "which"),
        (r"\bwh-at\b", "what"),
        (r"\bca-ve\b", "cave"),
        (r"\bca-ver\b", "caver"),
        (r"\bca-ving\b", "caving"),
        (r"\bin-cident\b", "incident"),
        (r"\bac-cident\b", "accident"),
        (r"\bre-port\b", "report"),
        (r"\bre-scue\b", "rescue"),
    ]

    async def should_run(self, incident: Incident) -> bool:
        return await incident.references.aexists()

    async def process(self, incident: Incident) -> OperationResult:
        changes: dict[str, dict[str, str]] = {}

        async for ref in incident.references.all():
            ref_changed = False
            for field_name in self.REFERENCE_FIELDS:
                old_value = getattr(ref, field_name) or ""
                if not old_value:
                    continue

                new_value = self._clean(old_value)
                if new_value != old_value:
                    key = f"reference_{ref.index}_{field_name}"
                    changes[key] = {"old": old_value, "new": new_value}
                    setattr(ref, field_name, new_value)
                    ref_changed = True

            if ref_changed:
                await ref.asave()

        return OperationResult(changes=changes)

    def _clean(self, text: str) -> str:
        text = text.strip()

        # Remove leading reference numbering (e.g., "1." "2." "1)" "(1)" etc.)
        text = re.sub(r"^\s*\(?(\d+)[.)]\)?\s*", "", text)

        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" +$", "", text, flags=re.MULTILINE)

        for pattern, replacement in self.SIMPLE_HYPHEN_FIXES:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text
