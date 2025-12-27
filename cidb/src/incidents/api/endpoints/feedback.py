from typing import Annotated

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Query, Router
from ninja.errors import HttpError

from cidb.src.incidents.api.schemas.common import PaginatedResponse
from cidb.src.incidents.api.schemas.feedback import (
    FeedbackDetailSchema,
    FeedbackListItemSchema,
    FeedbackSortBy,
    ResolveRequest,
    ResolveResponse,
)
from cidb.src.incidents.models.report import ContentReport, ReportReason, ReportStatus

router = Router()


@router.get("/", response=PaginatedResponse[FeedbackListItemSchema])
def list_feedback(
    request: HttpRequest,
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    reason: Annotated[str | None, Query(description="Filter by reason")] = None,
    sort_by: Annotated[FeedbackSortBy, Query(description="Sort field")] = FeedbackSortBy.CREATED_AT,
    sort_order: Annotated[str, Query(description="Sort order", pattern="^(asc|desc)$")] = "desc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[FeedbackListItemSchema]:
    queryset = ContentReport.objects.select_related("incident", "reporter")

    if status:
        if status not in ReportStatus.values:
            raise HttpError(400, f"Invalid status: {status}")
        queryset = queryset.filter(status=status)

    if reason:
        if reason not in ReportReason.values:
            raise HttpError(400, f"Invalid reason: {reason}")
        queryset = queryset.filter(reason=reason)

    order_prefix = "" if sort_order == "asc" else "-"
    queryset = queryset.order_by(f"{order_prefix}{sort_by.value}")

    total = queryset.count()
    offset = (page - 1) * page_size
    reports = queryset[offset : offset + page_size]

    items = [FeedbackListItemSchema.from_report(r) for r in reports]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.get("/{feedback_id}/", response=FeedbackDetailSchema)
def get_feedback(request: HttpRequest, feedback_id: int) -> FeedbackDetailSchema:
    report = get_object_or_404(
        ContentReport.objects.select_related("incident", "reporter"),
        pk=feedback_id,
    )
    return FeedbackDetailSchema.from_report(report)


@router.post("/{feedback_id}/resolve/", response=ResolveResponse)
def resolve_feedback(
    request: HttpRequest, feedback_id: int, payload: ResolveRequest
) -> ResolveResponse:
    if payload.status not in ReportStatus.values:
        raise HttpError(400, f"Invalid status: {payload.status}")

    report = get_object_or_404(ContentReport, pk=feedback_id)
    report.status = payload.status
    report.reviewer_notes = payload.reviewer_notes
    report.save(update_fields=["status", "reviewer_notes", "updated_at"])

    status_label = ReportStatus(payload.status).label
    return ResolveResponse(
        id=report.id,
        status=report.status,
        message=f"Feedback marked as {status_label}",
    )
