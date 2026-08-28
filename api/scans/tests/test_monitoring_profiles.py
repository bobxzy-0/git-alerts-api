import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from scans.models import MonitorRule, MonitoringProfile


@pytest.mark.django_db
def test_profile_generates_platform_and_search_rules():
    user = User.objects.create_user(username="profile-user")
    client = APIClient()
    client.force_authenticate(user)
    response = client.post("/monitoring-profiles/", {
        "name": "Acme", "company_name": "Acme Corp", "domains": ["acme.example"],
        "github_orgs": ["acme"], "gitlab_groups": ["acme/platform"],
        "custom_keywords": ["project falcon"], "interval_minutes": 30,
    }, format="json")
    assert response.status_code == 201
    profile = MonitoringProfile.objects.get(user=user)
    rules = profile.rules.order_by("source", "value")
    assert rules.count() == 5
    assert set(rules.values_list("source", flat=True)) == {"github", "gitlab", "brave"}
    assert all(rules.values_list("auto_generated", flat=True))


@pytest.mark.django_db
def test_profile_schedule_is_copied_to_generated_rules():
    user = User.objects.create_user(username="profile-schedule")
    client = APIClient()
    client.force_authenticate(user)
    response = client.post("/monitoring-profiles/", {
        "name": "Weekdays", "github_orgs": ["acme"],
        "schedule_kind": "WEEKLY", "schedule_time": "08:15",
        "schedule_weekdays": [0, 2, 4],
    }, format="json")
    assert response.status_code == 201
    rule = MonitoringProfile.objects.get(user=user).rules.get()
    assert rule.schedule_kind == MonitorRule.ScheduleKinds.WEEKLY
    assert rule.schedule_weekdays == [0, 2, 4]


@pytest.mark.django_db
def test_profile_update_replaces_generated_rules_without_duplicates():
    user = User.objects.create_user(username="profile-update")
    profile = MonitoringProfile.objects.create(user=user, name="Acme", github_orgs=["old"])
    MonitorRule.objects.create(user=user, profile=profile, auto_generated=True, name="old rule", source="github", scan_type="org_repos", value="old")
    manual = MonitorRule.objects.create(user=user, name="manual", source="github", scan_type="org_repos", value="keep")
    client = APIClient()
    client.force_authenticate(user)
    response = client.patch(f"/monitoring-profiles/{profile.pk}/", {"github_orgs": ["new", "new"]}, format="json")
    assert response.status_code == 200
    assert list(profile.rules.values_list("value", flat=True)) == ["new"]
    assert MonitorRule.objects.filter(pk=manual.pk).exists()


@pytest.mark.django_db
def test_profile_rejects_non_string_list_values():
    user = User.objects.create_user(username="profile-invalid")
    client = APIClient()
    client.force_authenticate(user)
    response = client.post("/monitoring-profiles/", {"name": "Invalid", "domains": [123]}, format="json")
    assert response.status_code == 400
