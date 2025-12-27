from typing import Annotated

from ninja import Schema
from pydantic import EmailStr, Field

from cidb.src.incidents.models import ReportReason


class CreateReportRequest(Schema):
    incident_id: int | None = None
    reason: ReportReason
    description: Annotated[str, Field(max_length=10000)] = ""
    email: EmailStr | None = None
    url: str = ""


class ReportResponse(Schema):
    id: int
    status: str
    message: str
