import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("findings", "0005_finding_deduplication_lifecycle")]
    operations = [
        migrations.CreateModel(name="NotificationChannel", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=255)), ("channel_type", models.CharField(choices=[("email", "Email"), ("webhook", "Webhook")], max_length=16)),
            ("target", models.CharField(max_length=2048)), ("secret_encrypted", models.TextField(blank=True, default="")),
            ("enabled", models.BooleanField(default=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notification_channels", to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name="AlertDelivery", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("status", models.CharField(choices=[("PENDING", "Pending"), ("SENT", "Sent"), ("FAILED", "Failed")], default="PENDING", max_length=16)),
            ("scheduled_for", models.DateTimeField(db_index=True)), ("sent_at", models.DateTimeField(blank=True, null=True)),
            ("attempts", models.PositiveSmallIntegerField(default=0)), ("last_error", models.TextField(blank=True, default="")), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("channel", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="deliveries", to="notifications.notificationchannel")),
            ("finding", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="alert_deliveries", to="findings.finding")),
            ("occurrence", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="alert_deliveries", to="findings.findingoccurrence")),
        ]),
        migrations.AddConstraint(model_name="notificationchannel", constraint=models.UniqueConstraint(fields=("user", "name"), name="unique_notification_channel_name")),
        migrations.AddConstraint(model_name="alertdelivery", constraint=models.UniqueConstraint(fields=("channel", "occurrence"), name="unique_alert_per_channel_occurrence")),
    ]
