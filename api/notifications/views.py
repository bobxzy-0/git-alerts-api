from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import AlertDelivery, EmailConfiguration, NotificationChannel
from .serializers import AlertDeliverySerializer, EmailConfigurationSerializer, NotificationChannelSerializer
from .tasks import send_test_notification


class NotificationChannelView(generics.ListCreateAPIView):
    serializer_class = NotificationChannelSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self): return NotificationChannel.objects.filter(user=self.request.user)
    def perform_create(self, serializer): serializer.save(user=self.request.user)


class NotificationChannelDetailsView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NotificationChannelSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self): return NotificationChannel.objects.filter(user=self.request.user)


class NotificationChannelTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        channel = get_object_or_404(NotificationChannel, pk=pk, user=request.user)
        try:
            send_test_notification(channel)
        except Exception as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY
            )
        return Response({"message": "Test notification sent."})


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
