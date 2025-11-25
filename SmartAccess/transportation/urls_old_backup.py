from django.urls import path
from . import views

app_name = 'transportation'

urlpatterns = [
    # Dashboard and main views
    path('', views.transportation_dashboard, name='dashboard'),
    path('dashboard/', views.transportation_dashboard, name='dashboard'),
    
    # Bus management
    path('buses/', views.bus_management, name='bus_management'),
    path('buses/add/', views.add_bus, name='add_bus'),
    
    # Route management
    path('routes/', views.route_management, name='route_management'),
    path('routes/add/', views.add_route, name='add_route'),
    
    # Transport logs
    path('logs/', views.transport_logs, name='transport_logs'),
    
    # Analytics and reports
    path('analytics/', views.transportation_analytics, name='analytics'),
    
    # API endpoints for NFC integration
    path('api/log/', views.api_log_transport, name='api_log_transport'),
    path('api/bus/<int:bus_id>/status/', views.api_bus_status, name='api_bus_status'),
]