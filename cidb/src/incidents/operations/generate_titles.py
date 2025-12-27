from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from . import register_operation
from .base import DataOperation, OperationResult, build_references_string, load_prompt

if TYPE_CHECKING:
    from cidb.src.incidents.models import Incident


class TitleOutput(BaseModel):
    title: str = Field(max_length=100)
    reasoning: str


@register_operation
class GenerateTitlesOperation(DataOperation):
    name = "generate_titles"
    version = "1.0"
    description = "Generate titles for all incidents"
    requires_llm = True

    def __init__(self) -> None:
        self.agent = Agent(
            "openai:gpt-4o-mini",
            system_prompt=load_prompt("generate_titles"),
            output_type=TitleOutput,
        )
        self.user_prompt_template = load_prompt("generate_titles_user")

    async def should_run(self, incident: Incident) -> bool:
        return True

    async def process(self, incident: Incident) -> OperationResult:
        cave_name = incident.cave.name if incident.cave else "Unknown"
        location = (
            str(incident.cave.location) if incident.cave and incident.cave.location else "Unknown"
        )
        report = incident.report[:2000] if incident.report else "No report available."
        analysis = incident.analysis[:500] if incident.analysis else "N/A"
        references = await build_references_string(incident)

        prompt = self.user_prompt_template.format(
            cave_name=cave_name,
            location=location,
            report=report,
            analysis=analysis,
            references=references,
        )

        result = await self.agent.run(prompt)
        new_title = result.output.title.strip()

        if new_title == incident.title:
            return OperationResult()

        old_title = incident.title
        incident.title = new_title

        return OperationResult(
            changes={"title": {"old": old_title, "new": new_title}},
        )
