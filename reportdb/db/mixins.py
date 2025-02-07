from typing import Any, cast

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

from .forms import InjuredCaverForm
from .models import Incident, InjuredCaver


class EditorOnly(UserPassesTestMixin):
    """A mixin to restrict access to views to editors only."""

    request: HttpRequest

    def test_func(self) -> bool:
        if self.request.user.is_authenticated:
            return self.request.user.is_editor
        return False


class InjuredCaverHTMXView(EditorOnly, View):
    """Parent class for views that display injured cavers in HTMX."""

    template_name = "includes/injured_cavers.html"

    def __init__(self) -> None:
        self.incident: Incident | None = None
        self.caver: InjuredCaver | None = None
        super().__init__()

    def dispatch(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        if self.kwargs.get("caver_pk"):
            self.caver = get_object_or_404(InjuredCaver, pk=self.kwargs["caver_pk"])
            assert isinstance(self.caver, InjuredCaver)

            self.incident = self.caver.incident
            assert isinstance(self.incident, Incident)
        else:
            self.incident = get_object_or_404(Incident, pk=self.kwargs["pk"])
            assert isinstance(self.incident, Incident)

        return cast(HttpResponse, super().dispatch(request, *args, **kwargs))

    def render_to_response(self) -> HttpResponse:
        context = {
            "incident": self.incident,
            "injured_caver_add_form": InjuredCaverForm(self.incident),
            "injured_cavers_htmx": True,
            "allow_editing_injured_cavers": True,
        }
        return render(self.request, self.template_name, context)
