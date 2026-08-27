from django.contrib import admin
from .models import CodeFingerprint, DetectionPattern, RepoScanHistory, SimilarityMatch, SourceHealth, SystemSettings

admin.site.register(RepoScanHistory)
admin.site.register(SystemSettings)
admin.site.register(SourceHealth)
admin.site.register(DetectionPattern)
admin.site.register(CodeFingerprint)
admin.site.register(SimilarityMatch)
