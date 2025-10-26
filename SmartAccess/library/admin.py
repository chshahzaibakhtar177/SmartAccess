from django.contrib import admin
from .models import Book, BookCategory, BookBorrow, BookReservation

@admin.register(BookCategory)
class BookCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'color']
    list_filter = ['name']
    search_fields = ['name', 'description']
    ordering = ['name']

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'isbn', 'category', 'status', 'publication_year']
    list_filter = ['category', 'status', 'publication_year', 'publisher']
    search_fields = ['title', 'author', 'isbn', 'publisher']
    ordering = ['title']
    readonly_fields = ['acquisition_date']

@admin.register(BookBorrow)
class BookBorrowAdmin(admin.ModelAdmin):
    list_display = ['book', 'student', 'borrow_date', 'due_date', 'return_date', 'status']
    list_filter = ['status', 'borrow_date', 'due_date']
    search_fields = ['book__title', 'student__user__username']
    ordering = ['-borrow_date']

@admin.register(BookReservation)
class BookReservationAdmin(admin.ModelAdmin):
    list_display = ['book', 'student', 'reservation_date', 'expiry_date', 'status']
    list_filter = ['status', 'reservation_date']
    search_fields = ['book__title', 'student__user__username']
    ordering = ['-reservation_date']
