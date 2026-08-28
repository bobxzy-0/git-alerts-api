import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from core.models import SystemSettings


@pytest.mark.django_db
def test_branding_is_public_and_has_wanlian_defaults():
    response = APIClient().get("/branding/")
    assert response.status_code == 200
    assert response.json()["brand_name"] == "万联源码泄漏监控"
    assert set(response.json()) == {"brand_name", "login_title", "home_title", "home_description"}


@pytest.mark.django_db
def test_authenticated_settings_update_changes_public_branding():
    user = User.objects.create_user(username="branding-admin", password="test-password")
    client = APIClient()
    client.force_authenticate(user)
    response = client.patch("/settings/", {
        "brand_name": "自定义源码监控",
        "login_title": "登录自定义源码监控",
        "home_title": "自定义首页",
        "home_description": "自定义页面文案",
    }, format="json")
    assert response.status_code == 200
    settings = SystemSettings.get_settings()
    assert settings.brand_name == "自定义源码监控"
    assert APIClient().get("/branding/").json()["home_description"] == "自定义页面文案"
