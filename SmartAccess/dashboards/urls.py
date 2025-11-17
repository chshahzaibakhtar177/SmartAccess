from django.urls import path
from . import views

urlpatterns = [
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'), 
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # AJAX API endpoints for real-time updates
    path('api/teacher/dashboard-data/', views.teacher_dashboard_data, name='teacher_dashboard_data'),
    path('api/student/dashboard-data/', views.student_dashboard_data, name='student_dashboard_data'),
]