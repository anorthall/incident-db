from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic_ai import Agent

from . import register_operation
from .base import DataOperation, OperationResult, build_references_string, load_prompt

if TYPE_CHECKING:
    from cidb.src.incidents.models import Incident


class DuplicateSourceOutput(BaseModel):
    has_duplicate: bool
    cleaned_text: str
    removed_text: str


@register_operation
class RemoveDuplicateSourcesOperation(DataOperation):
    name = "remove_duplicate_sources"
    version = "1.0"
    description = "Remove duplicate source text from end of reports"
    requires_llm = True

    def __init__(self) -> None:
        self.agent = Agent(
            "openai:gpt-4o-mini",
            system_prompt=load_prompt("remove_duplicate_sources"),
            output_type=DuplicateSourceOutput,
        )
        self.user_prompt_template = load_prompt("remove_duplicate_sources_user")

    async def should_run(self, incident: Incident) -> bool:
        if not incident.report:
            return False
        return await incident.references.aexists()

    async def process(self, incident: Incident) -> OperationResult:
        if not incident.report:
            return OperationResult()

        references_text = await build_references_string(incident)
        if references_text == "N/A":
            return OperationResult()

        prompt = self.user_prompt_template.format(
            report=incident.report,
            references=references_text,
        )

        result = await self.agent.run(prompt)

        if not result.output.has_duplicate:
            return OperationResult()

        old_report = incident.report
        new_report = result.output.cleaned_text.strip()

        if new_report == old_report:
            return OperationResult()

        incident.report = new_report

        return OperationResult(
            changes={
                "report": {"old": old_report, "new": new_report},
                "removed_text": {"old": "", "new": result.output.removed_text},
            },
        )
