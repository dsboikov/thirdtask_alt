from django.conf import settings
from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(blank=True, max_length=255, verbose_name="ФИО")),
                ("phone", models.CharField(
                    blank=True, max_length=16, verbose_name="Телефон",
                    validators=[django.core.validators.RegexValidator(
                        regex=r'^\+?\d{10,15}$',
                        message="Телефон должен быть в формате +71234567890 или 10–15 цифр."
                    )]
                )),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                              related_name="profile", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
