from rest_framework import serializers
from .models import Finding, IgnoreFindingType, IgnoreFindingDomain

class FindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Finding
        fields = "__all__"
        read_only_fields = [
            "repository", "type", "value", "description", "file", "line", "email",
            "commit_hash", "commit_url", "scan", "last_scan", "source", "secret_hash",
            "fingerprint", "severity", "risk_score", "first_seen_at", "last_seen_at",
            "occurrence_count", "created_at", "updated_at"
        ]

class IgnoreFindingTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IgnoreFindingType
        fields = "__all__"
        read_only_fields = ["created_at"]

class IgnoreFindingDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = IgnoreFindingDomain
        fields = "__all__"
        read_only_fields = ["created_at"]
