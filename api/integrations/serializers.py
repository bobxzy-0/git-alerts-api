from urllib.parse import urlparse

from rest_framework import serializers

from .models import UserIntegration


class UserIntegrationSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating an integration token"""
    user = serializers.CharField(source="user.username", read_only=True)
    token = serializers.CharField(write_only=True)
    proxy_url = serializers.CharField(write_only=True, required=False, allow_blank=True)
    proxy_configured = serializers.SerializerMethodField()
    proxy_scheme = serializers.SerializerMethodField()

    class Meta:
        model = UserIntegration
        fields = [
            "id", "user", "provider", "token", "proxy_url", "proxy_configured", "proxy_scheme", "status",
            "last_validated_at", "error_message",
            "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "user", "status", "proxy_configured", "proxy_scheme",
            "last_validated_at", "error_message",
            "created_at", "updated_at"
        ]

    def validate(self, attrs):
        token = attrs.get("token")

        if not token or len(token) < 10:
            raise serializers.ValidationError("Invalid token provided")
        proxy_url = attrs.get("proxy_url", "")
        if proxy_url:
            parsed = urlparse(proxy_url)
            try:
                port = parsed.port
            except ValueError:
                port = None
            if parsed.scheme not in {"http", "https", "socks5", "socks5h"} or not parsed.hostname or port is None:
                raise serializers.ValidationError({"proxy_url": "Use http, https, socks5, or socks5h with host and port."})
        
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        provider = validated_data["provider"]
        token = validated_data["token"]
        proxy_url = validated_data.get("proxy_url")

        obj, _ = UserIntegration.objects.get_or_create(
            user=user,
            provider=provider,
        )
        obj.set_token(token)
        if proxy_url is not None:
            obj.set_proxy_url(proxy_url)
        obj.save()
        
        return obj

    def get_proxy_configured(self, obj):
        return bool(obj.proxy_url_encrypted)

    def get_proxy_scheme(self, obj):
        return urlparse(obj.get_proxy_url()).scheme if obj.proxy_url_encrypted else ""
