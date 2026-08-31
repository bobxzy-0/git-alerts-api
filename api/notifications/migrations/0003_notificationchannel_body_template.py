from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0002_emailconfiguration"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificationchannel",
            name="body_template",
            field=models.TextField(blank=True, default=""),
        ),
    ]
