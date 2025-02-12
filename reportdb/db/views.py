from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.models import ACAUser
from core.utils import get_authed_user
from django.contrib import messages
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.http.response import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView, TemplateView, UpdateView, View
from editlog.models import EditLogEntry

from .forms import (
    AnalysisTextForm,
    ApproveFlagsForm,
    ApproveIncidentDateForm,
    ApproveMetadataForm,
    ApproveReportTextForm,
    IncidentForm,
    InjuredCaverForm,
    ReportTextForm,
)
from .mixins import EditorOnly, InjuredCaverHTMXView
from .models import Incident, InjuredCaver, Publication
from .services import highlight_text_from_incident, similarity

# 'Flags' (boolean fields) that can be used to filter incidents
# Mapping of BooleanField names to human-readable labels
ALLOWED_QUERY_FLAGS: dict[str, str] = {
    "fatality": "fatality",
    "injury": "injury",
    "rescue_over_24_hours": "long rescue",
    "self_rescue": "self rescue",
    "vertical": "vertical",
}


class About(TemplateView):
    template_name = "about.html"


class Help(TemplateView):
    template_name = "help.html"


@dataclass
class IncidentByYear:
    name: str
    slug: str
    count: int


class Index(TemplateView):
    template_name = "index.html"

    def count_by_year(
        self,
        year: int,
        incidents: dict[str, IncidentByYear],
    ) -> None:
        year_str: str = str(year)
        if not year_str:
            return

        if year_str not in incidents:
            incidents[year_str] = IncidentByYear(
                name=year_str,
                slug=year_str,
                count=1,
            )
        else:
            incidents[year_str].count += 1

    def count_by_category(
        self,
        category: str,
        incidents: dict[str, IncidentByYear],
    ) -> None:
        try:
            category_label: str = str(Incident.Category(category).label)
        except ValueError:
            category_label = "Uncategorised"

        if category_label not in incidents:
            incidents[category_label] = IncidentByYear(
                name=category_label,
                slug=category_label.lower().replace(" ", "-"),
                count=1,
            )
        else:
            incidents[category_label].count += 1

    def count_by_flag(
        self,
        incident: dict[str, str],
        incidents: dict[str, IncidentByYear],
    ) -> None:
        for flag in ALLOWED_QUERY_FLAGS:
            if incident.get(flag, False):
                flag_label: str = ALLOWED_QUERY_FLAGS[flag]

                if flag_label not in incidents:
                    incidents[flag_label] = IncidentByYear(
                        name=flag_label,
                        slug=flag.replace("_", "-"),
                        count=1,
                    )
                else:
                    incidents[flag_label].count += 1

    def get_context_data(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        # Build context for the incident list by year
        incidents = Incident.objects.all().values(
            "date",
            "category",
            *ALLOWED_QUERY_FLAGS.keys(),
        )

        # Build a list of IncidentByYear dataclasses with stats for each year
        incidents_by_year: dict[str, IncidentByYear] = {}
        incidents_by_category: dict[str, IncidentByYear] = {}
        incidents_by_flag: dict[str, IncidentByYear] = {}
        for incident in incidents:
            category: str = incident.get("category", "Uncategorised")

            self.count_by_year(incident["date"].year, incidents_by_year)
            self.count_by_category(category, incidents_by_category)
            self.count_by_flag(incident, incidents_by_flag)

        context["incidents_by_year"] = [
            IncidentByYear(name="All", slug="all", count=Incident.objects.count()),
            *sorted(incidents_by_category.values(), key=lambda x: x.name),
            *sorted(incidents_by_flag.values(), key=lambda x: x.name),
            *sorted(incidents_by_year.values(), key=lambda x: x.name),
        ]

        return context


class PublicationDetail(ListView[Incident]):
    model = Incident
    template_name = "incident_list.html"
    context_object_name = "incidents"

    def get_queryset(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> QuerySet[Incident]:
        return (
            super()
            .get_queryset()
            .select_related("publication")
            .filter(publication__id=self.kwargs["publication_id"])
            .order_by("date")
        )

    def get_context_data(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, Any]:
        context = super().get_context_data(*args, **kwargs)
        context["title"] = Publication.objects.get(id=self.kwargs["publication_id"])
        return context


class IncidentList(ListView[Incident]):
    """List incidents by status or year."""

    model = Incident
    template_name = "incident_list.html"
    context_object_name = "incidents"
    paginate_by = 100

    def __init__(self) -> None:
        self.filter: str = ""
        self.filter_type: str = "category"
        self.total_count: int = 0
        super().__init__()

    def get_queryset(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> QuerySet[Incident]:
        query = self.kwargs["query"].lower()
        queryset: QuerySet[Incident] = super().get_queryset().order_by("-date")

        # First match by category
        match query:
            case "all":
                self.filter_type = ""
                return self.prepare_queryset(query, queryset)
            case "uncategorised":
                self.filter = "uncategorised"
                return self.prepare_queryset(query, queryset.filter(category=""))
            case "other":
                self.filter = "other"
                return self.prepare_queryset(
                    query,
                    queryset.filter(category=Incident.Category.OTHER),
                )
            case "cave":
                self.filter = "cave"
                return self.prepare_queryset(
                    query,
                    queryset.filter(category=Incident.Category.CAVE),
                )
            case "mine":
                self.filter = "mine"
                return self.prepare_queryset(
                    query,
                    queryset.filter(category=Incident.Category.MINE),
                )
            case "cave-diving":
                self.filter = "cave diving"
                return self.prepare_queryset(
                    query,
                    queryset.filter(category=Incident.Category.DIVING),
                )

        # Now try matching by flags
        flag_query = query.replace("-", "_")
        print(flag_query)
        if flag_query in ALLOWED_QUERY_FLAGS:
            self.filter = ALLOWED_QUERY_FLAGS[flag_query]
            self.filter_type = "flag"
            return self.prepare_queryset(query, queryset.filter(**{flag_query: True}))

        # Finally, try matching by year
        try:
            year = int(query)
        except ValueError:
            return self.prepare_queryset(query, queryset, invalid_query=True)

        if 1800 < year <= datetime.now().year:
            yearly_qs = queryset.filter(date__year=year)
            if not bool(yearly_qs):
                messages.error(self.request, f"There are no incidents from {year} in the database.")
                self.filter_type = ""
                return self.prepare_queryset(query, queryset)

            self.filter = str(year)
            self.filter_type = "year"
            return self.prepare_queryset(query, yearly_qs)

        return self.prepare_queryset(query, queryset, invalid_query=True)

    def prepare_queryset(
        self,
        query: str,
        queryset: QuerySet[Incident],
        invalid_query: bool = False,
    ) -> QuerySet[Incident]:
        self.total_count = queryset.count()

        if invalid_query:
            self.filter_type = ""
            messages.error(
                self.request,
                f"Invalid query: '{query}'. Showing all incidents.",
            )

        if not bool(queryset):
            messages.error(self.request, "There are no incidents to show.")
        return queryset

    def get_page_title(self) -> str:
        if self.filter_type == "year":
            return f"Incidents from {self.filter}"
        if self.filter_type == "flag":
            return f"Incidents flagged as {self.filter}"
        if self.filter_type == "category":
            return f"{self.filter.capitalize()} incidents"
        return "Incident list"

    def get_context_data(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, Any]:
        context = super().get_context_data(*args, **kwargs)
        context["page_title"] = self.get_page_title()
        context["total_count"] = self.total_count
        context["filter"] = self.filter
        context["filter_type"] = self.filter_type
        return context


class IncidentDetail(DetailView[Incident]):
    model = Incident
    template_name = "incident_detail.html"
    context_object_name = "incident"

    def get_queryset(self) -> QuerySet[Incident]:
        return Incident.objects.select_related("publication").prefetch_related("injured_cavers")

    def get_context_data(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        if user := get_authed_user(self.request):
            if user.is_editor:
                context["injured_caver_add_form"] = InjuredCaverForm(self.object)
                context["incidents_on_same_date"] = Incident.objects.filter(
                    date=self.object.date
                ).exclude(pk=self.object.pk)

        return context


class IncidentUpdate(EditorOnly, UpdateView[Incident, IncidentForm]):
    model = Incident
    template_name = "incident_update.html"
    context_object_name = "incident"
    form_class = IncidentForm

    def form_valid(self, form: IncidentForm) -> HttpResponse:
        assert isinstance(self.request.user, ACAUser)
        form.instance.updated_by = self.request.user
        EditLogEntry.objects.create(
            incident=self.object,
            user=self.request.user,
            verb=EditLogEntry.EDITED,
            message="updated incident details",
        )
        return super().form_valid(form)


class IncidentAddText(EditorOnly, UpdateView[Incident, ReportTextForm]):
    model = Incident
    template_name = "incident_add_report_text.html"
    context_object_name = "incident"
    form_class = ReportTextForm

    def get_context_data(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, Any]:
        if not (obj := self.get_object()) or not obj.publication:
            raise ValueError("Incident object not found")

        context = super().get_context_data(**kwargs)
        text = obj.publication.text_file.read().decode("utf-8")
        text, count = highlight_text_from_incident(text, self.object)
        context["report_text"] = text
        context["find_count"] = count
        return context

    def get_queryset(self) -> QuerySet[Incident]:
        return Incident.objects.filter(
            publication__isnull=False,
            publication__text_file__isnull=False,
            publication__pdf_file__isnull=False,
        )

    def form_valid(self, form: ReportTextForm) -> HttpResponse:
        user = self.request.user
        assert isinstance(user, ACAUser), "User must be an ACAUser"

        form.instance.updated_by = user
        super().form_valid(form)

        EditLogEntry.objects.create(
            incident=self.object,
            user=user,
            verb=EditLogEntry.EDITED,
            message="report text updated",
        )

        if self.request.POST.get("editreport"):
            messages.success(
                self.request, "The report has been saved and you can now edit it below."
            )
            return redirect(reverse("db:incident_edit", args=[self.object.pk]))
        if self.request.POST.get("viewreport"):
            messages.success(self.request, "The report has been saved.")
            return redirect(self.object.get_absolute_url())

        messages.success(self.request, "The report has been saved.")
        return redirect(reverse("db:find_report_to_add_text"))


class IncidentAddAnalysis(EditorOnly, UpdateView[Incident, AnalysisTextForm]):
    model = Incident
    template_name = "incident_add_analysis.html"
    context_object_name = "incident"
    form_class = AnalysisTextForm

    def form_valid(
        self,
        form: AnalysisTextForm,
    ) -> HttpResponseRedirect:
        assert isinstance(self.request.user, ACAUser)
        form.instance.updated_by = self.request.user

        if self.request.POST.get("noanalysis"):
            EditLogEntry.objects.create(
                incident=self.object,
                user=self.request.user,
                verb=EditLogEntry.EDITED,
                message="marked as no analysis",
            )

            messages.success(self.request, "Incident marked as not containing analysis.")

            form.instance.no_analysis = True
            form.instance.incident_analysis = ""
            super().form_valid(form)
            return redirect(reverse("db:find_report_to_add_analysis"))

        EditLogEntry.objects.create(
            incident=self.object,
            user=self.request.user,
            verb=EditLogEntry.EDITED,
            message="analysis text updated",
        )

        super().form_valid(form)

        if self.request.POST.get("editreport"):
            messages.success(
                self.request, "The report has been saved and you can now edit it below."
            )
            return redirect(reverse("db:incident_edit", args=[self.object.pk]))
        if self.request.POST.get("viewreport"):
            messages.success(self.request, "The report has been saved.")
            return redirect(self.object.get_absolute_url())

        messages.success(self.request, "The report has been saved.")
        return redirect(reverse("db:find_report_to_add_analysis"))


class IncidentDelete(EditorOnly, View):
    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        incident = get_object_or_404(Incident, pk=self.kwargs["pk"])
        incident.delete()

        user = request.user
        assert isinstance(incident.publication, Publication)
        assert isinstance(user, ACAUser)

        EditLogEntry.objects.create(
            user=user,
            verb=EditLogEntry.DELETED,
            incident_name=str(incident),
            message="This incident was deleted",
        )

        messages.success(request, "The incident has been deleted.")
        return redirect("db:publication_detail", publication_id=incident.publication.pk)


class FindReportToAddText(EditorOnly, View):
    def get(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        qs = Incident.objects.need_report_text()
        if not bool(qs):
            messages.info(request, "There are no reports to add text to at the moment.")
            return redirect("db:index")

        incident = qs.order_by("?").first()
        if not incident:
            raise Http404("No incidents found in the database.")

        return redirect("db:add_report_text", pk=incident.pk)


class FindReportToAddAnalysis(EditorOnly, View):
    def get(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        qs = Incident.objects.need_analysis()
        if not bool(qs):
            messages.info(request, "There are no reports to add analysis to at the moment.")
            return redirect("db:index")

        incident = qs.order_by("?").first()
        if not incident:
            messages.info(request, "There are no reports to add analysis to at the moment.")
            return redirect("db:index")

        return redirect("db:add_analysis_text", pk=incident.pk)


class FindReportToReview(EditorOnly, View):
    def get(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        qs = Incident.objects.need_review()
        if bool(qs) and (incident := qs.order_by("?").first()):
            return redirect("db:incident_detail", pk=incident.pk)

        messages.info(request, "There are no reports to review at the moment.")
        return redirect("db:index")


class FindRandomIncident(View):
    def get(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        incident = Incident.objects.all().order_by("?").first()
        if not incident:
            raise Http404("No incidents found in the database.")

        return redirect("db:incident_detail", pk=incident.pk)


class EditIncidentDate(EditorOnly, UpdateView[Incident, ApproveIncidentDateForm]):
    model = Incident
    context_object_name = "incident"
    template_name = "approval/incident_approve_date.html"
    form_class = ApproveIncidentDateForm

    def get_success_url(self) -> str:
        return reverse("db:approve_report_text", args=[self.object.pk])


class EditReportText(EditorOnly, UpdateView[Incident, ApproveReportTextForm]):
    model = Incident
    context_object_name = "incident"
    template_name = "approval/incident_approve_text.html"
    form_class = ApproveReportTextForm

    def get_success_url(self) -> str:
        return reverse("db:approve_injured_cavers", args=[self.object.pk])

    def get_context_data(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["incident_report_sim"] = None
        context["incident_analysis_sim"] = None
        context["incident_references_sim"] = None

        incident = self.get_object()
        if incident.data_input_source == Incident.DataInput.AI:
            context["incident_report_sim"] = similarity(incident, "incident_report")
            context["incident_analysis_sim"] = similarity(incident, "incident_analysis")
            context["incident_references_sim"] = similarity(incident, "incident_references")

        return context


class EditInjuredCavers(EditorOnly, DetailView[Incident]):
    model = Incident
    context_object_name = "incident"
    template_name = "approval/incident_approve_cavers.html"
    form_class = ApproveReportTextForm

    def get_context_data(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["injured_caver_add_form"] = InjuredCaverForm(self.object)
        return context


class EditIncidentMetadata(EditorOnly, UpdateView[Incident, ApproveMetadataForm]):
    model = Incident
    context_object_name = "incident"
    template_name = "approval/incident_approve_metadata.html"
    form_class = ApproveMetadataForm

    def get_success_url(self) -> str:
        return reverse("db:approve_incident_flags", args=[self.object.pk])


class EditIncidentFlags(EditorOnly, UpdateView[Incident, ApproveFlagsForm]):
    model = Incident
    context_object_name = "incident"
    template_name = "approval/incident_approve_flags.html"
    form_class = ApproveFlagsForm

    def get_success_url(self) -> str:
        return reverse("db:approve_incident_final", args=[self.object.pk])


class EditIncidentFinal(EditorOnly, DetailView[Incident]):
    model = Incident
    context_object_name = "incident"
    template_name = "approval/incident_approve_final.html"

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        user = request.user
        assert isinstance(user, ACAUser)

        incident = self.get_object()
        incident.save()

        EditLogEntry.objects.create(
            user=user,
            incident=incident,
            verb=EditLogEntry.EDITED,
            message="edited report",
        )
        messages.success(request, "The report has been edited.")
        return redirect("db:incident_detail", pk=incident.pk)


class InjuredCaverAdd(InjuredCaverHTMXView):
    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        user = request.user
        assert isinstance(user, ACAUser)
        incident = self.incident
        assert isinstance(incident, Incident)

        form = InjuredCaverForm(incident, request.POST)

        if form.is_valid():
            caver = form.save(commit=False)
            caver.incident = incident
            caver.save()

            if caver.first_name or caver.surname:
                edit_msg = f"added injured caver: {caver.first_name} {caver.surname}"
            else:
                edit_msg = "added injured caver"

            EditLogEntry.objects.create(
                user=user,
                incident=self.incident,
                verb=EditLogEntry.EDITED,
                message=edit_msg,
            )

            messages.success(request, "The injured caver has been added.")
            return self.render_to_response()

        messages.error(
            request,
            "There was an error adding the injured caver. "
            "Please ensure you have filled in the form correctly and try again.",
        )
        return self.render_to_response()


class InjuredCaverUpdate(InjuredCaverHTMXView):
    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        user = request.user
        assert isinstance(user, ACAUser)
        caver = self.caver
        assert isinstance(caver, InjuredCaver)

        form = InjuredCaverForm(self.incident, request.POST, instance=self.caver)
        if form.is_valid():
            form.save()

            if caver.first_name or caver.surname:
                edit_msg = f"edited injured caver: {caver.first_name} {caver.surname}"
            else:
                edit_msg = "edited injured caver"

            EditLogEntry.objects.create(
                user=user,
                incident=self.incident,
                verb=EditLogEntry.EDITED,
                message=edit_msg,
            )

            messages.success(request, "The injured caver has been updated.")
            return self.render_to_response()

        messages.error(
            request,
            "There was an error adding the injured caver. "
            "Please ensure you have filled in the form correctly and try again.",
        )
        return self.render_to_response()


class InjuredCaverDelete(InjuredCaverHTMXView):
    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        user = request.user
        assert isinstance(user, ACAUser)
        caver = self.caver
        assert isinstance(caver, InjuredCaver)

        caver.delete()

        if caver.first_name or caver.surname:
            edit_msg = f"deleted injured caver: {caver.first_name} {caver.surname}"
        else:
            edit_msg = "deleted injured caver"

        EditLogEntry.objects.create(
            user=user,
            incident=self.incident,
            verb=EditLogEntry.EDITED,
            message=edit_msg,
        )

        messages.success(request, "The injured caver has been deleted.")
        return self.render_to_response()


class IncidentRedirect(View):
    """Redirect all /incident/ URLs to /i/ URLs."""

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseRedirect:
        path = self.kwargs["path"]
        return redirect(f"/i/{path}/")
