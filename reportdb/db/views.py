from dataclasses import dataclass
from datetime import datetime

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView, TemplateView, UpdateView, View
from editlog.models import EditLogEntry
from reversion.views import RevisionMixin

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
from .mixins import ApprovalMixin, EditorOnly, InjuredCaverHTMXView
from .models import Incident, Publication
from .services import highlight_text_from_incident, similarity


@dataclass
class IncidentsByYear:
    """A dataclass for storing incidents by year."""

    year: int  # The year
    incidents: int  # Total number of incidents
    approved: int  # Number of incidents approved
    pending: int  # Number of incidents pending information
    review: int  # Number of incidents pending review
    need_text: int  # Number of incidents pending report text

    def __str__(self):
        return str(self.year)

    def completion_rate(self) -> float:
        """Return the completion rate as a percentage."""
        return self.approved / self.incidents * 100


class About(TemplateView):
    template_name = "about.html"


class Help(TemplateView):
    template_name = "help.html"


class Index(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Build context for the incident list by year
        incidents = Incident.objects.public()
        context["incidentmanager"] = Incident.objects

        context["all_incidents_completion"] = 0
        if bool(incidents):  # Avoid division by zero on empty queryset
            context["all_incidents_completion"] = (
                incidents.filter(approved=True).count() / incidents.count() * 100
            )

        context["all_incidents_need_text"] = incidents.filter(
            incident_report=""
        ).count()

        # Build a list of IncidentByYear dataclasses with stats for each year
        incidents_by_year = []
        for incident in incidents:
            year = incident.date.year
            for y in incidents_by_year:
                if y.year == year:
                    y.incidents += 1
                    if incident.approved:
                        y.approved += 1
                    else:
                        y.pending += 1

                    if incident.editing_notes:
                        y.review += 1

                    if not incident.incident_report:
                        y.need_text += 1
                    break
            else:
                incidents_by_year.append(
                    IncidentsByYear(
                        year=year,
                        incidents=1,
                        approved=1 if incident.approved else 0,
                        pending=1 if not incident.approved else 0,
                        review=1 if incident.editing_notes else 0,
                        need_text=1 if not incident.incident_report else 0,
                    )
                )

        incidents_by_year.sort(key=lambda x: x.year)
        context["incidents_by_year"] = incidents_by_year

        return context


class PublicationDetail(ListView):
    model = Incident
    template_name = "incident_list.html"
    context_object_name = "incidents"

    def get_queryset(self, *args, **kwargs):
        queryset = (
            super()
            .get_queryset()
            .select_related("publication")
            .filter(publication__id=self.kwargs["publication_id"])
            .order_by("-approved", "date")
        )
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["title"] = Publication.objects.get(id=self.kwargs["publication_id"])
        return context


class IncidentList(ListView):
    """List incidents by status or year."""

    model = Incident
    template_name = "incident_list.html"
    context_object_name = "incidents"

    def __init__(self):
        self.title = "Incident list"
        super().__init__()

    def get_queryset(self, *args, **kwargs):
        queryset = (
            super().get_queryset().select_related("publication").order_by("-date")
        )
        query = self.kwargs["status"]

        # First try listing incidents by year
        try:
            year = int(query)
            if 1900 < year <= datetime.now().year:
                yearly_qs = queryset.filter(date__year=year)
                if not bool(yearly_qs):
                    messages.error(
                        self.request,
                        f"There are no incidents from {year}. Showing all incidents.",
                    )
                    return queryset

                self.title = f"Incidents from {year}"
                return yearly_qs
        except ValueError:
            pass

        # Then try listing incidents by status
        valid_statuses = ["approved", "pending", "review", "text", "edit"]
        if query in valid_statuses:
            match query:
                case "approved":
                    queryset = Incident.objects.approved()
                    self.title = "Approved incidents"
                case "pending":
                    queryset = Incident.objects.pending()
                    self.title = "Incidents pending information"
                case "review":
                    queryset = Incident.objects.need_review()
                    self.title = "Incidents pending review"
                case "text":
                    queryset = Incident.objects.need_report_text()
                    self.title = "Incidents pending report text"
                case "edit":
                    queryset = Incident.objects.to_edit()
                    self.title = "Incidents pending editing"

        if not bool(queryset):
            messages.error(self.request, "There are no incidents to show.")
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["title"] = self.title
        return context


class IncidentDetail(DetailView):
    model = Incident
    template_name = "incident_detail.html"
    context_object_name = "incident"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if not self.object.approved:
            incidents_on_same_date = Incident.objects.filter(date=self.object.date)
            cleaned_incidents = incidents_on_same_date.exclude(pk=self.object.pk)
            context["incidents_on_same_date"] = cleaned_incidents

        context["injured_caver_add_form"] = InjuredCaverForm(self.object)
        context["incident"] = self.object
        return context


class IncidentUpdate(EditorOnly, RevisionMixin, UpdateView):
    model = Incident
    template_name = "incident_update.html"
    context_object_name = "incident"
    form_class = IncidentForm

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        EditLogEntry.objects.create(
            incident=self.object,
            user=self.request.user,
            verb=EditLogEntry.EDITED,
            message="updated incident details",
        )
        return super().form_valid(form)


class IncidentAddText(EditorOnly, RevisionMixin, UpdateView):
    model = Incident
    template_name = "incident_add_report_text.html"
    context_object_name = "incident"
    form_class = ReportTextForm

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        with open(self.object.publication.get_text_path(), "r") as f:
            text = f.read()
        text, count = highlight_text_from_incident(text, self.object)
        context["report_text"] = text
        context["find_count"] = count
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        super().form_valid(form)

        EditLogEntry.objects.create(
            incident=self.object,
            user=self.request.user,
            verb=EditLogEntry.EDITED,
            message="report text updated",
        )

        if self.request.POST.get("editreport"):
            messages.success(
                self.request, "The report has been saved and you can now edit it below."
            )
            return redirect(reverse("db:incident_edit", args=[self.object.pk]))
        elif self.request.POST.get("viewreport"):
            messages.success(self.request, "The report has been saved.")
            return redirect(self.object.get_absolute_url())

        messages.success(self.request, "The report has been saved.")
        return redirect(reverse("db:find_report_to_add_text"))


class IncidentAddAnalysis(EditorOnly, RevisionMixin, UpdateView):
    model = Incident
    template_name = "incident_add_analysis.html"
    context_object_name = "incident"
    form_class = AnalysisTextForm

    def form_valid(self, form):
        form.instance.updated_by = self.request.user

        if self.request.POST.get("noanalysis"):
            EditLogEntry.objects.create(
                incident=self.object,
                user=self.request.user,
                verb=EditLogEntry.EDITED,
                message="marked as no analysis",
            )

            messages.success(
                self.request, "Incident marked as not containing analysis."
            )

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
        elif self.request.POST.get("viewreport"):
            messages.success(self.request, "The report has been saved.")
            return redirect(self.object.get_absolute_url())

        messages.success(self.request, "The report has been saved.")
        return redirect(reverse("db:find_report_to_add_analysis"))


class IncidentDelete(EditorOnly, RevisionMixin, View):
    def post(self, request, *args, **kwargs):
        incident = get_object_or_404(Incident, pk=self.kwargs["pk"])
        if incident.approved:
            messages.error(
                request,
                "Please ensure a report is not marked as approved "
                "before attempting to delete it.",
            )
            return redirect(incident.get_absolute_url())

        incident.delete()
        EditLogEntry.objects.create(
            user=self.request.user,
            verb=EditLogEntry.DELETED,
            incident_name=str(incident),
            message="This incident was deleted",
        )

        messages.success(request, "The incident has been deleted.")
        return redirect("db:publication_detail", publication_id=incident.publication.pk)


class FindReportToAddText(EditorOnly, View):
    def get(self, request, *args, **kwargs):
        qs = Incident.objects.need_report_text()
        if not bool(qs):
            messages.info(request, "There are no reports to add text to at the moment.")
            return redirect("db:index")

        incident = qs.order_by("?").first()
        return redirect("db:add_report_text", pk=incident.pk)


class FindReportToApprove(EditorOnly, View):
    def get(self, request, *args, **kwargs):
        qs = Incident.objects.pending()
        if not bool(qs):
            messages.info(request, "There are no reports to approve at the moment.")
            return redirect("db:index")

        incident = qs.order_by("?").first()
        if incident.data_input_source == Incident.DataInput.AI:
            return redirect("db:approve_incident_date", pk=incident.pk)
        return redirect("db:approve_report_text", pk=incident.pk)


class FindReportToAddAnalysis(EditorOnly, View):
    def get(self, request, *args, **kwargs):
        qs = Incident.objects.need_analysis()
        if not bool(qs):
            messages.info(
                request, "There are no reports to add analysis to at the moment."
            )
            return redirect("db:index")

        incident = qs.order_by("?").first()
        return redirect("db:add_analysis_text", pk=incident.pk)


class FindReportToReview(EditorOnly, View):
    def get(self, request, *args, **kwargs):
        qs = Incident.objects.need_review()
        if not bool(qs):
            messages.info(request, "There are no reports to review at the moment.")
            return redirect("db:index")

        incident = qs.order_by("?").first()
        return redirect("db:incident_detail", pk=incident.pk)


class FindRandomApprovedIncident(View):
    def get(self, request, *args, **kwargs):
        incident = Incident.objects.approved().order_by("?").first()
        return redirect("db:incident_detail", pk=incident.pk)


class ApproveIncidentDate(ApprovalMixin, RevisionMixin, UpdateView):
    model = Incident
    context_object_name = "incident"
    template_name = "approval/incident_approve_date.html"
    form_class = ApproveIncidentDateForm

    def get_success_url(self):
        return reverse("db:approve_report_text", args=[self.object.pk])


class ApproveReportText(ApprovalMixin, RevisionMixin, UpdateView):
    model = Incident
    context_object_name = "incident"
    template_name = "approval/incident_approve_text.html"
    form_class = ApproveReportTextForm

    def get_success_url(self):
        return reverse("db:approve_injured_cavers", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["incident_report_sim"] = None
        context["incident_analysis_sim"] = None
        context["incident_references_sim"] = None

        incident = self.get_object()
        if incident.data_input_source == Incident.DataInput.AI:
            context["incident_report_sim"] = similarity(incident, "incident_report")
            context["incident_analysis_sim"] = similarity(incident, "incident_analysis")
            context["incident_references_sim"] = similarity(
                incident, "incident_references"
            )

        return context


class ApproveInjuredCavers(ApprovalMixin, RevisionMixin, DetailView):
    model = Incident
    context_object_name = "incident"
    template_name = "approval/incident_approve_cavers.html"
    form_class = ApproveReportTextForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["injured_caver_add_form"] = InjuredCaverForm(self.object)
        return context


class ApproveIncidentMetadata(ApprovalMixin, RevisionMixin, UpdateView):
    model = Incident
    context_object_name = "incident"
    template_name = "approval/incident_approve_metadata.html"
    form_class = ApproveMetadataForm

    def get_success_url(self):
        return reverse("db:approve_incident_flags", args=[self.object.pk])


class ApproveIncidentFlags(ApprovalMixin, RevisionMixin, UpdateView):
    model = Incident
    context_object_name = "incident"
    template_name = "approval/incident_approve_flags.html"
    form_class = ApproveFlagsForm

    def get_success_url(self):
        return reverse("db:approve_incident_final", args=[self.object.pk])


class ApproveIncidentFinal(ApprovalMixin, RevisionMixin, DetailView):
    model = Incident
    context_object_name = "incident"
    template_name = "approval/incident_approve_final.html"

    def post(self, request, *args, **kwargs):
        incident = self.get_object()
        incident.approved = True
        incident.save()
        EditLogEntry.objects.create(
            user=request.user,
            incident=incident,
            verb=EditLogEntry.EDITED,
            message="approved report",
        )
        messages.success(request, "The report has been approved.")
        return redirect("db:incident_detail", pk=incident.pk)


class IncidentUnapprove(EditorOnly, RevisionMixin, View):
    def post(self, request, *args, **kwargs):
        incident = get_object_or_404(Incident, pk=self.kwargs["pk"])
        incident.approved = False
        incident.save()
        EditLogEntry.objects.create(
            user=request.user,
            incident=incident,
            verb=EditLogEntry.EDITED,
            message="unapproved report",
        )
        messages.success(request, "The report has been unapproved.")
        return redirect("db:incident_detail", pk=incident.pk)


class InjuredCaverAdd(InjuredCaverHTMXView):
    def post(self, request, *args, **kwargs):
        form = InjuredCaverForm(self.incident, request.POST)

        if form.is_valid():
            caver = form.save(commit=False)
            caver.incident = self.incident
            caver.save()

            if caver.first_name or caver.surname:
                edit_msg = f"added injured caver: {caver.first_name} {caver.surname}"
            else:
                edit_msg = "added injured caver"

            EditLogEntry.objects.create(
                user=request.user,
                incident=self.incident,
                verb=EditLogEntry.EDITED,
                message=edit_msg,
            )

            messages.success(request, "The injured caver has been added.")
            return self.render_to_response()
        else:
            messages.error(
                request,
                "There was an error adding the injured caver. "
                "Please ensure you have filled in the form correctly and try again.",
            )
            return self.render_to_response()


class InjuredCaverUpdate(InjuredCaverHTMXView):
    def post(self, request, *args, **kwargs):
        form = InjuredCaverForm(self.incident, request.POST, instance=self.caver)

        if form.is_valid():
            form.save()

            caver = self.caver
            if caver.first_name or caver.surname:
                edit_msg = f"edited injured caver: {caver.first_name} {caver.surname}"
            else:
                edit_msg = "edited injured caver"

            EditLogEntry.objects.create(
                user=request.user,
                incident=self.incident,
                verb=EditLogEntry.EDITED,
                message=edit_msg,
            )

            messages.success(request, "The injured caver has been updated.")
            return self.render_to_response()
        else:
            messages.error(
                request,
                "There was an error adding the injured caver. "
                "Please ensure you have filled in the form correctly and try again.",
            )
            return self.render_to_response()


class InjuredCaverDelete(InjuredCaverHTMXView):
    def post(self, request, *args, **kwargs):
        self.caver.delete()

        if self.caver.first_name or self.caver.surname:
            edit_msg = (
                f"deleted injured caver: {self.caver.first_name} {self.caver.surname}"
            )
        else:
            edit_msg = "deleted injured caver"

        EditLogEntry.objects.create(
            user=request.user,
            incident=self.incident,
            verb=EditLogEntry.EDITED,
            message=edit_msg,
        )

        messages.success(request, "The injured caver has been deleted.")
        return self.render_to_response()


class IncidentRedirect(View):
    """Redirect all /incident/ URLs to /i/ URLs."""

    def get(self, request, *args, **kwargs):
        path = self.kwargs["path"]
        return redirect(f"/i/{path}/")
