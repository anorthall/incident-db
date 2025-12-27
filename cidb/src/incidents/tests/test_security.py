import json

import pytest
from django.test import Client

from cidb.src.core.models import ACAUser
from cidb.src.incidents.models import ContentReport, Incident


@pytest.mark.django_db
class TestStaffEndpointAuthorization:
    STAFF_URLS = [
        "/api/v1/staff/feedback/",
    ]

    def test_all_require_auth(self, api_client: Client, db: None) -> None:
        for url in self.STAFF_URLS:
            resp = api_client.get(url)
            assert resp.status_code == 401, f"{url} accessible without auth"

    def test_all_require_staff_role(self, api_client: Client, regular_user: ACAUser) -> None:
        api_client.force_login(regular_user)
        for url in self.STAFF_URLS:
            resp = api_client.get(url)
            assert resp.status_code == 401, f"{url} accessible by non-staff user"

    def test_resolve_requires_auth(self, api_client: Client, content_report: ContentReport) -> None:
        resp = api_client.post(
            f"/api/v1/staff/feedback/{content_report.pk}/resolve/",
            json.dumps({"status": "resolved"}),
            content_type="application/json",
        )
        assert resp.status_code == 401

    def test_resolve_requires_staff_role(
        self, api_client: Client, regular_user: ACAUser, content_report: ContentReport
    ) -> None:
        api_client.force_login(regular_user)
        resp = api_client.post(
            f"/api/v1/staff/feedback/{content_report.pk}/resolve/",
            json.dumps({"status": "resolved"}),
            content_type="application/json",
        )
        assert resp.status_code == 401


@pytest.mark.django_db
class TestSearchInputSafety:
    def test_sql_injection_attempt(self, api_client: Client, incident: Incident) -> None:
        resp = api_client.get("/api/v1/incidents/search?q='; DROP TABLE incidents; --")
        assert resp.status_code == 200

    def test_xss_in_search_query(self, api_client: Client, incident: Incident) -> None:
        resp = api_client.get("/api/v1/incidents/search?q=<script>alert('xss')</script>")
        assert resp.status_code == 200

    def test_long_query_handled_gracefully(self, api_client: Client, db: None) -> None:
        resp = api_client.get(f"/api/v1/incidents/search?q={'a' * 400}")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestReportInputSafety:
    def test_html_in_description_stored_as_is(self, api_client: Client, db: None) -> None:
        html = "<script>alert('xss')</script><b>bold</b>"
        resp = api_client.post(
            "/api/v1/reports/",
            json.dumps({"reason": "other", "description": html}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        report = ContentReport.objects.get(pk=resp.json()["id"])
        assert report.description == html
