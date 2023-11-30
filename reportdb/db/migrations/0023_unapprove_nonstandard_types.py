# Generated by Django 4.2.3 on 2023-07-22 16:43

from django.db import migrations


def unapprove_non_standard_types(apps, schema_editor):
    incident = apps.get_model("db", "Incident")
    standard_types = [
        "Rockfall",
        "Stuck",
        "Lost",
        "Stranded",
        "Difficulty on rope",
        "Equipment problems",
        "Hypothermia",
        "Lost control on rappel",
        "Rigging problems",
        "Caver fall",
        "Drowning",
        "Acetylene related",
        "Bad air",
        "Illness",
        "Other",
    ]

    incident.objects.all().exclude(incident_type__in=standard_types).update(
        approved=False, completed=False
    )


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0022_alter_incident_incident_type_and_more"),
    ]

    operations = [
        migrations.RunPython(unapprove_non_standard_types),
    ]
