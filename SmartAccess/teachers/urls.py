from django.urls import path
from . import views

# Teachers app URLs - delegating to imported views from student app
urlpatterns = [
    path('add/', views.add_teacher, name='add_teacher'),
    path('update-photo/', views.update_teacher_photo, name='update_teacher_photo'),
]