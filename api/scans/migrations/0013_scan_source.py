from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("scans", "0012_monitorrule")]

    operations = [
        migrations.AddField(
            model_name="scan",
            name="source",
            field=models.CharField(
                choices=[("github", "GitHub"), ("gitlab", "GitLab"), ("gitee", "Gitee"), ("bitbucket", "Bitbucket"), ("codeberg", "Codeberg"), ("brave", "Brave Search")],
                default="github",
                max_length=32,
            ),
        ),
    ]
