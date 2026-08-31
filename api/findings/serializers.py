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

    def update(self, instance, validated_data):
        review_status = validated_data.get("review_status")
        lifecycle_map = {
            Finding.ReviewStatus.CONFIRMED: Finding.LifecycleStatus.ACKNOWLEDGED,
            Finding.ReviewStatus.FALSE_POSITIVE: Finding.LifecycleStatus.FALSE_POSITIVE,
            Finding.ReviewStatus.IGNORED: Finding.LifecycleStatus.IGNORED,
            Finding.ReviewStatus.RESOLVED: Finding.LifecycleStatus.RESOLVED,
            Finding.ReviewStatus.OPEN: Finding.LifecycleStatus.ACTIVE,
        }
        if review_status in lifecycle_map:
            validated_data["lifecycle_status"] = lifecycle_map[review_status]
        return super().update(instance, validated_data)

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
