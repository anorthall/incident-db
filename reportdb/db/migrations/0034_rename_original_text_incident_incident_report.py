# Generated by Django 4.2.7 on 2023-11-18 11:30

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0033_incident_data_input_source"),
    ]

    operations = [
        migrations.RenameField(
            model_name="incident",
            old_name="original_text",
            new_name="incident_report",
        ),
    ]