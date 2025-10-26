from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    # Django's built-in authentication URLs
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Custom authentication views
    path('dashboard_redirect/', views.dashboard_redirect, name='dashboard_redirect'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_manual, name='change_password_manual'),
    
    # Password reset views
    path('password-reset/', views.StudentPasswordResetView.as_view(), name='password_reset'),
    path('reset/<uidb64>/<token>/', views.StudentPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]