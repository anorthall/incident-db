import json

import pytest
from django.test import Client

from cidb.src.incidents.models import Incident, SearchClick, SearchQuery


@pytest.mark.django_db
class TestSearchIncidents:
    def test_no_query_returns_all(self, api_client: Client, incident: Incident) -> None:
        resp = api_client.get("/api/v1/incidents/search")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_pagination(self, api_client: Client, incident: Incident) -> None:
        resp = api_client.get("/api/v1/incidents/search?page=1&page_size=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 1

    def test_invalid_page_size_too_large(self, api_client: Client, db: None) -> None:
        resp = api_client.get("/api/v1/incidents/search?page_size=200")
        assert resp.status_code == 422

    def test_invalid_page_size_zero(self, api_client: Client, db: None) -> None:
        resp = api_client.get("/api/v1/incidents/search?page_size=0")
        assert resp.status_code == 422

    def test_sort_by_date(self, api_client: Client, incident: Incident) -> None:
        resp = api_client.get("/api/v1/incidents/search?sort_by=date&sort_order=desc")
        assert resp.status_code == 200

    def test_sort_by_popularity(self, api_client: Client, incident: Incident) -> None:
        resp = api_client.get("/api/v1/incidents/search?sort_by=popularity")
        assert resp.status_code == 200

    def test_search_records_query(self, api_client: Client, incident: Incident) -> None:
        api_client.get("/api/v1/incidents/search?q=cave")
        assert SearchQuery.objects.filter(query="cave").exists()

    def test_empty_results(self, api_client: Client, db: None) -> None:
        resp = api_client.get("/api/v1/incidents/search")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []


@pytest.mark.django_db
class TestGetIncident:
    def test_returns_detail(self, api_client: Client, incident: Incident) -> None:
        resp = api_client.get(f"/api/v1/incidents/{incident.pk}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Test Cave Incident"
        assert data["cave"]["name"] == "Test Cave"

    def test_increments_view_count(self, api_client: Client, incident: Incident) -> None:
        original = incident.view_count
        api_client.get(f"/api/v1/incidents/{incident.pk}")
        incident.refresh_from_db()
        assert incident.view_count == original + 1

    def test_nonexistent_returns_404(self, api_client: Client, db: None) -> None:
        resp = api_client.get("/api/v1/incidents/999999")
        assert resp.status_code == 404


@pytest.mark.django_db
class TestSuggestions:
    def test_returns_matching(self, api_client: Client, incident: Incident) -> None:
        SearchQuery.objects.create(query="cave rescue", query_count=5)
        SearchQuery.objects.create(query="cave diving", query_count=3)
        resp = api_client.get("/api/v1/incidents/suggestions?q=cave")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["suggestions"]) >= 1
        assert "cave rescue" in data["suggestions"]

    def test_min_length_enforced(self, api_client: Client, db: None) -> None:
        resp = api_client.get("/api/v1/incidents/suggestions?q=c")
        assert resp.status_code == 422


@pytest.mark.django_db
class TestDidYouMean:
    def test_returns_similar(self, api_client: Client, db: None) -> None:
        SearchQuery.objects.create(query="cave rescue", query_count=10)
        resp = api_client.get("/api/v1/incidents/did-you-mean?q=cave%20rescu")
        assert resp.status_code == 200
        data = resp.json()
        assert data["suggestion"] == "cave rescue"
        assert data["similarity"] is not None

    def test_no_match(self, api_client: Client, db: None) -> None:
        resp = api_client.get("/api/v1/incidents/did-you-mean?q=xyzxyzxyz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["suggestion"] is None


@pytest.mark.django_db
class TestClickTracking:
    def test_records_click(self, api_client: Client, incident: Incident) -> None:
        resp = api_client.post(
            "/api/v1/incidents/click",
            json.dumps({"query": "test", "incident_id": incident.pk, "position": 1}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert SearchClick.objects.count() == 1
        click = SearchClick.objects.first()
        assert click is not None
        assert click.query == "test"
        assert click.position == 1

    def test_invalid_incident(self, api_client: Client, db: None) -> None:
        resp = api_client.post(
            "/api/v1/incidents/click",
            json.dumps({"query": "test", "incident_id": 999999, "position": 1}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is False
        assert SearchClick.objects.count() == 0
