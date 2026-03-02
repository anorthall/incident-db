import json

import pytest
from django.test import Client

from cidb.src.core.models import ACAUser


@pytest.mark.django_db
class TestLogin:
    def test_success(self, api_client: Client, staff_user: ACAUser) -> None:
        resp = api_client.post(
            "/api/v1/auth/login",
            json.dumps(
                {
                    "email": "staff@example.com",
                    "password": "testpass123",  # pragma: allowlist secret
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["email"] == "staff@example.com"
        assert data["user"]["is_staff"] is True
        assert data["message"] == "Login successful"

    def test_wrong_password(self, api_client: Client, staff_user: ACAUser) -> None:
        resp = api_client.post(
            "/api/v1/auth/login",
            json.dumps(
                {
                    "email": "staff@example.com",
                    "password": "wrong",  # pragma: allowlist secret
                },
            ),
            content_type="application/json",
        )
        assert resp.status_code == 401

    def test_inactive_user(self, api_client: Client, inactive_user: ACAUser) -> None:
        resp = api_client.post(
            "/api/v1/auth/login",
            json.dumps(
                {
                    "email": "inactive@example.com",
                    "password": "testpass123",  # pragma: allowlist secret
                },
            ),
            content_type="application/json",
        )
        assert resp.status_code == 401

    def test_non_staff_user(self, api_client: Client, regular_user: ACAUser) -> None:
        resp = api_client.post(
            "/api/v1/auth/login",
            json.dumps(
                {
                    "email": "nobody@example.com",
                    "password": "testpass123",  # pragma: allowlist secret
                },
            ),
            content_type="application/json",
        )
        assert resp.status_code == 401

    def test_nonexistent_email(self, api_client: Client, db: None) -> None:
        resp = api_client.post(
            "/api/v1/auth/login",
            json.dumps(
                {
                    "email": "nobody@example.com",
                    "password": "testpass123",  # pragma: allowlist secret
                },
            ),
            content_type="application/json",
        )
        assert resp.status_code == 401


@pytest.mark.django_db
class TestLogout:
    def test_logout_clears_session(self, staff_client: Client, staff_user: ACAUser) -> None:
        resp = staff_client.post("/api/v1/auth/logout", content_type="application/json")
        assert resp.status_code == 200

        resp = staff_client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_logout_unauthenticated(self, api_client: Client, db: None) -> None:
        resp = api_client.post("/api/v1/auth/logout", content_type="application/json")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestGetMe:
    def test_authenticated(self, staff_client: Client, staff_user: ACAUser) -> None:
        resp = staff_client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "staff@example.com"
        assert data["name"] == "Staff User"
        assert data["is_staff"] is True

    def test_unauthenticated(self, api_client: Client, db: None) -> None:
        resp = api_client.get("/api/v1/auth/me")
        assert resp.status_code == 401


@pytest.mark.django_db
class TestCSRF:
    def test_csrf_token_endpoint(self, api_client: Client, db: None) -> None:
        resp = api_client.get("/api/v1/auth/csrf")
        assert resp.status_code == 200
        data = resp.json()
        assert "csrf_token" in data
        assert len(data["csrf_token"]) > 0
