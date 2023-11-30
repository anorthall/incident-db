from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("login/", views.Login.as_view(), name="login"),
    path("logout/", views.Logout.as_view(), name="logout"),
    path("password/", views.PasswordChangeView.as_view(), name="password"),
    path("healthcheck/", views.Healthcheck.as_view(), name="healthcheck"),
]
