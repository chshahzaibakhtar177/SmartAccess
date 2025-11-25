from django.urls import path
from . import views
from . import api_views

app_name = 'transportation'

urlpatterns = [
    # Dashboard
    path('', views.transportation_dashboard, name='dashboard'),
    
    # Bus management
    path('buses/', views.bus_list, name='bus_list'),
    path('buses/create/', views.bus_create, name='bus_create'),
    path('buses/<int:pk>/', views.bus_detail, name='bus_detail'),
    path('buses/<int:pk>/edit/', views.bus_edit, name='bus_edit'),
    path('buses/<int:pk>/delete/', views.bus_delete, name='bus_delete'),
    
    # Route management
    path('routes/', views.route_list, name='route_list'),
    path('routes/create/', views.route_create, name='route_create'),
    path('routes/<int:pk>/', views.route_detail, name='route_detail'),
    path('routes/<int:pk>/edit/', views.route_edit, name='route_edit'),
    path('routes/<int:pk>/delete/', views.route_delete, name='route_delete'),
    
    # Student bus assignments
    path('assignments/', views.student_assignment_list, name='student_assignment_list'),
    path('assignments/create/', views.student_assignment_create, name='student_assignment_create'),
    path('assignments/<int:pk>/edit/', views.student_assignment_edit, name='student_assignment_edit'),
    path('assignments/<int:pk>/delete/', views.student_assignment_delete, name='student_assignment_delete'),
    
    # Transport logs
    path('logs/', views.transport_logs, name='transport_logs'),
    
    # Student dashboard
    path('student/dashboard/', views.student_transportation_dashboard, name='student_dashboard'),
    
    # Analytics
    path('analytics/', views.transportation_analytics, name='analytics'),
    
    # API endpoints
    path('api/log/', views.api_log_transport, name='api_log_transport'),
    path('api/bus/<int:bus_id>/status/', views.api_bus_status, name='api_bus_status'),
    path('api/scan/', api_views.process_bus_scan, name='api_bus_scan'),  # Raspberry Pi NFC scanner
]