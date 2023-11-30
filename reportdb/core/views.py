from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import View

from .forms import AuthenticationForm, PasswordChangeForm


class Login(auth_views.LoginView):
    template_name = "login.html"
    form_class = AuthenticationForm


class Logout(LoginRequiredMixin, auth_views.LogoutView):
    def dispatch(self, *args, **kwargs):
        result = super().dispatch(*args, **kwargs)
        messages.success(self.request, "You have been logged out.")
        return result


class PasswordChangeView(
    SuccessMessageMixin, LoginRequiredMixin, auth_views.PasswordChangeView
):
    success_message = "Your password has been changed."
    success_url = reverse_lazy("db:index")
    template_name = "password_change.html"
    form_class = PasswordChangeForm


class Healthcheck(View):
    def get(self, request):
        return HttpResponse("OK")
