from django.db import migrations, models


def migrate_statuses(apps, schema_editor):
    Finding = apps.get_model("findings", "Finding")
    Finding.objects.filter(review_status="NOT_AN_ISSUE").update(review_status="FALSE_POSITIVE")
    Finding.objects.filter(review_status="SKIPPED").update(review_status="IGNORED")


class Migration(migrations.Migration):
    dependencies = [("findings", "0006_finding_review_status")]

    operations = [
        migrations.RunPython(migrate_statuses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="finding",
            name="review_status",
            field=models.CharField(
                choices=[
                    ("OPEN", "Pending review"),
                    ("CONFIRMED", "Confirmed issue"),
                    ("FALSE_POSITIVE", "False positive"),
                    ("IGNORED", "Ignored"),
                    ("RESOLVED", "Resolved"),
                ],
                db_index=True,
                default="OPEN",
                max_length=24,
            ),
        ),
    ]
