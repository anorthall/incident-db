from collections.abc import Awaitable, Callable

from django.http.request import HttpRequest
from django.http.response import HttpResponseBase
from django.utils import timezone


class LastSeenMiddleware:
    def __init__(
        self,
        get_response: Callable[[HttpRequest], HttpResponseBase | Awaitable[HttpResponseBase]],
    ) -> None:
        self.get_response = get_response

    def __call__(
        self,
        request: HttpRequest,
    ) -> HttpResponseBase | Awaitable[HttpResponseBase]:
        if request.user.is_authenticated:
            request.user.last_seen = timezone.now()
            request.user.save(update_fields=["last_seen"])

        return self.get_response(request)
