from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic_ai import Agent

from . import register_operation
from .base import DataOperation, OperationResult, build_references_string, load_prompt

if TYPE_CHECKING:
    from cidb.src.incidents.models import Incident


class IncompleteTextOutput(BaseModel):
    is_incomplete: bool
    incomplete_fields: list[str] = []
    details: dict[str, str] = {}


@register_operation
class DetectIncompleteTextOperation(DataOperation):
    name = "detect_incomplete_text"
    version = "1.0"
    description = "Detect cut-off or incomplete text in reports"
    requires_llm = True

    def __init__(self) -> None:
        self.agent = Agent(
            "openai:gpt-4o-mini",
            system_prompt=load_prompt("detect_incomplete_text"),
            output_type=IncompleteTextOutput,
        )
        self.user_prompt_template = load_prompt("detect_incomplete_text_user")

    async def should_run(self, incident: Incident) -> bool:
        return bool(incident.report or incident.analysis)

    async def process(self, incident: Incident) -> OperationResult:
        prompt = self.user_prompt_template.format(
            report=incident.report or "N/A",
            analysis=incident.analysis or "N/A",
            references=await build_references_string(incident),
        )

        result = await self.agent.run(prompt)

        if not result.output.is_incomplete:
            return OperationResult()

        return OperationResult(
            changes={
                "incomplete_detected": {
                    "old": "",
                    "new": ", ".join(result.output.incomplete_fields),
                },
                "incomplete_details": {
                    "old": "",
                    "new": str(result.output.details),
                },
            },
        )
