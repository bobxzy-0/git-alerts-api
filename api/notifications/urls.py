from django.urls import path
from .views import AlertDeliveryView, EmailConfigurationView, NotificationChannelDetailsView, NotificationChannelView

urlpatterns = [
    path("notifications/channels/", NotificationChannelView.as_view()),
    path("notifications/channels/<int:pk>/", NotificationChannelDetailsView.as_view()),
    path("notifications/deliveries/", AlertDeliveryView.as_view()),
    path("notifications/email-settings/", EmailConfigurationView.as_view()),
]
