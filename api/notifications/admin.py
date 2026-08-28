from django.contrib import admin
from .models import AlertDelivery, EmailConfiguration, NotificationChannel

admin.site.register(NotificationChannel)
admin.site.register(EmailConfiguration)
admin.site.register(AlertDelivery)
