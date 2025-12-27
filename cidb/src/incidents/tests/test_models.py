import pytest

from cidb.src.incidents.models import (
    ContentReport,
    Incident,
    ReportReason,
    SearchClick,
    SearchQuery,
)


@pytest.mark.django_db
class TestSearchQuery:
    def test_record_search_creates(self) -> None:
        SearchQuery.record_search("cave rescue")
        assert SearchQuery.objects.filter(query="cave rescue").exists()

    def test_record_search_increments(self) -> None:
        SearchQuery.record_search("cave rescue")
        SearchQuery.record_search("cave rescue")
        sq = SearchQuery.objects.get(query="cave rescue")
        assert sq.query_count == 2

    def test_normalizes_query(self) -> None:
        SearchQuery.record_search("  Cave RESCUE  ")
        assert SearchQuery.objects.filter(query="cave rescue").exists()
        assert not SearchQuery.objects.filter(query="  Cave RESCUE  ").exists()


@pytest.mark.django_db
class TestSearchClick:
    def test_record_click(self, incident: Incident) -> None:
        SearchClick.record_click(query="Cave Test", incident_id=incident.pk, position=3)
        click = SearchClick.objects.first()
        assert click is not None
        assert click.query == "cave test"
        assert click.position == 3
        assert click.incident_id == incident.pk


@pytest.mark.django_db
class TestContentReport:
    def test_str_with_incident(self, content_report: ContentReport) -> None:
        assert "inaccurate" in str(content_report)

    def test_str_without_incident(self, db: None) -> None:
        report = ContentReport.objects.create(
            reason=ReportReason.OTHER,
            description="General feedback",
        )
        assert "General feedback" in str(report)

    def test_default_status(self, db: None) -> None:
        report = ContentReport.objects.create(
            reason=ReportReason.TYPO,
            description="Test",
        )
        assert report.status == "pending"
