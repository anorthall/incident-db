from __future__ import annotations

from typing import Any

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from django_stubs_ext.db.models import TypedModelMeta


class ACAUserManager(BaseUserManager["ACAUser"]):
    def create_user(
        self, email: str, name: str, password: str | None = None, **kwargs: Any
    ) -> ACAUser:
        if not email:
            raise ValueError("Users must have an email address")

        if not name:
            raise ValueError("Users must have a name")

        user = self.model(
            email=self.normalize_email(email),
            name=name,
            **kwargs,
        )

        if password:
            user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> ACAUser:
        user = self.create_user(*args, **kwargs)

        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class ACAUser(AbstractBaseUser, PermissionsMixin):
    objects = ACAUserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    email = models.EmailField("email address", max_length=255, unique=True)
    name = models.CharField(max_length=50)

    is_editor = models.BooleanField(
        "Editor", default=False, help_text="Can this user edit reports?"
    )
    is_active = models.BooleanField(
        "Enabled user", default=False, help_text="Can this user log in?"
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(default=timezone.now)

    class Meta(TypedModelMeta):
        verbose_name = "user"

    def __str__(self) -> str:
        return self.name

    def get_short_name(self) -> str:
        return self.name.split()[0]

    def get_full_name(self) -> str:
        return self.name

    @property
    def is_staff(self) -> bool:
        return self.is_superuser
