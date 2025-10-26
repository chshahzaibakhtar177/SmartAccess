from django.urls import path
from . import views

# Events app URLs - delegating to imported views from student app
urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('<int:event_id>/', views.event_detail, name='event_detail'),
    path('create/', views.create_event, name='create_event'),
    path('<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('<int:event_id>/register/', views.register_for_event, name='register_for_event'),
    path('<int:event_id>/cancel-registration/', views.cancel_event_registration, name='cancel_event_registration'),
    path('api/nfc-checkin/', views.event_nfc_checkin_api, name='event_nfc_checkin_api'),
    
    # Category management URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.create_category, name='create_category'),
    path('categories/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    
    # Teacher event management URLs
    path('teacher-dashboard/', views.teacher_event_dashboard, name='teacher_event_dashboard'),
    path('<int:event_id>/registrations/', views.event_registrations, name='event_registrations'),
    path('registration/<int:registration_id>/manage/', views.manage_registration, name='manage_registration'),
    path('<int:event_id>/student/<int:student_id>/mark-attendance/', views.mark_attendance, name='mark_attendance'),
    path('<int:event_id>/student/<int:student_id>/remove-attendance/', views.remove_attendance, name='remove_attendance'),
]