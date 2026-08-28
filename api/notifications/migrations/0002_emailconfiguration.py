from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("notifications", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="EmailConfiguration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enabled", models.BooleanField(default=False)),
                ("host", models.CharField(blank=True, default="", max_length=255)),
                ("port", models.PositiveIntegerField(default=587)),
                ("username", models.CharField(blank=True, default="", max_length=255)),
                ("password_encrypted", models.TextField(blank=True, default="")),
                ("from_email", models.EmailField(blank=True, default="", max_length=254)),
                ("use_tls", models.BooleanField(default=True)),
                ("use_ssl", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="email_configuration", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
