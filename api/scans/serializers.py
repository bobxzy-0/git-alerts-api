from rest_framework import serializers
from .models import ExcludedRepository, MonitorRule, MonitoringProfile, Scan, ScanRepository, SourceType
from .services.monitoring_profiles import sync_profile_rules
from integrations.models import UserIntegration

class ScanSerializer(serializers.ModelSerializer):
    """Serializer for scan model with user validation"""
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Scan
        fields = "__all__"
        read_only_fields = [
            "user", "execution_status", "monitoring_status", "result_status",
            "error_code", "error_message",
            "total_repositories", "total_findings",
            "ignored_repositories", "ignored_findings",
            "scanned_repositories",
            "created_at", "updated_at", "started_at", "completed_at"
        ]

    def validate_source(self, value):
        if value not in {SourceType.GITHUB, SourceType.GITLAB, SourceType.GITEE, SourceType.BRAVE}:
            raise serializers.ValidationError("This source adapter is not enabled yet.")
        return value
    
    def validate(self, attrs):
        """Validate that no duplicate active scan exists for the same type and value"""
        user = self.context["request"].user
        type = attrs.get("type")
        value = attrs.get("value")

        source = attrs.get("source", SourceType.GITHUB)
        scan_type = attrs.get("type")
        if source == SourceType.BRAVE and scan_type != Scan.ScanTypes.SEARCH_REPOS:
            raise serializers.ValidationError("Brave Search supports search_repos rules only.")
        integration = UserIntegration.objects.filter(
            user=user,
            provider=source,
        ).first()

        if not integration or integration.status != UserIntegration.Status.CONNECTED:
            raise serializers.ValidationError(
                f"{source.title()} integration is not connected. Please connect via /integrations/ first"
            )

        is_scan_exists = Scan.objects.filter(
            user=user,
            type=type,
            value=value,
            execution_status__in=[
                Scan.ExecutionStatus.QUEUED,
                Scan.ExecutionStatus.RUNNING,
            ]
        ).exists()
        
        if is_scan_exists:
            raise serializers.ValidationError(
                "A scan for this target already queued or in progress."
            )
        
        return attrs


class MonitorRuleSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = MonitorRule
        fields = "__all__"
        read_only_fields = [
            "user", "last_run_at", "next_run_at", "is_running", "locked_at",
            "last_scan", "created_at", "updated_at",
        ]

    def validate_source(self, value):
        if value not in {SourceType.GITHUB, SourceType.GITLAB, SourceType.GITEE, SourceType.BRAVE}:
            raise serializers.ValidationError(
                "This source is reserved for a later adapter phase and is not enabled yet."
            )
        return value

    def validate(self, attrs):
        if attrs.get("source", SourceType.GITHUB) == SourceType.BRAVE and attrs.get("scan_type") != Scan.ScanTypes.SEARCH_REPOS:
            raise serializers.ValidationError("Brave Search supports search_repos rules only.")
        return attrs


class MonitoringProfileSerializer(serializers.ModelSerializer):
    generated_rule_count = serializers.IntegerField(source="rules.count", read_only=True)

    class Meta:
        model = MonitoringProfile
        fields = "__all__"
        read_only_fields = ["user", "created_at", "updated_at", "generated_rule_count"]

    def validate(self, attrs):
        list_fields = ("domains", "email_domains", "brands", "product_names", "internal_projects", "internal_domains", "github_orgs", "gitlab_groups", "custom_keywords")
        for field in list_fields:
            if field in attrs and (not isinstance(attrs[field], list) or not all(isinstance(item, str) for item in attrs[field])):
                raise serializers.ValidationError({field: "Must be a list of strings."})
        return attrs

    def create(self, validated_data):
        profile = MonitoringProfile.objects.create(user=self.context["request"].user, **validated_data)
        sync_profile_rules(profile)
        return profile

    def update(self, instance, validated_data):
        profile = super().update(instance, validated_data)
        sync_profile_rules(profile)
        return profile


class ExcludedRepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExcludedRepository
        fields = "__all__"
        read_only_fields = ["user", "normalized_url", "created_at", "updated_at"]

    def validate(self, attrs):
        from .services.repositories import normalize_repository_url
        user = self.context["request"].user
        source = attrs.get("source", getattr(self.instance, "source", None))
        repository_url = attrs.get("repository_url", getattr(self.instance, "repository_url", ""))
        queryset = ExcludedRepository.objects.filter(
            user=user, source=source,
            normalized_url=normalize_repository_url(repository_url),
        )
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("This repository is already in the permanent exclusion list.")
        return attrs


class ScanRepositorySerializer(serializers.ModelSerializer):
    is_permanently_excluded = serializers.SerializerMethodField()

    class Meta:
        model = ScanRepository
        fields = "__all__"
        read_only_fields = [field.name for field in ScanRepository._meta.fields]

    def get_is_permanently_excluded(self, obj):
        return ExcludedRepository.objects.filter(
            user=obj.scan.user, source=obj.source,
            normalized_url=obj.normalized_url, enabled=True,
        ).exists()
