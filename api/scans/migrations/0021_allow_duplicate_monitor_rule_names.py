from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("scans", "0020_alter_excludedrepository_source_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="monitorrule",
            name="unique_monitor_rule_name_per_user",
        ),
    ]
