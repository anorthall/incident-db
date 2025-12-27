import pytest
from django.test import Client

from cidb.src.core.models import ACAUser
from cidb.src.incidents.models import (
    Cave,
    ContentReport,
    Document,
    Incident,
    Location,
    Publication,
    ReportReason,
    Tag,
)


@pytest.fixture
def staff_user(db: None) -> ACAUser:
    user = ACAUser(email="staff@example.com", name="Staff User", is_staff=True, is_active=True)
    user.set_password("testpass123")
    user.save()
    return user


@pytest.fixture
def editor_user(db: None) -> ACAUser:
    user = ACAUser(email="editor@example.com", name="Editor User", is_editor=True, is_active=True)
    user.set_password("testpass123")
    user.save()
    return user


@pytest.fixture
def regular_user(db: None) -> ACAUser:
    user = ACAUser(email="user@example.com", name="Regular User", is_active=True)
    user.set_password("testpass123")
    user.save()
    return user


@pytest.fixture
def inactive_user(db: None) -> ACAUser:
    user = ACAUser(email="inactive@example.com", name="Inactive User", is_active=False)
    user.set_password("testpass123")
    user.save()
    return user


@pytest.fixture
def api_client() -> Client:
    return Client(enforce_csrf_checks=False)


@pytest.fixture
def csrf_client() -> Client:
    return Client(enforce_csrf_checks=True)


@pytest.fixture
def staff_client(staff_user: ACAUser) -> Client:
    client = Client(enforce_csrf_checks=False)
    client.force_login(staff_user)
    return client


@pytest.fixture
def editor_client(editor_user: ACAUser) -> Client:
    client = Client(enforce_csrf_checks=False)
    client.force_login(editor_user)
    return client


@pytest.fixture
def location(db: None) -> Location:
    return Location.objects.create(
        country_text="United States",
        state_text="Virginia",
        region_text="Appalachian",
    )


@pytest.fixture
def cave(location: Location) -> Cave:
    return Cave.objects.create(name="Test Cave", location=location)


@pytest.fixture
def document(db: None) -> Document:
    return Document.objects.create(text="Test document content")


@pytest.fixture
def publication(document: Document) -> Publication:
    return Publication.objects.create(
        title="Test Publication",
        content=document,
        published_at="2024",
    )


@pytest.fixture
def incident(cave: Cave, publication: Publication) -> Incident:
    return Incident.objects.create(
        title="Test Cave Incident",
        cave=cave,
        origin=publication,
        date="2024-06-15",
        report="A caver was injured during exploration.",
        analysis="Insufficient equipment preparation.",
        summary="Cave exploration accident.",
    )


@pytest.fixture
def tag(db: None) -> Tag:
    return Tag.objects.create(name="rescue")


@pytest.fixture
def incident_with_tags(incident: Incident, tag: Tag) -> Incident:
    incident.tags.add(tag)
    return incident


@pytest.fixture
def content_report(incident: Incident) -> ContentReport:
    return ContentReport.objects.create(
        incident=incident,
        reason=ReportReason.INACCURATE,
        description="The date is wrong.",
    )
