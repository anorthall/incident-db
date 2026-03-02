import structlog
from django.http import HttpRequest, HttpResponse
from ninja import NinjaAPI
from ninja.errors import HttpError

from cidb.src.core.api.auth import router as auth_router
from cidb.src.incidents.api.endpoints.incidents import router as incidents_router
from cidb.src.incidents.api.endpoints.reports import router as reports_router
from cidb.src.incidents.api.endpoints.staff import router as staff_router

logger = structlog.get_logger(__name__)

api = NinjaAPI(
    title="Caving Incident Database API",
    version="1.0.0",
    urls_namespace="incidents-api",
)


@api.exception_handler(HttpError)
def handle_http_error(request: HttpRequest, exc: HttpError) -> HttpResponse:
    logger.warning(
        "api_http_error",
        status_code=exc.status_code,
        message=str(exc.message),
        path=request.path,
    )
    return api.create_response(request, {"detail": exc.message}, status=exc.status_code)


@api.exception_handler(Exception)
def handle_unexpected_error(request: HttpRequest, exc: Exception) -> HttpResponse:
    logger.exception("api_unexpected_error", path=request.path)
    try:
        import sentry_sdk

        sentry_sdk.capture_exception(exc)
    except ImportError:
        pass
    return api.create_response(request, {"detail": "An unexpected error occurred"}, status=500)


api.add_router("/auth", auth_router, tags=["auth"])
api.add_router("/incidents", incidents_router, tags=["incidents"])
api.add_router("/reports", reports_router, tags=["reports"])
api.add_router("/staff", staff_router, tags=["staff"])
