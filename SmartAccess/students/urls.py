from django.urls import path
from . import views

# Students app URLs - pure student management functions
urlpatterns = [
    path('register/', views.register_student, name='register_student'),
    path('<int:student_id>/edit/', views.edit_student, name='edit_student'),
    path('<int:student_id>/delete/', views.delete_student, name='delete_student'),
    path('<int:student_id>/', views.student_detail, name='student_detail'),
    path('update-photo/', views.update_photo, name='update_photo'),
    path('search/', views.student_search, name='student_search'),
    path('api/search/', views.student_search_api, name='student_search_api'),
    # Card management functions now in students app
    path('<int:student_id>/assign-card/', views.assign_card_page, name='assign_card_page'),
    path('<int:student_id>/assign-card-request/', views.assign_card_request, name='assign_card_request'),
    path('<int:student_id>/remove-card/', views.remove_card, name='remove_card'),
]