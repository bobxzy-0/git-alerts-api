from rest_framework import serializers
import re

from .models import CodeFingerprint, DetectionPattern, SimilarityMatch, SourceHealth, SystemSettings
from .similarity import build_fingerprint, minhash_similarity, simhash_similarity


class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = [
            "brand_name", "login_title", "home_title", "home_description",
            "skip_recent_days", "verified_only", "org_repos_only", "updated_at",
        ]
        read_only_fields = ["updated_at"]


class BrandingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = ["brand_name", "login_title", "home_title", "home_description"]
        read_only_fields = fields


class SourceHealthSerializer(serializers.ModelSerializer):
    integration_status = serializers.SerializerMethodField()
    configured = serializers.SerializerMethodField()

    class Meta:
        model = SourceHealth
        fields = "__all__"
        read_only_fields = [field.name for field in SourceHealth._meta.fields]

    def _integration(self, obj):
        from integrations.models import UserIntegration
        return UserIntegration.objects.filter(user=obj.user, provider=obj.source).first()

    def get_integration_status(self, obj):
        integration = self._integration(obj)
        return integration.status if integration else "not_configured"

    def get_configured(self, obj):
        return self._integration(obj) is not None


class DetectionPatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectionPattern
        fields = "__all__"
        read_only_fields = ["user", "created_at", "updated_at"]

    def validate_pattern(self, value):
        try:
            re.compile(value)
        except re.error as exc:
            raise serializers.ValidationError(f"Invalid regular expression: {exc}") from exc
        return value


class CodeFingerprintSerializer(serializers.ModelSerializer):
    content = serializers.CharField(write_only=True, max_length=5_000_000)
    authorization_confirmed = serializers.BooleanField(write_only=True)

    class Meta:
        model = CodeFingerprint
        fields = "__all__"
        read_only_fields = ["user", "content_sha256", "token_count", "simhash", "minhash", "tlsh", "created_at"]

    def validate_authorization_confirmed(self, value):
        if not value:
            raise serializers.ValidationError("You must confirm authorization to fingerprint this code.")
        return value

    def create(self, validated_data):
        content = validated_data.pop("content")
        validated_data.pop("authorization_confirmed")
        fingerprint = CodeFingerprint.objects.create(
            user=self.context["request"].user, **validated_data, **build_fingerprint(content)
        )
        if fingerprint.kind == CodeFingerprint.Kind.CANDIDATE:
            for baseline in CodeFingerprint.objects.filter(user=fingerprint.user, kind=CodeFingerprint.Kind.BASELINE):
                sim_score = simhash_similarity(baseline.simhash, fingerprint.simhash)
                min_score = minhash_similarity(baseline.minhash, fingerprint.minhash)
                combined = (sim_score + min_score) / 2
                if combined >= 0.5:
                    SimilarityMatch.objects.create(
                        user=fingerprint.user, baseline=baseline, candidate=fingerprint,
                        simhash_score=sim_score, minhash_score=min_score, combined_score=combined,
                    )
        return fingerprint


class SimilarityMatchSerializer(serializers.ModelSerializer):
    baseline_name = serializers.CharField(source="baseline.name", read_only=True)
    candidate_name = serializers.CharField(source="candidate.name", read_only=True)

    class Meta:
        model = SimilarityMatch
        fields = "__all__"
        read_only_fields = [field.name for field in SimilarityMatch._meta.fields]
