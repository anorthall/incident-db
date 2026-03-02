import json

import pytest
from django.test import Client

from cidb.src.core.models import ACAUser
from cidb.src.incidents.models import ContentReport


@pytest.mark.django_db
class TestListFeedback:
    def test_as_staff(self, staff_client: Client, content_report: ContentReport) -> None:
        resp = staff_client.get("/api/v1/staff/feedback/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_as_editor(self, editor_client: Client, content_report: ContentReport) -> None:
        resp = editor_client.get("/api/v1/staff/feedback/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_unauthenticated(self, api_client: Client, db: None) -> None:
        resp = api_client.get("/api/v1/staff/feedback/")
        assert resp.status_code == 401

    def test_non_staff_denied(self, api_client: Client, regular_user: ACAUser) -> None:
        api_client.force_login(regular_user)
        resp = api_client.get("/api/v1/staff/feedback/")
        assert resp.status_code == 401

    def test_filter_by_status(self, staff_client: Client, content_report: ContentReport) -> None:
        resp = staff_client.get("/api/v1/staff/feedback/?status=pending")
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["status"] == "pending" for item in data["items"])

    def test_filter_by_reason(self, staff_client: Client, content_report: ContentReport) -> None:
        resp = staff_client.get("/api/v1/staff/feedback/?reason=inaccurate")
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["reason"] == "inaccurate" for item in data["items"])

    def test_invalid_status_filter(self, staff_client: Client, db: None) -> None:
        resp = staff_client.get("/api/v1/staff/feedback/?status=invalid")
        assert resp.status_code == 400


@pytest.mark.django_db
class TestGetFeedback:
    def test_returns_detail(self, staff_client: Client, content_report: ContentReport) -> None:
        resp = staff_client.get(f"/api/v1/staff/feedback/{content_report.pk}/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["description"] == "The date is wrong."
        assert data["reason"] == "inaccurate"

    def test_unauthenticated(self, api_client: Client, content_report: ContentReport) -> None:
        resp = api_client.get(f"/api/v1/staff/feedback/{content_report.pk}/")
        assert resp.status_code == 401


@pytest.mark.django_db
class TestResolveFeedback:
    def test_resolves(self, staff_client: Client, content_report: ContentReport) -> None:
        resp = staff_client.post(
            f"/api/v1/staff/feedback/{content_report.pk}/resolve/",
            json.dumps({"status": "resolved", "reviewer_notes": "Fixed the date."}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        content_report.refresh_from_db()
        assert content_report.status == "resolved"
        assert content_report.reviewer_notes == "Fixed the date."

    def test_unauthenticated(self, api_client: Client, content_report: ContentReport) -> None:
        resp = api_client.post(
            f"/api/v1/staff/feedback/{content_report.pk}/resolve/",
            json.dumps({"status": "resolved"}),
            content_type="application/json",
        )
        assert resp.status_code == 401

    def test_invalid_status(self, staff_client: Client, content_report: ContentReport) -> None:
        resp = staff_client.post(
            f"/api/v1/staff/feedback/{content_report.pk}/resolve/",
            json.dumps({"status": "invalid_status"}),
            content_type="application/json",
        )
        assert resp.status_code == 400
