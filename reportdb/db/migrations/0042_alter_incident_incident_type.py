# Generated by Django 4.2.7 on 2023-11-26 18:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0041_alter_incident_fatality_alter_incident_spar"),
    ]

    operations = [
        migrations.AlterField(
            model_name="incident",
            name="incident_type",
            field=models.CharField(
                choices=[
                    ("YY", "Unknown"),
                    ("B", "Rockfall"),
                    ("C", "Stuck"),
                    ("D", "Lost"),
                    ("E", "Stranded"),
                    ("F", "Difficulty on rope"),
                    ("G", "Difficulty on ladder"),
                    ("H", "Equipment problems"),
                    ("I", "Hypothermia"),
                    ("J", "Lost control on rappel"),
                    ("K", "Rigging problems"),
                    ("L", "Caver fall"),
                    ("M", "Drowning"),
                    ("N", "Acetylene related"),
                    ("O", "Bad air"),
                    ("P", "Illness"),
                    ("Q", "Injury that does not fit other categories"),
                ],
                default="YY",
                help_text="The primary type of the incident.",
                max_length=2,
                verbose_name="primary type",
            ),
        ),
    ]
