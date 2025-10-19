from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.dashboard_home, name='dashboard_home'),
    path('operations/', views.operations_dashboard, name='operations_dashboard'),
    path('supervisor/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('executive/', views.executive_dashboard, name='executive_dashboard'),
    path('safety/', views.safety_dashboard, name='safety_dashboard'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    
    # Authentication
    path('login/', views.custom_login, name='login'),
    
    # API endpoints
    path('api/live-events/', views.api_live_events, name='api_live_events'),
    path('api/alerts/', views.api_alerts, name='api_alerts'),
    path('api/cv-detections/', views.api_cv_detections, name='api_cv_detections'),
    path('api/site-map/', views.api_site_map, name='api_site_map'),
    path('api/dashboard-stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
    
    # Report downloads
    path('download/shift-report/<str:format_type>/', views.download_shift_report, name='download_shift_report'),
    path('download/analytics-report/<str:format_type>/', views.download_analytics_report, name='download_analytics_report'),
]