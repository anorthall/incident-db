from django.urls import path

from . import views

app_name = "editlog"

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("scores/", views.Scores.as_view(), name="scores"),
]
