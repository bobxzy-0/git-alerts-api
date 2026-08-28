from rest_framework import serializers

from .models import AlertDelivery, EmailConfiguration, NotificationChannel
from .tasks import validate_webhook_target


class NotificationChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationChannel
        exclude = ["secret_encrypted"]
        read_only_fields = ["user", "created_at", "updated_at"]

    def validate(self, attrs):
        channel_type = attrs.get("channel_type", getattr(self.instance, "channel_type", None))
        target = attrs.get("target", getattr(self.instance, "target", ""))
        if channel_type == NotificationChannel.Types.EMAIL:
            serializers.EmailField().run_validation(target)
        elif channel_type == NotificationChannel.Types.WEBHOOK:
            try:
                validate_webhook_target(target)
            except ValueError as exc:
                raise serializers.ValidationError({"target": str(exc)}) from exc
        return attrs


class AlertDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertDelivery
        fields = "__all__"
        read_only_fields = [field.name for field in AlertDelivery._meta.fields]


class EmailConfigurationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password_configured = serializers.SerializerMethodField()

    class Meta:
        model = EmailConfiguration
        exclude = ["password_encrypted"]
        read_only_fields = ["user", "created_at", "updated_at", "password_configured"]

    def get_password_configured(self, obj):
        return bool(obj.password_encrypted)

    def validate(self, attrs):
        if attrs.get("use_tls", getattr(self.instance, "use_tls", True)) and attrs.get("use_ssl", getattr(self.instance, "use_ssl", False)):
            raise serializers.ValidationError("TLS and SSL cannot both be enabled.")
        enabled = attrs.get("enabled", getattr(self.instance, "enabled", False))
        if enabled:
            required = {
                "host": attrs.get("host", getattr(self.instance, "host", "")),
                "from_email": attrs.get("from_email", getattr(self.instance, "from_email", "")),
            }
            missing = [field for field, value in required.items() if not value]
            if missing:
                raise serializers.ValidationError({field: "This field is required when SMTP is enabled." for field in missing})
        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop("password", "")
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save(update_fields=["password_encrypted", "updated_at"])
        return instance
