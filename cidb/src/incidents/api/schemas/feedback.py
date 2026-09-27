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


def _incident_of(report: ContentReport) -> IncidentMinimalSchema | None:
    if not report.incident:
        return None
    return IncidentMinimalSchema(
        id=report.incident.id,
        title=report.incident.title,
    )


def _reporter_of(report: ContentReport) -> ReporterSchema | None:
    if not report.reporter:
        return None
    email = report.reporter.emails[0] if report.reporter.emails else None
    return ReporterSchema(
        id=str(report.reporter.id),
        email=email,
    )


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
    def from_report(cls, report: ContentReport) -> FeedbackListItemSchema:
        return cls(
            id=report.id,
            incident=_incident_of(report),
            url=report.url,
            reason=report.reason,
            reason_display=ReportReason(report.reason).label,
            description=report.description,
            status=report.status,
            status_display=ReportStatus(report.status).label,
            reporter=_reporter_of(report),
            created_at=report.created_at,
            updated_at=report.updated_at,
        )


class FeedbackDetailSchema(FeedbackListItemSchema):
    reviewer_notes: str

    @classmethod
    def from_report(cls, report: ContentReport) -> FeedbackDetailSchema:
        return cls(
            id=report.id,
            incident=_incident_of(report),
            url=report.url,
            reason=report.reason,
            reason_display=ReportReason(report.reason).label,
            description=report.description,
            status=report.status,
            status_display=ReportStatus(report.status).label,
            reporter=_reporter_of(report),
            created_at=report.created_at,
            updated_at=report.updated_at,
            reviewer_notes=report.reviewer_notes,
        )


class ResolveRequest(Schema):
    status: str
    reviewer_notes: str = ""


class ResolveResponse(Schema):
    id: int
    status: str
    message: str
