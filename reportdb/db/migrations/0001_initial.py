# Generated by Django 4.2.1 on 2023-05-18 05:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Publication",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                (
                    "pdf_file",
                    models.FileField(upload_to="reports/pdf", verbose_name="PDF file"),
                ),
                ("text_file", models.FileField(upload_to="reports/txt")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Incident",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "date",
                    models.DateField(
                        help_text="The date that the incident occurred. If you do not know the exact date, use the first of the month, or year, then tick 'Approximate date'."
                    ),
                ),
                (
                    "approximate_date",
                    models.BooleanField(
                        default=False,
                        help_text="Tick this box if the date above is approximate.",
                    ),
                ),
                (
                    "publication_page",
                    models.IntegerField(
                        help_text="The page number that this incident appeared on in the publication. This should be taken from the page number in the corner of the PDF."
                    ),
                ),
                (
                    "cave",
                    models.CharField(
                        help_text="If not known, enter 'unknown'.", max_length=100
                    ),
                ),
                (
                    "state",
                    models.CharField(
                        help_text="Use the full name of the state.", max_length=50
                    ),
                ),
                (
                    "county",
                    models.CharField(
                        blank=True,
                        help_text="Use the full name of the county. Can be left blank.",
                        max_length=50,
                    ),
                ),
                (
                    "country",
                    models.CharField(
                        default="USA",
                        help_text="Use 'USA', not 'United States of America'.",
                        max_length=50,
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("Caving", "Caving"),
                            ("Caving related", "Caving related"),
                            ("Cave diving", "Cave diving"),
                            ("Other", "Other"),
                        ],
                        default="Caving",
                        help_text="Select the category that best describes the incident.",
                        max_length=50,
                    ),
                ),
                (
                    "incident_type",
                    models.CharField(
                        help_text="Describe the type of incident. E.g. 'fall', 'drowning', etc.",
                        max_length=100,
                    ),
                ),
                (
                    "primary_cause",
                    models.CharField(
                        help_text="Briefly describe the primary cause of the incident, for example 'inadequate equipment', 'inexperience', 'poor judgement', etc.",
                        max_length=200,
                    ),
                ),
                (
                    "secondary_cause",
                    models.CharField(
                        blank=True,
                        help_text="Briefly describe the secondary cause of the incident. Can be left blank.",
                        max_length=200,
                    ),
                ),
                (
                    "caver_first_name",
                    models.CharField(
                        blank=True,
                        help_text="The first name of the injured caver. Can be left blank.",
                        max_length=100,
                    ),
                ),
                (
                    "caver_surname",
                    models.CharField(
                        blank=True,
                        help_text="The surname of the injured caver. Can be left blank.",
                        max_length=100,
                    ),
                ),
                (
                    "caver_age",
                    models.IntegerField(
                        blank=True,
                        help_text="The age of the injured caver at the time of the incident. Can be left blank.",
                        null=True,
                    ),
                ),
                (
                    "caver_gender",
                    models.CharField(
                        blank=True,
                        help_text="The gender of the injured caver. Can be left blank.",
                        max_length=10,
                    ),
                ),
                (
                    "caver_injuries",
                    models.CharField(
                        blank=True,
                        help_text="The injuries sustained by the injured caver. Can be left blank.",
                        max_length=200,
                    ),
                ),
                (
                    "caver_injury_areas",
                    models.CharField(
                        blank=True,
                        help_text="The areas of the body that were injured. Can be left blank.",
                        max_length=200,
                    ),
                ),
                (
                    "group_type",
                    models.CharField(
                        choices=[
                            ("Cavers", "Cavers"),
                            ("Novice cavers", "Novice cavers"),
                            ("Cave divers", "Cave divers"),
                            ("Club or grotto cavers", "Club or grotto cavers"),
                            ("College cavers", "College cavers"),
                            (
                                "Industrial",
                                "Industrial (e.g. mining, construction, etc.)",
                            ),
                            ("Military", "Military"),
                            ("Other", "Other"),
                        ],
                        default="Cavers",
                        help_text="The type of group involved in the incident.",
                        max_length=50,
                    ),
                ),
                (
                    "group_size",
                    models.IntegerField(
                        blank=True,
                        help_text="The number of people involved in the incident, excluding any rescue or aid teams. Can be left blank.",
                        null=True,
                    ),
                ),
                (
                    "aid_type",
                    models.CharField(
                        choices=[
                            ("None", "None"),
                            ("Surface aid only", "Surface aid only"),
                            ("Underground aid", "Underground aid"),
                            ("Body recovery", "Body recovery"),
                            ("Aid on standby", "Aid on standby"),
                            ("Other", "Other"),
                        ],
                        default="None",
                        help_text="The type of aid required.",
                        max_length=100,
                    ),
                ),
                (
                    "fatality",
                    models.BooleanField(
                        default=False,
                        help_text="Tick this box if somebody died as a result of this incident. This will also automatically tick the injury box.",
                    ),
                ),
                (
                    "injury",
                    models.BooleanField(
                        default=False,
                        help_text="Tick this box if somebody was injured as a result of this incident.",
                    ),
                ),
                (
                    "multiple_incidents",
                    models.BooleanField(
                        default=False,
                        help_text="Tick this box if there were multiple incidents, e.g. several falls.",
                    ),
                ),
                (
                    "multiple_people_involved",
                    models.BooleanField(
                        default=False,
                        help_text="Tick this box if there were multiple people involved in the incident.",
                    ),
                ),
                (
                    "rescue_over_24_hours",
                    models.BooleanField(
                        default=False,
                        help_text="Tick this box if the rescue took over 24 hours.",
                        verbose_name="Rescue duration over 24 hours",
                    ),
                ),
                (
                    "vertical",
                    models.BooleanField(
                        default=False,
                        help_text="Tick this box if the incident involved vertical caving.",
                        verbose_name="Vertical incident",
                    ),
                ),
                (
                    "spar",
                    models.BooleanField(
                        default=False,
                        help_text="Tick this box if SPAR techniques were used.",
                        verbose_name="SPAR",
                    ),
                ),
                (
                    "original_text",
                    models.TextField(
                        blank=True,
                        help_text="The original text of the incident from NSS News.",
                    ),
                ),
                (
                    "notes",
                    models.TextField(
                        blank=True, help_text="Any additional notes about the incident."
                    ),
                ),
                (
                    "references",
                    models.TextField(
                        blank=True,
                        help_text="Any references to other sources of information.",
                    ),
                ),
                (
                    "editing_notes",
                    models.TextField(
                        blank=True,
                        help_text="Notes that will be visible only to people editing this incident on this website. For example: 'need to find the exact date of this incident'.",
                    ),
                ),
                (
                    "completed",
                    models.BooleanField(
                        default=False,
                        help_text="Tick this box if all available data has been entered for this incident.",
                    ),
                ),
                (
                    "approved",
                    models.BooleanField(
                        default=False,
                        help_text="Tick this box if you have reviewed the data for this incident and are satisfied that it is correct and ready for publication.",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "publication",
                    models.ForeignKey(
                        help_text="The publication that this incident appeared in.",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="db.publication",
                    ),
                ),
            ],
        ),
    ]