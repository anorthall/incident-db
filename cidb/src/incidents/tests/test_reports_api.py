import json

import pytest
from django.test import Client

from cidb.src.core.models import Visitor
from cidb.src.incidents.models import ContentReport, Incident


@pytest.mark.django_db
class TestCreateReport:
    def test_with_incident(self, api_client: Client, incident: Incident) -> None:
        resp = api_client.post(
            "/api/v1/reports/",
            json.dumps(
                {
                    "incident_id": incident.pk,
                    "reason": "inaccurate",
                    "description": "The date is wrong",
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending"
        report = ContentReport.objects.get(pk=data["id"])
        assert report.incident_id == incident.pk

    def test_general_report_without_incident(self, api_client: Client, db: None) -> None:
        resp = api_client.post(
            "/api/v1/reports/",
            json.dumps(
                {
                    "reason": "other",
                    "description": "General feedback about the site",
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 200
        report = ContentReport.objects.get(pk=resp.json()["id"])
        assert report.incident is None

    def test_creates_visitor(self, api_client: Client, db: None) -> None:
        assert Visitor.objects.count() == 0
        api_client.post(
            "/api/v1/reports/",
            json.dumps(
                {
                    "reason": "typo",
                    "description": "Typo in report",
                    "email": "reporter@example.com",
                }
            ),
            content_type="application/json",
        )
        assert Visitor.objects.count() >= 1

    def test_invalid_reason(self, api_client: Client, db: None) -> None:
        resp = api_client.post(
            "/api/v1/reports/",
            json.dumps(
                {
                    "reason": "nonexistent_reason",
                    "description": "Test",
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 422

    def test_long_description(self, api_client: Client, db: None) -> None:
        resp = api_client.post(
            "/api/v1/reports/",
            json.dumps(
                {
                    "reason": "other",
                    "description": "x" * 10000,
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 200
