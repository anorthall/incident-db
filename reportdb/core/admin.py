from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserChangeForm, UserCreationForm
from .models import ACAUser


@admin.register(ACAUser)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = (
        "email",
        "name",
        "date_joined",
        "last_seen",
        "is_active",
        "is_editor",
        "is_superuser",
    )
    search_fields = ("email", "name")
    ordering = ("email", "last_seen")
    list_filter = ("is_active", "is_superuser", "is_editor")
    readonly_fields = ("last_login", "last_seen", "date_joined")

    fieldsets = (
        (
            "Account details",
            {
                "fields": (
                    "email",
                    "name",
                    "last_login",
                    "last_seen",
                    "date_joined",
                    "password",
                    "is_active",
                    "is_editor",
                    "is_superuser",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "name",
                    "password1",
                    "password2",
                    "is_active",
                    "is_editor",
                ),
            },
        ),
    )
