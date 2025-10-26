from django.urls import path
from . import views

# Fines app URLs - delegating to imported views from student app
urlpatterns = [
    path('add/', views.add_fine, name='add_fine'),
    path('<int:fine_id>/edit/', views.edit_fine, name='edit_fine'),
    path('<int:fine_id>/delete/', views.delete_fine, name='delete_fine'),
    path('<int:fine_id>/toggle/', views.toggle_fine_payment, name='toggle_fine_payment'),
]