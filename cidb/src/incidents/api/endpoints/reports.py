import contextlib
from uuid import UUID

from django.http import HttpRequest
from ipware import get_client_ip
from ninja import Router

from cidb.src.core.middleware import VISITOR_COOKIE_NAME
from cidb.src.core.models import Visitor
from cidb.src.incidents.api.schemas.report import CreateReportRequest, ReportResponse
from cidb.src.incidents.models import ContentReport, Incident

router = Router()


def get_or_create_visitor(request: HttpRequest, email: str = "") -> Visitor:
    id_str = request.COOKIES.get(VISITOR_COOKIE_NAME)
    ip_address, _ = get_client_ip(request)
    visitor: Visitor | None = None

    if id_str:
        with contextlib.suppress(ValueError, Visitor.DoesNotExist):
            visitor = Visitor.objects.get(id=UUID(id_str))

    if visitor is None:
        visitor = Visitor.objects.create(
            emails=[email] if email else [],
            ip_addresses=[ip_address] if ip_address else [],
        )

    else:
        if ip_address:
            visitor.add_ip_address(ip_address)
        if email:
            visitor.add_email(email)

    return visitor


@router.post("/", response=ReportResponse)
def create_report(request: HttpRequest, payload: CreateReportRequest) -> ReportResponse:
    if payload.incident_id:
        incident = Incident.objects.filter(pk=payload.incident_id).only("pk").first()

    else:
        incident = None

    visitor = get_or_create_visitor(request, payload.email or "")

    report = ContentReport.objects.create(
        incident=incident,
        reporter=visitor,
        reason=payload.reason,
        description=payload.description,
        url=payload.url,
    )

    return ReportResponse(
        id=report.id,
        status="pending",
        message="Thank you for your feedback.",
    )
