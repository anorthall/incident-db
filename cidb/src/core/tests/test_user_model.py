import pytest

from cidb.src.core.models import ACAUser


@pytest.mark.django_db
class TestACAUserManager:
    def test_create_user_requires_email(self) -> None:
        with pytest.raises(ValueError, match="email"):
            ACAUser.objects.create_user(name="Test", password="test123")

    def test_create_user_requires_name(self) -> None:
        with pytest.raises(ValueError, match="name"):
            ACAUser.objects.create_user(email="test@example.com", password="test123")

    def test_create_user_normalizes_email(self) -> None:
        user = ACAUser.objects.create_user(
            email="Test@EXAMPLE.COM", name="Test", password="test123"
        )
        assert user.email == "Test@example.com"

    def test_user_str(self) -> None:
        user = ACAUser(name="Alice Smith", email="alice@example.com")
        assert str(user) == "Alice Smith"

    def test_get_short_name(self) -> None:
        user = ACAUser(name="Alice Smith", email="alice@example.com")
        assert user.get_short_name() == "Alice"
