from django.urls import URLPattern, path
from .views import BrandingView, CodeFingerprintListCreateView, DashboardView, DetectionPatternDetailView, DetectionPatternListCreateView, SimilarityMatchListView, SourceHealthView, SystemSettingsView

urlpatterns = [
    path('settings/', SystemSettingsView.as_view(), name='settings'),
    path('branding/', BrandingView.as_view(), name='branding'),
    path('source-health/', SourceHealthView.as_view(), name='source-health'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('detection-patterns/', DetectionPatternListCreateView.as_view(), name='detection-patterns'),
    path('detection-patterns/<int:pk>/', DetectionPatternDetailView.as_view(), name='detection-pattern-detail'),
    path('code-fingerprints/', CodeFingerprintListCreateView.as_view(), name='code-fingerprints'),
    path('similarity-matches/', SimilarityMatchListView.as_view(), name='similarity-matches'),
]
