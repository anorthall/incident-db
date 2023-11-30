from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout
from django import forms

from .models import Incident, InjuredCaver


class CustomCheckbox(Field):
    template = "forms/custom_checkbox.html"


class AnalysisTextForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            "incident_report",
            "incident_analysis",
            "editing_notes",
        ]
        widgets = {
            "incident_report": forms.Textarea(attrs={"rows": 10}),
            "incident_analysis": forms.Textarea(attrs={"rows": 8}),
            "editing_notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields["incident_report"].help_text = ""
        self.fields["incident_analysis"].help_text = ""
        self.fields["editing_notes"].help_text = (
            "Notes that will be visible only to people editing this incident "
            "on this website."
        )


class ReportTextForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            "incident_report",
            "incident_analysis",
            "incident_summary",
            "editing_notes",
            "incident_notes",
            "incident_references",
        ]
        widgets = {
            "incident_report": forms.Textarea(attrs={"rows": 10}),
            "incident_analysis": forms.Textarea(attrs={"rows": 8}),
            "incident_references": forms.Textarea(attrs={"rows": 4}),
            "incident_notes": forms.Textarea(attrs={"rows": 4}),
            "incident_summary": forms.Textarea(attrs={"rows": 4}),
            "editing_notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields["incident_report"].label = ""
        self.fields["incident_report"].help_text = (
            "Copy the original text of the report from the publication "
            "above into this box and properly format it.<br> Any references to "
            "external publications, such as websites, journals or books, "
            "should be included in the 'References' field below."
        )
        self.helper.layout = Layout(
            Field("incident_report"),
            Field("incident_analysis"),
            Field("incident_references"),
            Field("incident_summary"),
            Field("incident_notes"),
            Field("editing_notes"),
        )


class BaseIncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            "date",
            "approximate_date",
            "cave",
            "state",
            "county",
            "country",
            "category",
            "incident_type",
            "incident_type_2",
            "incident_type_3",
            "primary_cause",
            "secondary_cause",
            "group_type",
            "group_size",
            "source",
            "aid_type",
            "fatality",
            "injury",
            "multiple_incidents",
            "rescue_over_24_hours",
            "vertical",
            "spar",
            "incident_report",
            "incident_analysis",
            "incident_summary",
            "incident_notes",
            "incident_references",
            "editing_notes",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "incident_report": forms.Textarea(attrs={"rows": 8}),
            "incident_analysis": forms.Textarea(attrs={"rows": 6}),
            "incident_summary": forms.Textarea(attrs={"rows": 4}),
            "incident_notes": forms.Textarea(attrs={"rows": 3}),
            "incident_references": forms.Textarea(attrs={"rows": 3}),
            "editing_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields["approximate_date"].help_text = ""
        self.fields[
            "incident_report"
        ].help_text = "The original incident report from the publication."
        self.fields[
            "incident_analysis"
        ].help_text = "The original incident analysis from the publication."
        self.fields[
            "incident_references"
        ].help_text = "Any references to external publications or websites."
        self.fields[
            "incident_notes"
        ].help_text = "Any notes that may be relevant to people reading the report."
        self.fields[
            "editing_notes"
        ].help_text = (
            "Any notes that may be relevant to editors. These notes are private."
        )
        self.fields["incident_type"].choices = (
            ("", "Select a type..."),
            *self.fields["incident_type"].choices,
        )


class IncidentForm(BaseIncidentForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Field("date", wrapper_class="col-lg-6"),
                CustomCheckbox(
                    "approximate_date", wrapper_class="col-lg-6 checkbox-adjust-down"
                ),
                css_class="row my-0",
            ),
            HTML("<hr>"),
            Div(
                Field("cave", wrapper_class="col-lg-6"),
                Field("state", wrapper_class="col-lg-6"),
                Field("county", wrapper_class="col-lg-6"),
                Field("country", wrapper_class="col-lg-6"),
                css_class="row my-0",
            ),
            HTML("<hr>"),
            Div(
                Field("category", wrapper_class="col-lg-6"),
                Field("incident_type", wrapper_class="col-lg-6"),
                Field("incident_type_2", wrapper_class="col-lg-6"),
                Field("incident_type_3", wrapper_class="col-lg-6"),
                Field("primary_cause", wrapper_class="col-lg-6"),
                Field("secondary_cause", wrapper_class="col-lg-6"),
                Field("aid_type", wrapper_class="col-lg-6"),
                Field("group_type", wrapper_class="col-lg-6"),
                Field("group_size", wrapper_class="col-lg-6"),
                Field("source", wrapper_class="col-lg-6"),
                css_class="row my-0",
            ),
            HTML("<div class='fw-bolder mt-3 mb-3'>Incident flags</div>"),
            Div(
                CustomCheckbox("fatality"),
                CustomCheckbox("injury"),
                CustomCheckbox("multiple_incidents"),
                CustomCheckbox("rescue_over_24_hours"),
                CustomCheckbox("vertical"),
                CustomCheckbox("spar"),
                css_class="row g-3",
            ),
            HTML("<hr class='mt-5'>"),
            HTML("<div class='fw-bolder mt-4'>Incident text fields</div>"),
            HTML(
                """
<p class='form-text mb-4'>
  Ensure that the text matches the original publication as closely as possible.
  Analysis and references should be split out of the main report and placed in
  the appropriate fields below. You are free to add additional references if
  you feel they are relevant. The notes field is for any additional information
  that does not fit in the other fields that may be relevant to people reading
  the report. The editing notes field is private and is only visible to editors.
</p>
            """
            ),
            "incident_report",
            "incident_analysis",
            "incident_summary",
            "incident_references",
            "incident_notes",
            "editing_notes",
            HTML("<hr class='my-4'>"),
        )


class ApproveIncidentDateForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            "date",
            "approximate_date",
            "cave",
            "state",
            "county",
            "country",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "county": forms.TextInput(attrs={"placeholder": "Optional"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        for field in self.fields:
            self.fields[field].help_text = None

        self.helper.layout = Layout(
            Div(
                Field("date", wrapper_class="col-lg-6"),
                CustomCheckbox(
                    "approximate_date", wrapper_class="col-lg-6 checkbox-adjust-down"
                ),
                css_class="row my-0",
            ),
            Div(
                Field("cave", wrapper_class="col-12"),
                Field("state", wrapper_class="col-lg-4"),
                Field("county", wrapper_class="col-lg-4"),
                Field("country", wrapper_class="col-lg-4"),
                css_class="row my-0",
            ),
        )


class ApproveReportTextForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            "incident_report",
            "incident_analysis",
            "incident_summary",
            "incident_notes",
            "incident_references",
        ]
        widgets = {
            "incident_report": forms.Textarea(attrs={"rows": 2}),
            "incident_analysis": forms.Textarea(attrs={"rows": 2}),
            "incident_summary": forms.Textarea(attrs={"rows": 2}),
            "incident_notes": forms.Textarea(attrs={"rows": 2}),
            "incident_references": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields["incident_report"].required = True

        for field in self.fields:
            self.fields[field].help_text = None
            self.fields[field].label = ""

        if self.instance:
            if self.instance.publication and self.instance.publication_page:
                self.fields["incident_report"].help_text = (
                    f"Original report from {self.instance.publication}, "
                    f"page {self.instance.publication_page}."
                )


class ApproveMetadataForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            "cave",
            "state",
            "county",
            "country",
            "category",
            "incident_type",
            "incident_type_2",
            "incident_type_3",
            "primary_cause",
            "secondary_cause",
            "aid_type",
            "group_type",
            "group_size",
            "source",
        ]
        widgets = {
            "secondary_cause": forms.TextInput(attrs={"placeholder": "Optional"}),
            "county": forms.TextInput(attrs={"placeholder": "Optional"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        for field in self.fields:
            self.fields[field].help_text = None

        self.fields["incident_type"].choices = (
            ("", "Select a type..."),
            *self.fields["incident_type"].choices,
        )

        self.helper.layout = Layout(
            Div(
                Field("cave", wrapper_class="col-12"),
                Field("state", wrapper_class="col-lg-4"),
                Field("county", wrapper_class="col-lg-4"),
                Field("country", wrapper_class="col-lg-4"),
                Field("category", wrapper_class="col-lg-6"),
                Field("incident_type", wrapper_class="col-lg-6"),
                Field("incident_type_2", wrapper_class="col-lg-6"),
                Field("incident_type_3", wrapper_class="col-lg-6"),
                Field("primary_cause", wrapper_class="col-12"),
                Field("secondary_cause", wrapper_class="col-12"),
                Field("group_type", wrapper_class="col-lg-6"),
                Field("group_size", wrapper_class="col-lg-6"),
                Field("aid_type", wrapper_class="col-lg-6"),
                Field("source", wrapper_class="col-lg-6"),
                css_class="row my-0",
            ),
        )


class ApproveFlagsForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            "fatality",
            "injury",
            "multiple_incidents",
            "rescue_over_24_hours",
            "vertical",
            "spar",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class InjuredCaverForm(forms.ModelForm):
    class Meta:
        model = InjuredCaver
        fields = ["first_name", "surname", "age", "sex", "injuries", "injury_areas"]

    def __init__(self, incident, *args, **kwargs):
        self.incident = incident
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_id = f"{self.incident.pk}_caver_form"
        self.helper.layout = Layout(
            Div(
                Field("first_name", wrapper_class="col-12 col-lg-6"),
                Field("surname", wrapper_class="col-12 col-lg-6"),
                Field("age", wrapper_class="col-12 col-lg-6"),
                Field("sex", wrapper_class="col-12 col-lg-6"),
                Field("injuries", wrapper_class="col-12"),
                Field("injury_areas", wrapper_class="col-12"),
                css_class="row mb-2",
            ),
        )

        for fieldname in self.fields:
            self.fields[fieldname].help_text = None

    def clean(self):
        values = [
            self.cleaned_data.get("first_name"),
            self.cleaned_data.get("surname"),
            self.cleaned_data.get("age"),
            self.cleaned_data.get("injuries"),
            self.cleaned_data.get("injury_areas"),
        ]
        if not any(values):
            raise forms.ValidationError("Please fill in at least one field.")
        return self.cleaned_data
