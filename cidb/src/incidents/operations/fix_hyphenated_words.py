from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic_ai import Agent

from . import register_operation
from .base import DataOperation, OperationResult, load_prompt

if TYPE_CHECKING:
    from cidb.src.incidents.models import Incident


class HyphenationOutput(BaseModel):
    corrected_text: str


@register_operation
class FixHyphenatedWordsOperation(DataOperation):
    name = "fix_hyphenated_words"
    version = "1.0"
    description = "Fix incorrectly hyphenated words from PDF extraction"
    requires_llm = True

    HYPHEN_PATTERN = re.compile(r"\b[a-z]+-[a-z]+\b", re.IGNORECASE)
    FIELDS = ("report", "analysis", "summary")

    def __init__(self) -> None:
        self.agent = Agent(
            "openai:gpt-4o-mini",
            system_prompt=load_prompt("fix_hyphenated_words"),
            output_type=HyphenationOutput,
        )
        self.user_prompt_template = load_prompt("fix_hyphenated_words_user")

    async def should_run(self, incident: Incident) -> bool:
        for field in self.FIELDS:
            text = getattr(incident, field) or ""
            if self.HYPHEN_PATTERN.search(text):
                return True
        return False

    async def process(self, incident: Incident) -> OperationResult:
        changes: dict[str, dict[str, str]] = {}

        for field in self.FIELDS:
            old_text = getattr(incident, field) or ""
            if not old_text or not self.HYPHEN_PATTERN.search(old_text):
                continue

            prompt = self.user_prompt_template.format(text=old_text[:8000])
            result = await self.agent.run(prompt)
            new_text = result.output.corrected_text.strip()

            if new_text != old_text:
                changes[field] = {"old": old_text, "new": new_text}
                setattr(incident, field, new_text)

        return OperationResult(changes=changes)
