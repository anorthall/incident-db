# Generated by Django 5.0.4 on 2024-04-27 12:25

from django.db import migrations, models


def update_incident_category(apps, _):
    incident = apps.get_model("db", "Incident")

    for i in incident.objects.all():
        print(i)
        match i.category:
            case "YY":
                i.category = ""
            case "CA":
                i.category = "CAVE"
            case "CD":
                i.category = "DIVING"
            case "CR":
                i.category = "OTHER"
            case "ZZ":
                i.category = "OTHER"
            case _:
                raise ValueError(f"Unknown category: {i.category}")
        i.save()


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0049_check_us_state_again'),
    ]

    operations = [
        migrations.AlterField(
            model_name='incident',
            name='category',
            field=models.CharField(blank=True, choices=[('CAVE', 'Cave'), ('DIVING', 'Cave Diving'), ('MINE', 'Mine'), ('OTHER', 'Other')], help_text='Select the category that best describes the incident.', max_length=10),
        ),
        migrations.RunPython(update_incident_category),
    ]
