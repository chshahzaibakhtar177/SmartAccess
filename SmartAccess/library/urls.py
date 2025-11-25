from django.urls import path
from . import views

# Library app URLs - delegating to imported views from student app
urlpatterns = [
    path('', views.library_dashboard, name='library_dashboard'),
    path('books/', views.book_list, name='book_list'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    path('books/add/', views.add_book, name='add_book'),
    path('books/<int:pk>/edit/', views.edit_book, name='edit_book'),
    path('books/<int:pk>/delete/', views.delete_book, name='delete_book'),
    
    # Teacher book issuing and returning
    path('teacher/issue/', views.teacher_issue_book, name='teacher_issue_book'),
    path('teacher/return/', views.teacher_return_book, name='teacher_return_book'),
    path('teacher/return/<int:borrow_id>/process/', views.process_book_return, name='process_book_return'),
    path('api/search-student/', views.search_student_api, name='search_student_api'),
    
    # NFC API endpoint
    path('api/scan-card-for-issue/', views.scan_card_for_issue, name='scan_card_for_issue'),
    
    # Student dashboard (view-only)
    path('student-dashboard/', views.student_library_dashboard, name='student_library_dashboard'),
    
    # Student actions disabled - all borrowing/returning done by teachers
    # path('books/<int:pk>/borrow/', views.borrow_book, name='borrow_book'),
    # path('borrows/<int:borrow_id>/return/', views.return_book, name='return_book'),
    # path('books/<int:pk>/reserve/', views.reserve_book, name='reserve_book'),
    # path('reservations/<int:reservation_id>/cancel/', views.cancel_reservation, name='cancel_reservation'),
    
    # API endpoints
    path('api/nfc-checkout/', views.book_nfc_checkout_api, name='book_nfc_checkout_api'),
    
    # Reports
    path('reports/overdue/', views.overdue_books_report, name='overdue_books_report'),
    
    # Book Category Management URLs
    path('categories/', views.category_list, name='library_category_list'),
    path('categories/create/', views.category_create, name='library_category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='library_category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='library_category_delete'),
]