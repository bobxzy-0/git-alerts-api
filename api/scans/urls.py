from django.urls import path
from .views import (
    MonitorRuleDetailsView,
    MonitorRuleView,
    MonitoringProfileDetailsView,
    MonitoringProfileView,
    ScanDetailsView,
    ScanFindingsView,
    ScanView,
)

urlpatterns = [
    path('scans/', ScanView.as_view(), name='scan'),
    path('scans/<int:pk>/', ScanDetailsView.as_view(), name='scan-details'),
    path('scans/<int:pk>/findings/', ScanFindingsView.as_view(), name='scan-findings'),
    path('monitor-rules/', MonitorRuleView.as_view(), name='monitor-rule'),
    path('monitor-rules/<int:pk>/', MonitorRuleDetailsView.as_view(), name='monitor-rule-details'),
    path('monitoring-profiles/', MonitoringProfileView.as_view(), name='monitoring-profile'),
    path('monitoring-profiles/<int:pk>/', MonitoringProfileDetailsView.as_view(), name='monitoring-profile-details'),
]
