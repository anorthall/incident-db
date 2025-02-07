from typing import Any

from crispy_bootstrap5.bootstrap5 import FloatingField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, Submit
from django import forms
from django.contrib import auth
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from django.http import HttpRequest

from .models import ACAUser


class AuthenticationForm(auth.forms.AuthenticationForm):
    def __init__(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.request = request
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "mb-4"
        self.helper.form_show_errors = False
        self.helper.layout = Layout(
            Div(
                Div(
                    FloatingField("username"),
                    css_class="col-12",
                ),
                Div(
                    FloatingField("password"),
                    css_class="col-12",
                ),
                Div(
                    Submit("submit", "Sign in", css_class="btn-lg h-100 w-100"),
                    css_class="col-12",
                ),
                css_class="row",
            )
        )


class PasswordChangeForm(auth.forms.PasswordChangeForm):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "mb-4"
        self.helper.layout = Layout(
            Div(
                Div(
                    FloatingField("old_password"),
                    css_class="col-12",
                ),
                Div(
                    FloatingField("new_password1"),
                    css_class="col-12",
                ),
                Div(
                    FloatingField("new_password2"),
                    css_class="col-12",
                ),
                Div(
                    Submit(
                        "submit",
                        "Change password",
                        css_class="btn-lg h-100 w-100",
                    ),
                    css_class="col-12",
                ),
                css_class="row",
            )
        )


class UserCreationForm(forms.ModelForm):  # type: ignore[type-arg]
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        model = ACAUser
        fields = [
            "email",
            "name",
            "password1",
            "password2",
            "is_active",
            "is_superuser",
        ]

    def clean_password2(self) -> str:
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        assert isinstance(password1, str)
        assert isinstance(password2, str)

        if (
            not password1
            or not password2
            or not isinstance(password1, str)
            or not isinstance(password2, str)
        ):
            raise ValidationError("Password cannot be empty")

        if password1 != password2:
            raise ValidationError("Passwords don't match")

        return password2

    def save(
        self,
        commit: bool = True,
    ) -> ACAUser:
        user = super().save(commit=False)
        assert isinstance(user, ACAUser)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm[ACAUser]):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = ACAUser
        fields = [
            "email",
            "name",
            "is_active",
        ]
