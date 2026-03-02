from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_alter_acauser_managers_acauser_is_staff"),
    ]

    operations = [
        migrations.AddField(
            model_name="acauser",
            name="username",
            field=models.CharField(max_length=150, blank=True, default="", verbose_name="username"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="acauser",
            name="first_name",
            field=models.CharField(
                max_length=150, blank=True, default="", verbose_name="first name"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="acauser",
            name="last_name",
            field=models.CharField(
                max_length=150, blank=True, default="", verbose_name="last name"
            ),
            preserve_default=False,
        ),
    ]
