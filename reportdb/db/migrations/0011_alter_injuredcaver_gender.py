# Generated by Django 4.2.3 on 2023-07-16 18:16

from django.db import migrations, models


def move_gender_to_sex(apps, schema_editor):
    injured_caver = apps.get_model("db", "InjuredCaver")
    for ic in injured_caver.objects.all():
        if ic.gender.strip() in ["Male", "Female", ""]:
            ic.sex = ic.gender.strip()
            ic.save()


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0010_remove_injuredcaver_gender_injuredcaver_sex_and_more"),
    ]

    operations = [
        migrations.RunPython(move_gender_to_sex),
    ]