from django.contrib import admin
from .models import EventCategory, Event, EventRegistration, EventAttendance

@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'color']
    search_fields = ['name', 'description']
    list_filter = ['name']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'organizer', 'start_datetime', 'status', 'max_capacity']
    search_fields = ['title', 'description', 'venue']
    list_filter = ['category', 'status', 'organizer', 'start_datetime']
    date_hierarchy = 'start_datetime'

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ['event', 'student', 'registration_date', 'payment_status', 'status']
    search_fields = ['event__title', 'student__user__first_name', 'student__user__last_name']
    list_filter = ['payment_status', 'status', 'registration_date']

@admin.register(EventAttendance)
class EventAttendanceAdmin(admin.ModelAdmin):
    list_display = ['event', 'student', 'checkin_time', 'checkout_time', 'checkin_method']
    search_fields = ['event__title', 'student__user__first_name', 'student__user__last_name']
    list_filter = ['checkin_time', 'checkin_method', 'event']
