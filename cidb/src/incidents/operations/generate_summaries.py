from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic_ai import Agent

from . import register_operation
from .base import DataOperation, OperationResult, load_prompt

if TYPE_CHECKING:
    from cidb.src.incidents.models import Incident


class SummaryOutput(BaseModel):
    summary: str
    reasoning: str


@register_operation
class GenerateSummariesOperation(DataOperation):
    name = "generate_summaries"
    version = "1.0"
    description = "Generate summaries for incidents without one"
    requires_llm = True

    def __init__(self) -> None:
        self.agent = Agent(
            "openai:gpt-4o-mini",
            system_prompt=load_prompt("generate_summaries"),
            output_type=SummaryOutput,
        )
        self.user_prompt_template = load_prompt("generate_summaries_user")

    async def should_run(self, incident: Incident) -> bool:
        return not incident.summary or not incident.summary.strip()

    async def process(self, incident: Incident) -> OperationResult:
        cave_name = incident.cave.name if incident.cave else "Unknown"
        location = (
            str(incident.cave.location) if incident.cave and incident.cave.location else "Unknown"
        )
        report = incident.report[:2000] if incident.report else "No report available."
        analysis = incident.analysis[:500] if incident.analysis else "N/A"

        tag_names = [tag.name async for tag in incident.tags.all()]
        tags = ", ".join(tag_names) if tag_names else "N/A"

        prompt = self.user_prompt_template.format(
            cave_name=cave_name,
            location=location,
            report=report,
            analysis=analysis,
            tags=tags,
        )

        result = await self.agent.run(prompt)
        new_summary = result.output.summary.strip()

        if new_summary == incident.summary:
            return OperationResult()

        old_summary = incident.summary
        incident.summary = new_summary

        return OperationResult(
            changes={"summary": {"old": old_summary, "new": new_summary}},
        )
