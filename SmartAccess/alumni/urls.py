from django.urls import path
from . import views

app_name = 'alumni'

urlpatterns = [
    # Alumni Dashboard
    path('', views.alumni_dashboard, name='dashboard'),
    
    # Alumni Profile Management
    path('profile/', views.alumni_profile, name='profile'),
    path('profile/edit/', views.edit_alumni_profile, name='edit_profile'),
    
    # Alumni Registration (for converting students to alumni)
    path('register/', views.register_alumni, name='register'),
    path('convert-student/<int:student_id>/', views.convert_student_to_alumni, name='convert_student'),
    
    # Alumni Event Participation
    path('events/', views.alumni_events, name='events'),
    path('events/<int:event_id>/join/', views.join_event, name='join_event'),
    path('events/<int:event_id>/leave/', views.leave_event, name='leave_event'),
    
    # Alumni Directory
    path('directory/', views.alumni_directory, name='directory'),
    path('directory/<int:alumni_id>/', views.alumni_detail, name='detail'),
    
    # Alumni Analytics (Admin/Teacher Only)
    path('analytics/', views.alumni_analytics, name='analytics'),
    path('export/', views.export_alumni_data, name='export_data'),
    
    # Test and Demo page (Teachers only)
    path('test-demo/', views.test_demo, name='test_demo'),
]