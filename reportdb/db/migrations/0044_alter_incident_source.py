# Generated by Django 4.2.7 on 2023-11-27 17:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0043_incident_original_text"),
    ]

    operations = [
        migrations.AlterField(
            model_name="incident",
            name="source",
            field=models.CharField(
                choices=[
                    ("YY", "Unknown"),
                    ("CA", "Injured caver"),
                    ("PA", "Member of injured caver's party"),
                    ("RE", "Member of rescue party"),
                    ("TH", "Third party"),
                ],
                default="YY",
                help_text="The source of the incident information.",
                max_length=2,
            ),
        ),
    ]
