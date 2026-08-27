from django.contrib import admin
from .models import Scan

@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = (
        "user", "type", "value", "execution_status", "monitoring_status",
        "result_status", "created_at", "completed_at",
    )
    list_filter = (
        "user", "type", "execution_status", "monitoring_status",
        "result_status", "created_at", "completed_at",
    )
    search_fields = ("user__username", "value", "type")
    ordering = ("-created_at",)
