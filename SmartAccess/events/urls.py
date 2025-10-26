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
]