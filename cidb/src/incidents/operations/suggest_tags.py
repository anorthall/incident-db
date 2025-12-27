from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic_ai import Agent

from . import register_operation
from .base import DataOperation, OperationResult, load_prompt

if TYPE_CHECKING:
    from cidb.src.incidents.models import Incident


class TagSuggestionOutput(BaseModel):
    suggested_tags: list[str]
    reasoning: dict[str, str] = {}


@register_operation
class SuggestTagsOperation(DataOperation):
    name = "suggest_tags"
    version = "1.0"
    description = "Suggest tags for incidents based on content"
    requires_llm = True

    def __init__(self) -> None:
        self.agent = Agent(
            "openai:gpt-4o-mini",
            system_prompt=load_prompt("suggest_tags"),
            output_type=TagSuggestionOutput,
        )
        self.user_prompt_template = load_prompt("suggest_tags_user")
        self._cached_tags: list[str] | None = None

    async def _get_available_tags(self) -> list[str]:
        if self._cached_tags is None:
            from cidb.src.incidents.models import Tag

            self._cached_tags = [t async for t in Tag.objects.values_list("name", flat=True)]
        return self._cached_tags

    async def should_run(self, incident: Incident) -> bool:
        return await incident.tags.acount() == 0

    async def process(self, incident: Incident) -> OperationResult:
        available_tags = await self._get_available_tags()
        if not available_tags:
            return OperationResult()

        cave_name = incident.cave.name if incident.cave else "Unknown"

        prompt = self.user_prompt_template.format(
            available_tags="\n".join(f"- {t}" for t in available_tags),
            report=incident.report[:4000] if incident.report else "N/A",
            analysis=incident.analysis[:1000] if incident.analysis else "N/A",
            cave_name=cave_name,
        )

        result = await self.agent.run(prompt)

        valid_tags = [t for t in result.output.suggested_tags if t in available_tags]
        if not valid_tags:
            return OperationResult()

        from cidb.src.incidents.models import Tag

        tag_objects = [t async for t in Tag.objects.filter(name__in=valid_tags)]
        await incident.tags.aadd(*tag_objects)

        return OperationResult(
            changes={
                "tags": {
                    "old": "",
                    "new": ", ".join(valid_tags),
                },
            },
        )
