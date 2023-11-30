from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


class ACAUserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **kwargs):
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

    def create_superuser(self, *args, **kwargs):
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

    class Meta:
        verbose_name = "user"

    def __str__(self):
        return self.name

    def get_short_name(self):
        return self.name.split()[0]

    def get_full_name(self):
        return self.name

    @property
    def is_staff(self):
        return self.is_superuser
