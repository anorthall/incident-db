from __future__ import annotations

import re
from typing import TYPE_CHECKING

from . import register_operation
from .base import DataOperation, OperationResult

if TYPE_CHECKING:
    from cidb.src.incidents.models import Incident


@register_operation
class CleanAnalysisCommentsOperation(DataOperation):
    name = "clean_analysis_comments"
    version = "1.0"
    description = "Remove Comments:/Analysis: prefixes from analysis field"
    requires_llm = False

    PREFIXES = [
        r"^Comments?:\s*",
        r"^Analysis:\s*",
        r"^Notes?:\s*",
        r"^Editorial:\s*",
        r"^Editor'?s?\s+Notes?:\s*",
    ]

    async def should_run(self, incident: Incident) -> bool:
        if not incident.analysis:
            return False
        return any(re.match(pattern, incident.analysis, re.IGNORECASE) for pattern in self.PREFIXES)

    async def process(self, incident: Incident) -> OperationResult:
        if not incident.analysis:
            return OperationResult()

        old_analysis = incident.analysis
        new_analysis = old_analysis

        for pattern in self.PREFIXES:
            new_analysis = re.sub(pattern, "", new_analysis, flags=re.IGNORECASE)

        if new_analysis == old_analysis:
            return OperationResult()

        incident.analysis = new_analysis

        return OperationResult(
            changes={"analysis": {"old": old_analysis, "new": new_analysis}},
        )
