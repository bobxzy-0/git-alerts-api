from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("findings", "0005_finding_deduplication_lifecycle"),
    ]

    operations = [
        migrations.AddField(
            model_name="finding",
            name="review_status",
            field=models.CharField(
                choices=[
                    ("OPEN", "Open / Pending review"),
                    ("CONFIRMED", "Confirmed issue"),
                    ("NOT_AN_ISSUE", "Not an issue"),
                    ("IGNORED", "Ignored"),
                    ("SKIPPED", "Skipped for now"),
                ],
                db_index=True,
                default="OPEN",
                max_length=24,
            ),
        ),
    ]
