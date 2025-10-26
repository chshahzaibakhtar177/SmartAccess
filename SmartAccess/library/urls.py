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
    path('books/<int:pk>/borrow/', views.borrow_book, name='borrow_book'),
    path('borrows/<int:borrow_id>/return/', views.return_book, name='return_book'),
    path('books/<int:pk>/reserve/', views.reserve_book, name='reserve_book'),
    path('reservations/<int:reservation_id>/cancel/', views.cancel_reservation, name='cancel_reservation'),
    path('student-dashboard/', views.student_library_dashboard, name='student_library_dashboard'),
    path('api/nfc-checkout/', views.book_nfc_checkout_api, name='book_nfc_checkout_api'),
    path('reports/overdue/', views.overdue_books_report, name='overdue_books_report'),
]