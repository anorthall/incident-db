from django.http import HttpRequest, HttpResponse
from django.views.generic import View


class Healthcheck(View):
    def get(
        self,
        request: HttpRequest,
    ) -> HttpResponse:
        return HttpResponse("OK")
