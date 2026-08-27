import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from core.models import CodeFingerprint, SimilarityMatch
from core.similarity import build_fingerprint, minhash_similarity, simhash_similarity


def test_identical_content_has_exact_simhash_and_minhash_similarity():
    left = build_fingerprint("def calculate_total(items):\n    return sum(items)\n")
    right = build_fingerprint("def calculate_total(items):\n    return sum(items)\n")
    assert simhash_similarity(left["simhash"], right["simhash"]) == 1
    assert minhash_similarity(left["minhash"], right["minhash"]) == 1


def test_small_code_change_remains_similar():
    left = build_fingerprint("def calculate_total(items): return sum(items)")
    right = build_fingerprint("def calculate_total(values): return sum(values)")
    assert simhash_similarity(left["simhash"], right["simhash"]) > 0.7


@pytest.mark.django_db
def test_candidate_creates_match_without_storing_source_content():
    user = User.objects.create_user(username="similarity-user")
    client = APIClient()
    client.force_authenticate(user)
    content = "class InternalBillingEngine:\n    def calculate_invoice(self, account): return account.total\n"
    baseline = client.post("/code-fingerprints/", {
        "name": "billing baseline", "kind": "BASELINE", "content": content,
        "authorization_confirmed": True,
    }, format="json")
    candidate = client.post("/code-fingerprints/", {
        "name": "public candidate", "kind": "CANDIDATE", "content": content,
        "source_repository": "https://github.com/example/leak", "authorization_confirmed": True,
    }, format="json")
    assert baseline.status_code == 201
    assert candidate.status_code == 201
    assert "content" not in candidate.json()
    assert SimilarityMatch.objects.get(user=user).combined_score == 1
    model_fields = {field.name for field in CodeFingerprint._meta.fields}
    assert "content" not in model_fields


@pytest.mark.django_db
def test_fingerprint_requires_explicit_authorization_confirmation():
    user = User.objects.create_user(username="similarity-unauthorized")
    client = APIClient()
    client.force_authenticate(user)
    response = client.post("/code-fingerprints/", {
        "name": "blocked", "kind": "BASELINE", "content": "secret source",
        "authorization_confirmed": False,
    }, format="json")
    assert response.status_code == 400
    assert CodeFingerprint.objects.count() == 0
