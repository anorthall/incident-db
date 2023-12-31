# Generated by Django 4.2.7 on 2023-11-18 11:46

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0036_rename_notes_incident_incident_notes_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="incident",
            name="incident_summary",
            field=models.TextField(
                blank=True,
                help_text="A short summary of the incident. Maximum 400 characters.",
                max_length=400,
            ),
        ),
    ]
