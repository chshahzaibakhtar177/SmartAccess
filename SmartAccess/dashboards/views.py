from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Sum
from datetime import timedelta

# Import models from modular apps
from students.models import Student
from fines.models import Fine  
from attendance.models import EntryLog
from events.models import Event
from library.models import Book
from authentication.decorators import student_required, teacher_required


@login_required
@student_required
def student_dashboard(request):
    """Student dashboard with attendance, fines, and recent activities"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found. Please contact administrator.")
        return redirect('login')
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # Get Entry Logs
    entry_logs = EntryLog.objects.filter(
        student=student,
        timestamp__date__gte=last_30_days
    ).order_by('-timestamp')

    # Get fine details
    fines = Fine.objects.filter(student=student)
    total_amount = fines.aggregate(Sum('amount'))['amount__sum'] or 0
    unpaid_fines = fines.filter(is_paid=False)
    
    # Get recent activity
    recent_activities = EntryLog.objects.filter(
        student=student
    ).order_by('-timestamp')[:5]

    # Calculate attendance stats
    total_days = entry_logs.filter(action='in').count()
    late_days = entry_logs.filter(
        action='in',
        timestamp__time__hour__gte=9,
        timestamp__time__minute__gte=0
    ).count()

    context = {
        'student': student,
        'total_fines': total_amount,
        'unpaid_fines': unpaid_fines,
        'entry_logs': entry_logs,
        'recent_activities': recent_activities,
        'attendance_stats': {
            'total_days': total_days,
            'present_days': total_days - late_days,
            'late_days': late_days,
        },
        'total_fines_count': fines.count(),
        'total_paid': fines.filter(is_paid=True).count(),
        'total_unpaid': fines.filter(is_paid=False).count(),
        'show_photo_form': not student.photo
    }
    
    return render(request, 'dashboards/student_dashboard.html', context)


@login_required
@teacher_required
def teacher_dashboard(request):
    """Teacher dashboard with student statistics and attendance overview"""
    today = timezone.now().date()
    
    # Get statistics
    total_students = Student.objects.count()
    students_inside = Student.objects.filter(is_in_university=True).count()
    total_fines = Fine.objects.filter(is_paid=False).count()
    
    # Get today's attendance
    today_entries = EntryLog.objects.filter(
        timestamp__date=today,
        action='in'
    ).select_related('student')
    
    # Get late entries (after 9 AM)
    late_entries = today_entries.filter(
        timestamp__time__hour__gte=9,
        timestamp__time__minute__gte=0
    )
    
    # Get recent activities
    recent_logs = EntryLog.objects.select_related('student')\
        .order_by('-timestamp')[:10]
    
    # Get unpaid fines
    unpaid_fines = Fine.objects.filter(is_paid=False)\
        .select_related('student')\
        .order_by('-date_issued')[:5]

    context = {
        'total_students': total_students,
        'students_inside': students_inside,
        'total_fines': total_fines,
        'today_entries': today_entries,
        'late_entries': late_entries,
        'recent_logs': recent_logs,
        'unpaid_fines': unpaid_fines,
        'attendance_rate': (today_entries.count() / total_students * 100) if total_students > 0 else 0
    }
    
    return render(request, 'dashboards/teacher_dashboard.html', context)


@login_required
def admin_dashboard(request):
    """Admin dashboard with system-wide statistics and management tools"""
    # Restrict access to superusers only
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard_redirect')
        
    today = timezone.now().date()
    last_week = today - timedelta(days=7)

    # Today's statistics
    today_entries = EntryLog.objects.filter(
        timestamp__date=today
    )
    today_checkins = today_entries.filter(action='in').count()
    today_checkouts = today_entries.filter(action='out').count()

    # Students currently inside
    students_inside = Student.objects.filter(is_in_university=True).count()

    # Weekly statistics
    weekly_logs = EntryLog.objects.filter(
        timestamp__date__gte=last_week
    ).values('timestamp__date').annotate(
        entries=Count('id', filter=Q(action='in'))
    ).order_by('timestamp__date')

    # Fine statistics
    total_fines = Fine.objects.aggregate(
        total=Sum('amount'),
        unpaid=Sum('amount', filter=Q(is_paid=False))
    )

    # Recent activities
    recent_logs = EntryLog.objects.select_related('student')\
        .order_by('-timestamp')[:15]

    # Event statistics  
    upcoming_events = Event.objects.filter(
        start_datetime__gte=timezone.now()
    ).count()

    # Library statistics
    total_books = Book.objects.count()
    borrowed_books = Book.objects.filter(status='borrowed').count()

    context = {
        'today_checkins': today_checkins,
        'today_checkouts': today_checkouts,
        'students_inside': students_inside,
        'weekly_logs': weekly_logs,
        'total_fines': total_fines,
        'recent_logs': recent_logs,
        'upcoming_events': upcoming_events,
        'total_books': total_books,
        'borrowed_books': borrowed_books,
    }
    
    return render(request, 'admin/admin_dashboard.html', context)
