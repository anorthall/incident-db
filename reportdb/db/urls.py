from django.urls import path, re_path

from . import views

# fmt: off
app_name = "db"
urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("about/", views.About.as_view(), name="about"),
    path("help/", views.Help.as_view(), name="help"),
    path("pub/<int:publication_id>/", views.PublicationDetail.as_view(), name="publication_detail"),  # noqa: E501
    path("list/<str:status>/", views.IncidentList.as_view(), name="incident_list"),  # noqa: E501
    path("i/<int:pk>/", views.IncidentDetail.as_view(), name="incident_detail"),
    path("i/<int:pk>/edit/", views.IncidentUpdate.as_view(), name="incident_edit"),  # noqa: E501
    path("i/<int:pk>/delete/", views.IncidentDelete.as_view(), name="incident_delete"),  # noqa: E501
    path("i/<int:pk>/add-report/", views.IncidentAddText.as_view(), name="add_report_text"),  # noqa: E501
    path("i/<int:pk>/add-analysis/", views.IncidentAddAnalysis.as_view(), name="add_analysis_text"),  # noqa: E501
    path("i/<int:pk>/approve/date/", views.ApproveIncidentDate.as_view(), name="approve_incident_date"),  # noqa: E501
    path("i/<int:pk>/approve/text/", views.ApproveReportText.as_view(), name="approve_report_text"),  # noqa: E501
    path("i/<int:pk>/approve/cavers/", views.ApproveInjuredCavers.as_view(), name="approve_injured_cavers"),  # noqa: E501
    path("i/<int:pk>/approve/metadata/", views.ApproveIncidentMetadata.as_view(), name="approve_metadata"),  # noqa: E501
    path("i/<int:pk>/approve/flags/", views.ApproveIncidentFlags.as_view(), name="approve_incident_flags"),  # noqa: E501
    path("i/<int:pk>/approve/final/", views.ApproveIncidentFinal.as_view(), name="approve_incident_final"),  # noqa: E501
    path("i/<int:pk>/unapprove/", views.IncidentUnapprove.as_view(), name="incident_unapprove"),  # noqa: E501
    path("i/<int:pk>/cavers/add/", views.InjuredCaverAdd.as_view(), name="injured_caver_add"),  # noqa: E501
    path("i/random/", views.FindRandomApprovedIncident.as_view(), name="random_incident"),  # noqa: E501
    path("i/add-report/", views.FindReportToAddText.as_view(), name="find_report_to_add_text"),  # noqa: E501
    path("i/approve-report/", views.FindReportToApprove.as_view(), name="find_report_to_approve"),  # noqa: E501
    path("i/review-report/", views.FindReportToReview.as_view(), name="find_report_to_review"),  # noqa: E501
    path("i/add-analysis/", views.FindReportToAddAnalysis.as_view(), name="find_report_to_add_analysis"),  # noqa: E501
    path("cavers/<int:caver_pk>/delete/", views.InjuredCaverDelete.as_view(), name="injured_caver_delete"),  # noqa: E501
    path("cavers/<int:caver_pk>/edit/", views.InjuredCaverUpdate.as_view(), name="injured_caver_update"),  # noqa: E501
    re_path(r"^incident/(?P<path>\S+)/$", views.IncidentRedirect.as_view(), name="incident_redirect"),  # noqa: E501
]
