from django.urls import path
from . import views

# Attendance app URLs - delegating to imported views from student app
urlpatterns = [
    path('logs/', views.view_logs, name='view_logs'),
    path('logs/export/', views.export_logs_csv, name='export_logs_csv'),
    path('reports/', views.generate_attendance_report, name='generate_attendance_report'),
    path('analytics/', views.attendance_analytics, name='attendance_analytics'),
    path('simulate/', views.simulate_card_scan, name='simulate_card_scan'),
    path('student/<int:student_id>/', views.student_detail, name='student_detail'),
    path('api/nfc-scan/', views.nfc_scan_api, name='nfc_scan_api'),
]