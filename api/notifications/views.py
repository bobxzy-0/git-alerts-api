from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import AlertDelivery, EmailConfiguration, NotificationChannel
from .serializers import AlertDeliverySerializer, EmailConfigurationSerializer, NotificationChannelSerializer


class NotificationChannelView(generics.ListCreateAPIView):
    serializer_class = NotificationChannelSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self): return NotificationChannel.objects.filter(user=self.request.user)
    def perform_create(self, serializer): serializer.save(user=self.request.user)


class NotificationChannelDetailsView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NotificationChannelSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self): return NotificationChannel.objects.filter(user=self.request.user)


class AlertDeliveryView(generics.ListAPIView):
    serializer_class = AlertDeliverySerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self): return AlertDelivery.objects.filter(channel__user=self.request.user)


class EmailConfigurationView(generics.RetrieveUpdateAPIView):
    serializer_class = EmailConfigurationSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        obj, _ = EmailConfiguration.objects.get_or_create(user=self.request.user)
        return obj
