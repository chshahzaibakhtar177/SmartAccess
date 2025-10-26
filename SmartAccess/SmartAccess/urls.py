"""
URL configuration for SmartAccess project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from student.views import *
from django.contrib.auth import views as auth_views


def home_redirect(request):
    return redirect('login')

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('', home_redirect, name='home_redirect'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('dashboard_redirect/', dashboard_redirect, name='dashboard_redirect'),

    
    path('register_student/', register_student, name='register_student'),
    path('edit_student/<int:student_id>/', edit_student, name='edit_student'),
    path('delete_student/<int:student_id>/', delete_student, name='delete_student'),
    path('student/change_password/', change_password_manual, name='change_password_manual'),

    
    path('fines/add/', add_fine, name='add_fine'),
    path('fines/edit/<int:fine_id>/', edit_fine, name='edit_fine'),
    path('fines/delete/<int:fine_id>/', delete_fine, name='delete_fine'),
    path('fine/toggle/<int:fine_id>/', toggle_fine_payment, name='toggle_fine_payment'),
    path('api/student-search/', student_search_api, name='student_search_api'),
    path('api/nfc-scan/', nfc_scan_api, name='nfc_scan_api'),  # New NFC API endpoint
    
    # Card assignment URLs
    path('assign-card/<int:student_id>/', assign_card_page, name='assign_card_page'),
    path('assign-card-request/<int:student_id>/', assign_card_request, name='assign_card_request'),
    path('remove-card/<int:student_id>/', remove_card, name='remove_card'),
    
    # Event Management URLs
    path('events/', event_list, name='event_list'),
    path('events/<int:event_id>/', event_detail, name='event_detail'),
    path('events/create/', create_event, name='create_event'),
    path('events/<int:event_id>/edit/', edit_event, name='edit_event'),
    path('events/<int:event_id>/register/', register_for_event, name='register_for_event'),
    path('events/<int:event_id>/cancel-registration/', cancel_event_registration, name='cancel_event_registration'),
    path('api/event-nfc-checkin/', event_nfc_checkin_api, name='event_nfc_checkin_api'),
    
    # Library Management URLs
    path('library/', library_dashboard, name='library_dashboard'),
    path('library/books/', book_list, name='book_list'),
    path('library/books/<int:pk>/', book_detail, name='book_detail'),
    path('library/books/add/', add_book, name='add_book'),
    path('library/books/<int:pk>/edit/', edit_book, name='edit_book'),
    path('library/books/<int:pk>/delete/', delete_book, name='delete_book'),
    path('library/books/<int:pk>/borrow/', borrow_book, name='borrow_book'),
    path('library/borrows/<int:borrow_id>/return/', return_book, name='return_book'),
    path('library/books/<int:pk>/reserve/', reserve_book, name='reserve_book'),
    path('library/reservations/<int:reservation_id>/cancel/', cancel_reservation, name='cancel_reservation'),
    path('library/student/', student_library_dashboard, name='student_library_dashboard'),
    path('library/overdue-report/', overdue_books_report, name='overdue_books_report'),
    path('api/library/nfc-checkout/', book_nfc_checkout_api, name='book_nfc_checkout_api'),
    
    path('student/dashboard/', student_dashboard, name='student_dashboard'),
    path('teacher/dashboard/', teacher_dashboard, name='teacher_dashboard'),
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),


    path('simulate-scan/', simulate_card_scan, name='simulate_card_scan'),
    path('view_logs/', view_logs, name='view_logs'),
    path('student/<int:student_id>/', student_detail, name='student_detail'),

    
    path('admin/add-teacher/', add_teacher, name='add_teacher'),
    
    path('export_logs/csv/', export_logs_csv, name='export_logs_csv'),
    
    path('student/update-photo/', update_photo, name='update_photo'),
    path('teacher/update-photo/', update_teacher_photo, name='update_teacher_photo'),
    
    path('profile/', profile_view, name='profile'),

    path('password-reset/', StudentPasswordResetView.as_view(), name='password_reset'),
    path('reset/<uidb64>/<token>/', StudentPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('attendance/analytics/', attendance_analytics, name='attendance_analytics'),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
