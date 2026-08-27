from django.urls import path
from .views import AlertDeliveryView, NotificationChannelDetailsView, NotificationChannelView

urlpatterns = [
    path("notifications/channels/", NotificationChannelView.as_view()),
    path("notifications/channels/<int:pk>/", NotificationChannelDetailsView.as_view()),
    path("notifications/deliveries/", AlertDeliveryView.as_view()),
]
