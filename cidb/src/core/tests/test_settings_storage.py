from django.conf import settings


def test_s3_credentials_are_none_when_unset() -> None:
    assert settings.AWS_S3_ACCESS_KEY_ID is None
    assert settings.AWS_S3_SECRET_ACCESS_KEY is None


def test_media_url_uses_custom_domain() -> None:
    assert settings.MEDIA_URL.startswith("https://")
    assert settings.MEDIA_URL.endswith("/media/")


def test_querystring_auth_disabled() -> None:
    assert settings.AWS_QUERYSTRING_AUTH is False
