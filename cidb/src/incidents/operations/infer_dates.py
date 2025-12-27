from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from cidb.src.core.imprecise_date import DatePrecision, ImpreciseDate

from . import register_operation
from .base import DataOperation, OperationResult, build_references_string, load_prompt

if TYPE_CHECKING:
    from cidb.src.incidents.models import Incident


class DateInferenceOutput(BaseModel):
    inferred_year: int | None = None
    inferred_month: int | None = Field(default=None, ge=1, le=12)
    inferred_day: int | None = Field(default=None, ge=1, le=31)
    confidence: int = Field(ge=0, le=100)
    reasoning: str
    evidence: str


MIN_CONFIDENCE = 90
MIN_YEAR = 1800


@register_operation
class InferDatesOperation(DataOperation):
    name = "infer_dates"
    version = "1.0"
    description = "Infer precise dates from source documents"
    requires_llm = True

    def __init__(self) -> None:
        self.agent = Agent(
            "openai:gpt-4o-mini",
            system_prompt=load_prompt("infer_dates"),
            output_type=DateInferenceOutput,
        )
        self.user_prompt_template = load_prompt("infer_dates_user")

    async def should_run(self, incident: Incident) -> bool:
        date = incident.date
        if date is None or date.precision == DatePrecision.DAY:
            return False
        return bool(incident.source_extract and incident.source_extract.content)

    async def process(self, incident: Incident) -> OperationResult:
        date = incident.date
        source_extract = incident.source_extract
        if date is None or source_extract is None:
            return OperationResult()

        prev_date, next_date = await self._get_adjacent_dates(incident)

        prompt = self.user_prompt_template.format(
            current_date=str(date),
            date_precision=date.precision.name.lower(),
            prev_date=str(prev_date) if prev_date else "Not available",
            next_date=str(next_date) if next_date else "Not available",
            source_content=source_extract.content[:6000],
            report=incident.report[:3000] if incident.report else "N/A",
            references=await build_references_string(incident),
        )

        result = await self.agent.run(prompt)
        output = result.output

        if output.confidence < MIN_CONFIDENCE:
            return OperationResult()

        if not self._validate_inference(incident, output, prev_date, next_date):
            return OperationResult()

        new_date = self._build_new_date(incident, output)
        if new_date is None:
            return OperationResult()

        if new_date.precision.value <= date.precision.value:
            return OperationResult()

        old_date_str = str(date)
        incident.date = new_date

        return OperationResult(
            changes={
                "date": {"old": old_date_str, "new": str(new_date)},
                "date_confidence": {"old": "", "new": str(output.confidence)},
                "date_evidence": {"old": "", "new": output.evidence[:500]},
                "date_reasoning": {"old": "", "new": output.reasoning[:500]},
            },
        )

    async def _get_adjacent_dates(
        self, incident: Incident
    ) -> tuple[ImpreciseDate | None, ImpreciseDate | None]:
        if not incident.source_extract:
            return None, None

        from cidb.src.incidents.models import Incident as IncidentModel

        same_source = (
            IncidentModel.objects.filter(
                source_extract__source_file=incident.source_extract.source_file
            )
            .select_related("source_extract")
            .order_by("source_extract__sequence")
        )

        incidents_list = [inc async for inc in same_source]

        try:
            current_idx = next(i for i, inc in enumerate(incidents_list) if inc.id == incident.id)
        except StopIteration:
            return None, None

        prev_incident = incidents_list[current_idx - 1] if current_idx > 0 else None
        next_incident = (
            incidents_list[current_idx + 1] if current_idx < len(incidents_list) - 1 else None
        )

        prev_date = prev_incident.date if prev_incident else None
        next_date = next_incident.date if next_incident else None

        return prev_date, next_date

    def _validate_inference(
        self,
        incident: Incident,
        output: DateInferenceOutput,
        prev_date: ImpreciseDate | None,
        next_date: ImpreciseDate | None,
    ) -> bool:
        date = incident.date
        if date is None:
            return False

        if output.inferred_year is None:
            return False

        if output.inferred_year < MIN_YEAR:
            return False

        if output.inferred_year > datetime.date.today().year:
            return False

        current_year = date.year
        if output.inferred_year != current_year:
            return False

        if output.inferred_month is not None:
            current_month = date.month
            if current_month is not None and output.inferred_month != current_month:
                return False

        try:
            if output.inferred_day:
                datetime.date(
                    output.inferred_year,
                    output.inferred_month or 1,
                    output.inferred_day,
                )
        except ValueError:
            return False

        inferred = self._build_date_for_comparison(output)
        if inferred is None:
            return False

        if prev_date and inferred < prev_date.date:
            return False
        return not (next_date and inferred > next_date.date)

    def _build_date_for_comparison(self, output: DateInferenceOutput) -> datetime.date | None:
        if output.inferred_year is None:
            return None
        return datetime.date(
            output.inferred_year,
            output.inferred_month or 1,
            output.inferred_day or 1,
        )

    def _build_new_date(
        self, incident: Incident, output: DateInferenceOutput
    ) -> ImpreciseDate | None:
        if output.inferred_year is None:
            return None

        try:
            return ImpreciseDate.from_date(
                year=output.inferred_year,
                month=output.inferred_month,
                day=output.inferred_day,
            )
        except ValueError:
            return None
