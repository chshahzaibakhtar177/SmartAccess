from django.contrib import admin
from .models import Bus, Route, TransportLog, BusSchedule


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ['bus_number', 'driver_name', 'capacity', 'route', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['bus_number', 'driver_name', 'route']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Bus Information', {
            'fields': ('bus_number', 'capacity', 'route', 'is_active')
        }),
        ('Driver Information', {
            'fields': ('driver_name', 'driver_contact')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['route_name', 'start_location', 'end_location', 'total_distance', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['route_name', 'start_location', 'end_location']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Route Information', {
            'fields': ('route_name', 'start_location', 'end_location', 'status')
        }),
        ('Route Details', {
            'fields': ('total_distance', 'estimated_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(TransportLog)
class TransportLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'bus', 'boarding_status', 'boarding_time', 'travel_duration_display']
    list_filter = ['user_type', 'boarding_status', 'boarding_time', 'bus', 'route']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'nfc_uid', 'bus__bus_number']
    readonly_fields = ['created_at', 'travel_duration_display']
    date_hierarchy = 'boarding_time'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'user_type', 'nfc_uid')
        }),
        ('Transport Details', {
            'fields': ('bus', 'route', 'boarding_location')
        }),
        ('Timing Information', {
            'fields': ('boarding_status', 'boarding_time', 'alighting_time', 'travel_duration_display')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def travel_duration_display(self, obj):
        duration = obj.get_travel_duration()
        if duration:
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        return "Not available"
    travel_duration_display.short_description = "Travel Duration"


@admin.register(BusSchedule)
class BusScheduleAdmin(admin.ModelAdmin):
    list_display = ['bus', 'route', 'schedule_type', 'departure_time', 'arrival_time', 'weekdays_display', 'is_active']
    list_filter = ['schedule_type', 'is_active', 'bus', 'route']
    search_fields = ['bus__bus_number', 'route__route_name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Schedule Information', {
            'fields': ('bus', 'route', 'schedule_type', 'is_active')
        }),
        ('Timing', {
            'fields': ('departure_time', 'arrival_time')
        }),
        ('Weekdays', {
            'fields': ('weekdays',),
            'description': 'Enter weekday numbers as a list (0=Monday, 1=Tuesday, ..., 6=Sunday). Example: [0,1,2,3,4] for weekdays.'
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def weekdays_display(self, obj):
        weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        if obj.weekdays:
            return ', '.join([weekday_names[day] for day in obj.weekdays if 0 <= day <= 6])
        return "No days set"
    weekdays_display.short_description = "Active Days"
