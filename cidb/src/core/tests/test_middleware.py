import pytest
from django.test import Client

from cidb.src.core.models import ACAUser, Visitor


@pytest.mark.django_db
class TestAuthHeaderMiddleware:
    def test_headers_set_for_authenticated_user(
        self, staff_client: Client, staff_user: ACAUser
    ) -> None:
        resp = staff_client.get("/api/v1/auth/me")
        assert resp["CIDB-User-Authenticated"] == "true"
        assert resp["CIDB-User-Email"] == "staff@example.com"
        assert resp["CIDB-User-Name"] == "Staff User"
        assert resp["CIDB-User-Is-Staff"] == "true"

    def test_headers_unauthenticated(self, api_client: Client) -> None:
        resp = api_client.get("/api/v1/auth/csrf")
        assert resp["CIDB-User-Authenticated"] == "false"

    def test_no_auth_headers_on_non_api_paths(
        self, staff_client: Client, staff_user: ACAUser
    ) -> None:
        resp = staff_client.get("/core/healthcheck/")
        assert "CIDB-User-Authenticated" not in resp


@pytest.mark.django_db
class TestRequestLoggingMiddleware:
    def test_adds_request_id(self, api_client: Client) -> None:
        resp = api_client.get("/api/v1/auth/csrf")
        assert "CIDB-Request-ID" in resp
        assert len(resp["CIDB-Request-ID"]) > 0

    def test_echoes_provided_request_id(self, api_client: Client) -> None:
        resp = api_client.get(
            "/api/v1/auth/csrf", headers={"CIDB-Request-ID": "custom-request-id-123"}
        )
        assert resp["CIDB-Request-ID"] == "custom-request-id-123"


@pytest.mark.django_db
class TestVisitorTrackingMiddleware:
    def test_sets_visitor_cookie_on_first_visit(self, api_client: Client) -> None:
        resp = api_client.get("/api/v1/auth/csrf")
        assert "cidb_visitor" in resp.cookies
        assert Visitor.objects.count() == 1

    def test_reuses_existing_visitor_cookie(self, api_client: Client) -> None:
        resp1 = api_client.get("/api/v1/auth/csrf")
        visitor_id = resp1.cookies["cidb_visitor"].value

        resp2 = api_client.get("/api/v1/auth/csrf")
        assert resp2.cookies.get("cidb_visitor") is not None
        assert Visitor.objects.count() == 1

        visitor = Visitor.objects.first()
        assert visitor is not None
        assert str(visitor.id) == visitor_id
        assert visitor.request_count == 2

    def test_invalid_cookie_creates_new_visitor(self, api_client: Client) -> None:
        api_client.cookies["cidb_visitor"] = "not-a-uuid"
        resp = api_client.get("/api/v1/auth/csrf")
        assert resp.status_code == 200
        assert Visitor.objects.count() == 1
