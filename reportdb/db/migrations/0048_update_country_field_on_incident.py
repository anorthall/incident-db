# Generated by Django 5.0.4 on 2024-04-27 12:11

from django.db import migrations

from db.choices import Countries


def update_country_on_incident(apps, _):
    incident = apps.get_model("db", "Incident")
    index = {v: k for k, v in Countries.choices}

    for count, i in enumerate(incident.objects.all()):
        process_country(index, i)

    print(f"Processed {count} incidents")


def process_country(index, i):
    country = i.country

    if not country:
        return

    if country == "United States" or country == "USA" or country == "US":
        i.country = Countries.US
        i.save()
        return

    if country in index:
        i.country = index[country]
        i.save()
        return

    if country in Countries:
        i.country = country
        i.save()
        return

    print(i.id, country)
    raise ValueError(f"Could not find country for {country}")


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0047_alter_cave_country_alter_incident_country_and_more'),
    ]

    operations = [
        migrations.RunPython(update_country_on_incident)
    ]
