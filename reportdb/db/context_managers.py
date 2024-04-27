from db.models import Incident


def task_count(request):
    """Add pending task counts to the context for use in the sidebar."""
    context = {}

    if not request.user.is_authenticated:
        return context

    context["report_text_pending"] = Incident.objects.need_report_text().count()
    context["total_tasks"] = context["report_text_pending"]

    return context
