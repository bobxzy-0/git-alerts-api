from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0009_codefingerprint_similaritymatch")]

    operations = [
        migrations.AddField(model_name="systemsettings", name="brand_name", field=models.CharField(default="万联源码泄漏监控", max_length=120)),
        migrations.AddField(model_name="systemsettings", name="login_title", field=models.CharField(default="登录万联源码泄漏监控", max_length=160)),
        migrations.AddField(model_name="systemsettings", name="home_title", field=models.CharField(default="万联源码泄漏监控", max_length=160)),
        migrations.AddField(model_name="systemsettings", name="home_description", field=models.CharField(default="持续监控公开代码平台，发现源码与敏感信息泄漏风险", max_length=500)),
    ]
