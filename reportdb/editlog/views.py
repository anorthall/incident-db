from core.models import ACAUser
from db.mixins import EditorOnly
from django.contrib.auth import get_user_model
from django.db.models import Count, QuerySet
from django.views.generic import ListView, TemplateView

from .models import EditLogEntry

User = get_user_model()


class Index(EditorOnly, ListView):
    model = EditLogEntry
    context_object_name = "logs"
    template_name = "editlog/log_list.html"
    paginate_by = 50

    def get_queryset(self):
        return EditLogEntry.objects.order_by("-timestamp").select_related(
            "user", "incident"
        )


class Scores(EditorOnly, TemplateView):
    template_name = "editlog/scores.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        active_editors: QuerySet[ACAUser] = User.objects.filter(
            is_editor=True, editlogentry__isnull=False
        ).annotate(editlog_score=Count("editlogentry"))

        scores = [(user, getattr(user, "editlog_score", 0)) for user in active_editors]

        scores.sort(key=lambda x: x[1], reverse=True)
        context["scores"] = scores

        return context
