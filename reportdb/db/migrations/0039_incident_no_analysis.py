# Generated by Django 4.2.7 on 2023-11-19 23:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0038_remove_incident_keywords_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="incident",
            name="no_analysis",
            field=models.BooleanField(
                default=False,
                help_text="Tick this box if the original report contained no analysis.",
            ),
        ),
    ]
