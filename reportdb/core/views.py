from typing import Any, cast

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import View

from .forms import AuthenticationForm, PasswordChangeForm


class Login(auth_views.LoginView):
    template_name = "login.html"
    form_class = AuthenticationForm


class Logout(LoginRequiredMixin, auth_views.LogoutView):
    def dispatch(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        result = super().dispatch(
            request,
            *args,
            **kwargs,
        )
        messages.success(
            request,
            "You have been logged out.",
        )
        return cast(HttpResponse, result)


class PasswordChangeView(
    SuccessMessageMixin[PasswordChangeForm],
    LoginRequiredMixin,
    auth_views.PasswordChangeView,
):
    success_message = "Your password has been changed."
    success_url = reverse_lazy("db:index")
    template_name = "password_change.html"
    form_class = PasswordChangeForm


class Healthcheck(View):
    def get(
        self,
        request: HttpRequest,
    ) -> HttpResponse:
        return HttpResponse("OK")
