from datetime import datetime
from enum import StrEnum

from ninja import Schema

from cidb.src.incidents.models.report import ContentReport, ReportReason, ReportStatus


class FeedbackSortBy(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    STATUS = "status"
    REASON = "reason"


class ReporterSchema(Schema):
    id: str
    email: str | None


class IncidentMinimalSchema(Schema):
    id: int
    title: str


class FeedbackListItemSchema(Schema):
    id: int
    incident: IncidentMinimalSchema | None
    url: str
    reason: str
    reason_display: str
    description: str
    status: str
    status_display: str
    reporter: ReporterSchema | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def _base_kwargs(cls, report: ContentReport) -> dict[str, object]:
        incident = None
        if report.incident:
            incident = IncidentMinimalSchema(
                id=report.incident.id,
                title=report.incident.title,
            )

        reporter = None
        if report.reporter:
            email = report.reporter.emails[0] if report.reporter.emails else None
            reporter = ReporterSchema(
                id=str(report.reporter.id),
                email=email,
            )

        return {
            "id": report.id,
            "incident": incident,
            "url": report.url,
            "reason": report.reason,
            "reason_display": ReportReason(report.reason).label,
            "description": report.description,
            "status": report.status,
            "status_display": ReportStatus(report.status).label,
            "reporter": reporter,
            "created_at": report.created_at,
            "updated_at": report.updated_at,
        }

    @classmethod
    def from_report(cls, report: ContentReport) -> FeedbackListItemSchema:
        return cls(**cls._base_kwargs(report))


class FeedbackDetailSchema(FeedbackListItemSchema):
    reviewer_notes: str

    @classmethod
    def from_report(cls, report: ContentReport) -> FeedbackDetailSchema:
        return cls(**cls._base_kwargs(report), reviewer_notes=report.reviewer_notes)


class ResolveRequest(Schema):
    status: str
    reviewer_notes: str = ""


class ResolveResponse(Schema):
    id: int
    status: str
    message: str
