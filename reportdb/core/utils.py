from typing import cast

from django.http import HttpRequest

from core.models import ACAUser


def get_authed_user(request: HttpRequest) -> ACAUser | None:
    if request.user.is_authenticated:
        return cast(ACAUser, request.user)
    return None
