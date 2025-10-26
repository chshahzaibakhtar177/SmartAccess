from django.contrib import admin
from .models import (Student, Fine, EntryLog, Teacher, Event, EventCategory, 
                     EventRegistration, EventAttendance, Book, BookCategory, 
                     BookBorrow, BookReservation)

# Student Management
admin.site.register(Student)
admin.site.register(Fine)
admin.site.register(EntryLog)
admin.site.register(Teacher)

# Event Management
admin.site.register(Event)
admin.site.register(EventCategory)
admin.site.register(EventRegistration)
admin.site.register(EventAttendance)

# Library Management
@admin.register(BookCategory)
class BookCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'color']
    search_fields = ['name']

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'isbn', 'category', 'status', 'location']
    list_filter = ['status', 'category', 'publication_year']
    search_fields = ['title', 'author', 'isbn']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(BookBorrow)
class BookBorrowAdmin(admin.ModelAdmin):
    list_display = ['student', 'book', 'borrow_date', 'due_date', 'status', 'fine_amount']
    list_filter = ['status', 'borrow_date', 'due_date']
    search_fields = ['student__name', 'student__roll_number', 'book__title']
    readonly_fields = ['borrow_date']

@admin.register(BookReservation)
class BookReservationAdmin(admin.ModelAdmin):
    list_display = ['student', 'book', 'reservation_date', 'expiry_date', 'status']
    list_filter = ['status', 'reservation_date']
    search_fields = ['student__name', 'student__roll_number', 'book__title']

admin.site.site_header = "SmartAccess Admin"
admin.site.site_title = "SmartAccess Admin Portal"
admin.site.index_title = "Welcome to SmartAccess Admin Portal"

