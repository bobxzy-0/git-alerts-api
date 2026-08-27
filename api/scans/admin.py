from django.contrib import admin
from .models import MonitorRule, MonitoringProfile, RepositoryScanQueue, Scan

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


@admin.register(MonitorRule)
class MonitorRuleAdmin(admin.ModelAdmin):
    list_display = (
        "name", "user", "source", "scan_type", "interval_minutes", "enabled",
        "is_running", "last_run_at", "next_run_at",
    )
    list_filter = ("enabled", "source", "scan_type", "interval_minutes", "is_running")
    search_fields = ("name", "value", "user__username")


@admin.register(RepositoryScanQueue)
class RepositoryScanQueueAdmin(admin.ModelAdmin):
    list_display = ("source", "owner", "repository", "status", "discovery_scan", "scan", "created_at")
    list_filter = ("source", "status")
    search_fields = ("repository_url", "owner", "repository", "user__username")


@admin.register(MonitoringProfile)
class MonitoringProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "enabled", "interval_minutes", "updated_at")
    list_filter = ("enabled", "interval_minutes")
