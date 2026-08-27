from django.contrib import admin
from .models import Finding, FindingOccurrence, IgnoreFindingType, IgnoreFindingDomain

@admin.register(Finding)
class FindingAdmin(admin.ModelAdmin):
    list_display = (
        "type", "severity", "lifecycle_status", "repository", "validated",
        "occurrence_count", "first_seen_at", "last_seen_at",
    )
    list_filter = ("severity", "lifecycle_status", "source", "validated", "created_at")
    search_fields = ("repository", "email", "description", "value", "commit_hash")
    ordering = ("-created_at",)

admin.site.register(IgnoreFindingType)
admin.site.register(IgnoreFindingDomain)
admin.site.register(FindingOccurrence)
