import pytest
from django.test import Client
from pytest_django.fixtures import SettingsWrapper


@pytest.mark.parametrize(
    "path",
    ["/nonexistent-xyz", "/core/nope", "/api/v1/nope", "/api/v1/auth/nope"],
)
@pytest.mark.django_db
def test_unknown_path_returns_404(settings: SettingsWrapper, path: str) -> None:
    settings.DEBUG = False
    settings.ALLOWED_HOSTS = ["testserver"]

    response = Client(raise_request_exception=False).get(path)

    assert response.status_code == 404


@pytest.mark.django_db
def test_non_integer_incident_id_returns_422(settings: SettingsWrapper) -> None:
    settings.DEBUG = False
    settings.ALLOWED_HOSTS = ["testserver"]

    response = Client(raise_request_exception=False).get("/api/v1/incidents/not-an-int")

    assert response.status_code == 422
