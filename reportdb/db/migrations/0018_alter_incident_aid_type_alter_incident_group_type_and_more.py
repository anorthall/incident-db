# Generated by Django 4.2.3 on 2023-07-18 11:28

from django.db import migrations, models


def convert_source_values(apps, schema_editor):
    """
    Convert Incident.source values from U, C, P and T
    to Incident.UNKNOWN, Incident.SOURCE_CAVER, Incident.SOURCE_PARTY
    and Incident.SOURCE_THIRD_PARTY.
    """
    incident = apps.get_model("db", "Incident")
    for incident in incident.objects.all():
        if incident.source == "U":
            incident.source = "Unknown"
        elif incident.source == "C":
            incident.source = "Injured caver"
        elif incident.source == "P":
            incident.source = "Member of injured caver's party"
        elif incident.source == "T":
            incident.source = "Third party"
        incident.save()


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0017_alter_incident_county_alter_incident_group_size_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="incident",
            name="aid_type",
            field=models.CharField(
                choices=[
                    ("Unknown", "Unknown"),
                    ("None", "None"),
                    ("Surface aid", "Surface aid"),
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
        migrations.AlterField(
            model_name="incident",
            name="group_type",
            field=models.CharField(
                choices=[
                    ("Unknown", "Unknown"),
                    ("Cavers", "Cavers"),
                    ("Novice cavers", "Novice cavers"),
                    ("Cave divers", "Cave divers"),
                    ("Club or grotto cavers", "Club or grotto cavers"),
                    ("College cavers", "College cavers"),
                    ("Industrial", "Industrial (e.g. mining, construction, etc.)"),
                    ("Military", "Military"),
                    ("Other", "Other"),
                ],
                default="Cavers",
                help_text="The type of group involved in the incident.",
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="incident",
            name="source",
            field=models.CharField(
                choices=[
                    ("Unknown", "Unknown"),
                    ("Injured caver", "Injured caver"),
                    (
                        "Member of injured caver's party",
                        "Member of injured caver's party",
                    ),
                    ("Third party", "Third party"),
                ],
                default="U",
                help_text="The source of the incident information.",
                max_length=50,
            ),
        ),
        migrations.RunPython(convert_source_values),
    ]
