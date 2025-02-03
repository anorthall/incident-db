from django.http import HttpRequest

from core.models import ACAUser


def get_authed_user(
    request: HttpRequest,
) -> ACAUser | None:
    if request.user.is_authenticated and isinstance(request.user, ACAUser):
        return request.user
    return None
