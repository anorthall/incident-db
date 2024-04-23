from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, render
from django.views import View
from reversion.views import RevisionMixin

from .forms import InjuredCaverForm
from .models import Incident, InjuredCaver


class EditorOnly(UserPassesTestMixin):
    """A mixin to restrict access to views to editors only."""

    def test_func(self):
        if self.request.user.is_authenticated:
            return self.request.user.is_editor
        return False


class ApprovalMixin(EditorOnly):
    """A mixin for views relating to incident approval."""

    def test_func(self):
        """Only allow editors to access, and only if the incident is unapproved."""
        if super().test_func():
            return not self.get_object().approved
        return False


class InjuredCaverHTMXView(EditorOnly, RevisionMixin, View):
    """Parent class for views that display injured cavers in HTMX."""

    template_name = "includes/injured_cavers.html"

    def __init__(self):
        self.incident = None
        self.caver = None
        super().__init__()

    def dispatch(self, request, *args, **kwargs):
        if self.kwargs.get("caver_pk"):
            self.caver = get_object_or_404(InjuredCaver, pk=self.kwargs["caver_pk"])
            self.incident = self.caver.incident
        else:
            self.incident = get_object_or_404(Incident, pk=self.kwargs["pk"])

        if self.incident.approved:
            messages.error(
                request,
                "This incident has already been approved and can no longer be edited.",
            )
            return self.render_to_response()
        return super().dispatch(request, *args, **kwargs)

    def render_to_response(self):
        context = {
            "incident": self.incident,
            "injured_caver_add_form": InjuredCaverForm(self.incident),
            "injured_cavers_htmx": True,
            "allow_editing_injured_cavers": True,
        }
        return render(self.request, self.template_name, context)
