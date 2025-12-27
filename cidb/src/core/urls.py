from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("healthcheck/", views.Healthcheck.as_view(), name="healthcheck"),
]
