from django.contrib import admin
from .models import AlertDelivery, NotificationChannel

admin.site.register(NotificationChannel)
admin.site.register(AlertDelivery)
