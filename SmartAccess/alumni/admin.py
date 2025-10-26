from django.contrib import admin
from .models import Alumni, AlumniEventParticipation


@admin.register(Alumni)
class AlumniAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'graduation_year', 'degree_program', 
        'current_company', 'current_job_title', 'registration_date',
        'is_active', 'is_public_profile'
    ]
    list_filter = [
        'graduation_year', 'degree_program', 'industry', 
        'is_active', 'is_public_profile', 'registration_date'
    ]
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name',
        'user__email', 'degree_program', 'current_company',
        'current_job_title', 'industry'
    ]
    readonly_fields = ['registration_date', 'last_updated']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'registration_date', 'last_updated')
        }),
        ('Academic Information', {
            'fields': ('graduation_year', 'degree_program', 'final_gpa')
        }),
        ('Professional Information', {
            'fields': (
                'current_job_title', 'current_company', 'industry',
                'linkedin_profile'
            )
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'alternative_email', 'current_address')
        }),
        ('Additional Information', {
            'fields': ('achievements', 'profile_photo')
        }),
        ('Privacy & Status', {
            'fields': ('is_public_profile', 'is_active')
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(AlumniEventParticipation)
class AlumniEventParticipationAdmin(admin.ModelAdmin):
    list_display = [
        'alumni', 'event', 'participation_type', 
        'participation_date', 'attendance_confirmed'
    ]
    list_filter = [
        'participation_type', 'participation_date', 
        'attendance_confirmed', 'event__category'
    ]
    search_fields = [
        'alumni__user__username', 'alumni__user__first_name',
        'alumni__user__last_name', 'event__title'
    ]
    readonly_fields = ['participation_date']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'alumni__user', 'event'
        )
