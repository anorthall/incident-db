from typing import Any, ClassVar

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone
from django_stubs_ext.db.models import TypedModelMeta


class ACAUserManager(UserManager["ACAUser"]):
    def create_user(self, *args: Any, **kwargs: Any) -> ACAUser:
        if not (email := kwargs.pop("email", None)):
            raise ValueError("Users must have an email address")

        if not (name := kwargs.pop("name", None)):
            raise ValueError("Users must have a name")

        password = kwargs.pop("password", None)

        user = self.model(
            email=self.normalize_email(email),
            name=name,
            **kwargs,
        )

        if password:
            user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(self, *args: Any, **kwargs: Any) -> ACAUser:
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)
        kwargs.setdefault("is_active", True)

        if not kwargs.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")

        if not kwargs.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(*args, **kwargs)


class ACAUser(AbstractUser):
    objects: ClassVar[ACAUserManager] = ACAUserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    email = models.EmailField(
        "email address",
        max_length=255,
        unique=True,
    )

    name = models.CharField(
        max_length=50,
    )

    is_editor = models.BooleanField(
        "Editor",
        default=False,
        help_text="Can this user edit reports?",
    )

    is_active = models.BooleanField(
        "Enabled user",
        default=False,
        help_text="Can this user log in?",
    )

    is_staff = models.BooleanField(
        "Staff status",
        default=False,
        help_text="Designates whether the user can log into the admin site.",
    )

    date_joined = models.DateTimeField(
        auto_now_add=True,
    )

    last_seen = models.DateTimeField(
        default=timezone.now,
    )

    class Meta(TypedModelMeta):
        verbose_name = "user"

    def __str__(self) -> str:
        return self.name

    def get_short_name(self) -> str:
        return self.name.split()[0]

    def get_full_name(self) -> str:
        return self.name
