from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from cidb.src.core.models import ACAUser, Visitor

admin.site.unregister(Group)


@admin.register(ACAUser)
class ACAUserAdmin(BaseUserAdmin[ACAUser], ModelAdmin[ACAUser]):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = (
        "email",
        "name",
        "date_joined",
        "last_seen",
        "is_active",
        "is_staff",
        "is_editor",
        "is_superuser",
    )
    search_fields = ("email", "name")
    ordering = ("email", "last_seen")
    list_filter = ("is_active", "is_staff", "is_superuser", "is_editor")
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
                    "is_staff",
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


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin[Group]):
    pass


@admin.register(Visitor)
class VisitorAdmin(ModelAdmin[Visitor]):
    list_display = ("id", "__str__", "user", "request_count", "last_seen_at", "created_at")
    search_fields = ("emails",)
    list_filter = ("last_seen_at",)
    readonly_fields = (
        "id",
        "user",
        "emails",
        "ip_addresses",
        "request_count",
        "last_seen_at",
        "created_at",
        "updated_at",
    )
