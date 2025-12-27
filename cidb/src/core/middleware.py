from __future__ import annotations

import time
from collections.abc import Callable
from datetime import timedelta
from uuid import UUID, uuid7

import sentry_sdk
import structlog
from django.db.models import F
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from ipware import get_client_ip

from cidb.conf.logging import request_id_var
from cidb.src.core.models import Visitor

logger = structlog.get_logger(__name__)

VISITOR_COOKIE_NAME = "cidb_visitor"
COOKIE_MAX_AGE = timedelta(days=365 * 2)
API_PATH_PREFIX = "/api/"


class AuthHeaderMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if not request.path.startswith(API_PATH_PREFIX):
            return response

        if hasattr(request, "user") and request.user.is_authenticated:
            user = request.user
            response["CIDB-User-Authenticated"] = "true"
            response["CIDB-User-ID"] = str(user.pk)
            response["CIDB-User-Email"] = user.email
            response["CIDB-User-Name"] = user.name
            response["CIDB-User-Is-Staff"] = "true" if user.is_staff else "false"
            response["CIDB-User-Is-Editor"] = "true" if user.is_editor else "false"
        else:
            response["CIDB-User-Authenticated"] = "false"

        return response


class RequestLoggingMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.headers.get("CIDB-Request-ID") or str(uuid7())
        request_id_var.set(request_id)

        start_time = time.perf_counter()

        logger.info(
            "HTTP request started",
            method=request.method,
            path=request.path,
        )

        response = self.get_response(request)

        duration_ms = (time.perf_counter() - start_time) * 1000
        log_method = logger.warning if response.status_code >= 400 else logger.info
        log_method(
            "HTTP request finished",
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        response["CIDB-Request-ID"] = request_id
        return response

    def process_exception(self, request: HttpRequest, exception: Exception) -> None:
        logger.exception(
            "request_exception",
            method=request.method,
            path=request.path,
        )

        sentry_sdk.capture_exception(exception)


class VisitorTrackingMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not request.path.startswith(API_PATH_PREFIX):
            return self.get_response(request)

        id_str = request.COOKIES.get(VISITOR_COOKIE_NAME)
        id: UUID | None = None
        new_visitor = False

        if id_str:
            try:
                id = UUID(id_str)
            except ValueError:
                id = None

        if id is None:
            id = uuid7()
            new_visitor = True

        ip_address, _ = get_client_ip(request)

        user_id: int | None = None
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = request.user.pk

        response = self.get_response(request)

        self._update_visitor(id, ip_address, user_id, new_visitor)

        response.set_cookie(
            VISITOR_COOKIE_NAME,
            str(id),
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite="Lax",
            secure=not request.META.get("SERVER_NAME", "").startswith("localhost"),
        )

        return response

    def _update_visitor(
        self,
        id: UUID,
        ip_address: str | None,
        user_id: int | None,
        new_visitor: bool,
    ) -> None:
        if new_visitor:
            self._create_visitor(id, ip_address, user_id)

        else:
            update_kwargs: dict[str, object] = {
                "request_count": F("request_count") + 1,
                "last_seen_at": timezone.now(),
            }

            if user_id:
                update_kwargs["user_id"] = user_id

            updated = Visitor.objects.filter(id=id).update(**update_kwargs)

            if updated and ip_address:
                try:
                    visitor = Visitor.objects.only("ip_addresses").get(id=id)
                    visitor.add_ip_address(ip_address)
                except Visitor.DoesNotExist:
                    pass

            elif not updated:
                self._create_visitor(id, ip_address, user_id)

    def _create_visitor(
        self,
        id: UUID,
        ip_address: str | None,
        user_id: int | None,
    ) -> None:
        Visitor.objects.create(
            id=id,
            ip_addresses=[ip_address] if ip_address else [],
            request_count=1,
            last_seen_at=timezone.now(),
            user_id=user_id,
        )
        logger.info("new_visitor_created", visitor_id=str(id))
