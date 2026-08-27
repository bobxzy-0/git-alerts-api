from django.urls import path
from .views import (
    MonitorRuleDetailsView,
    MonitorRuleView,
    ExcludedRepositoryDetailsView,
    ExcludedRepositoryView,
    MonitoringProfileDetailsView,
    MonitoringProfileView,
    ScanDetailsView,
    ScanFindingsView,
    ScanRepositoryView,
    ScanView,
)

urlpatterns = [
    path('scans/', ScanView.as_view(), name='scan'),
    path('scans/<int:pk>/', ScanDetailsView.as_view(), name='scan-details'),
    path('scans/<int:pk>/findings/', ScanFindingsView.as_view(), name='scan-findings'),
    path('scans/<int:pk>/repositories/', ScanRepositoryView.as_view(), name='scan-repositories'),
    path('monitor-rules/', MonitorRuleView.as_view(), name='monitor-rule'),
    path('monitor-rules/<int:pk>/', MonitorRuleDetailsView.as_view(), name='monitor-rule-details'),
    path('monitoring-profiles/', MonitoringProfileView.as_view(), name='monitoring-profile'),
    path('monitoring-profiles/<int:pk>/', MonitoringProfileDetailsView.as_view(), name='monitoring-profile-details'),
    path('excluded-repositories/', ExcludedRepositoryView.as_view(), name='excluded-repository'),
    path('excluded-repositories/<int:pk>/', ExcludedRepositoryDetailsView.as_view(), name='excluded-repository-details'),
]
