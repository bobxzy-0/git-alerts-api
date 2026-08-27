from rest_framework import serializers

from .models import AlertDelivery, NotificationChannel
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
