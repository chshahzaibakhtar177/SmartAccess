from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth.models import User
import csv

from .models import Alumni, AlumniEventParticipation, AlumniNetworking, AlumniJobPosting
from .forms import (
    AlumniRegistrationForm, AlumniProfileUpdateForm, 
    AlumniEventParticipationForm, AlumniSearchForm, ConvertStudentForm
)
from events.models import Event
from students.models import Student
from authentication.decorators import teacher_required


# Alumni Views Implementation
@login_required
def alumni_dashboard(request):
    """Alumni dashboard view"""
    try:
        alumni = Alumni.objects.get(user=request.user)
        
        # Get alumni statistics
        total_events_participated = AlumniEventParticipation.objects.filter(alumni=alumni).count()
        recent_events = AlumniEventParticipation.objects.filter(
            alumni=alumni
        ).select_related('event').order_by('-participation_date')[:5]
        
        # Get networking connections count
        networking_connections = AlumniNetworking.objects.filter(
            Q(alumni1=alumni) | Q(alumni2=alumni)
        ).count()
        
        # Get job postings count
        job_postings_count = AlumniJobPosting.objects.filter(posted_by=alumni).count()
        
        context = {
            'alumni': alumni,
            'total_events_participated': total_events_participated,
            'recent_events': recent_events,
            'networking_connections': networking_connections,
            'job_postings_count': job_postings_count,
        }
        return render(request, 'alumni/dashboard.html', context)
        
    except Alumni.DoesNotExist:
        messages.error(request, 'Alumni profile not found. Please contact administration.')
        return redirect('dashboards:dashboard')

@login_required
def alumni_profile(request):
    """Alumni profile view"""
    try:
        alumni = Alumni.objects.get(user=request.user)
        context = {
            'alumni': alumni,
        }
        return render(request, 'alumni/profile.html', context)
    except Alumni.DoesNotExist:
        messages.error(request, 'Alumni profile not found.')
        return redirect('alumni:dashboard')

@login_required
def edit_alumni_profile(request):
    """Edit alumni profile view"""
    try:
        alumni = Alumni.objects.get(user=request.user)
        
        if request.method == 'POST':
            form = AlumniProfileUpdateForm(request.POST, request.FILES, instance=alumni)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('alumni:profile')
        else:
            form = AlumniProfileUpdateForm(instance=alumni)
        
        context = {
            'form': form,
            'alumni': alumni,
        }
        return render(request, 'alumni/edit_profile.html', context)
        
    except Alumni.DoesNotExist:
        messages.error(request, 'Alumni profile not found.')
        return redirect('alumni:dashboard')

@login_required
@teacher_required
def register_alumni(request):
    """Register new alumni view"""
    if request.method == 'POST':
        form = AlumniRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Get or create user
                user_data = form.cleaned_data
                user, created = User.objects.get_or_create(
                    email=user_data['email'],
                    defaults={
                        'username': user_data['email'],
                        'first_name': user_data['first_name'],
                        'last_name': user_data['last_name'],
                    }
                )
                
                if not created and Alumni.objects.filter(user=user).exists():
                    messages.error(request, 'Alumni profile already exists for this user.')
                    return render(request, 'alumni/register.html', {'form': form})
                
                # Create alumni profile
                alumni = form.save(commit=False)
                alumni.user = user
                alumni.is_active = True
                alumni.save()
                
                messages.success(request, f'Alumni profile created successfully for {user.get_full_name()}!')
                return redirect('alumni:directory')
                
            except Exception as e:
                messages.error(request, f'Error creating alumni profile: {str(e)}')
    else:
        form = AlumniRegistrationForm()
    
    context = {'form': form}
    return render(request, 'alumni/register.html', context)

@login_required
@teacher_required
def convert_student_to_alumni(request, student_id):
    """Convert student to alumni view"""
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        form = ConvertStudentForm(request.POST)
        if form.is_valid():
            try:
                # Check if alumni profile already exists
                if Alumni.objects.filter(user=student.user).exists():
                    messages.error(request, 'Alumni profile already exists for this student.')
                    return render(request, 'alumni/convert_student.html', {'form': form, 'student': student})
                
                # Create alumni profile
                Alumni.objects.create(
                    user=student.user,
                    student_id=student.student_id,
                    course=form.cleaned_data['course'],
                    department=form.cleaned_data['department'],
                    graduation_year=form.cleaned_data['graduation_year'],
                    graduation_date=form.cleaned_data['graduation_date'],
                    current_position=form.cleaned_data.get('current_position', ''),
                    company=form.cleaned_data.get('company', ''),
                    contact_number=form.cleaned_data.get('contact_number', ''),
                    linkedin_profile=form.cleaned_data.get('linkedin_profile', ''),
                    address=form.cleaned_data.get('address', ''),
                    is_active=True
                )
                
                # Deactivate student profile
                student.is_active = False
                student.save()
                
                messages.success(request, f'Successfully converted {student.user.get_full_name()} to alumni.')
                return redirect('alumni:directory')
                
            except Exception as e:
                messages.error(request, f'Error converting student to alumni: {str(e)}')
    else:
        form = ConvertStudentForm(initial={
            'course': student.course,
            'department': student.department,
        })
    
    context = {
        'form': form,
        'student': student,
    }
    return render(request, 'alumni/convert_student.html', context)

@login_required
def alumni_events(request):
    """Alumni events view"""
    try:
        alumni = Alumni.objects.get(user=request.user)
        
        # Get all available events
        available_events = Event.objects.filter(
            is_active=True,
            event_date__gte=timezone.now()
        ).order_by('event_date')
        
        # Get alumni's participated events
        participated_events = AlumniEventParticipation.objects.filter(
            alumni=alumni
        ).select_related('event').order_by('-participation_date')
        
        # Get participated event IDs to exclude from available events
        participated_event_ids = participated_events.values_list('event_id', flat=True)
        available_events = available_events.exclude(id__in=participated_event_ids)
        
        # Paginate available events
        paginator = Paginator(available_events, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'alumni': alumni,
            'available_events': page_obj,
            'participated_events': participated_events,
        }
        return render(request, 'alumni/events.html', context)
        
    except Alumni.DoesNotExist:
        messages.error(request, 'Alumni profile not found.')
        return redirect('alumni:dashboard')

@login_required
def join_event(request, event_id):
    """Join event view"""
    try:
        alumni = Alumni.objects.get(user=request.user)
        event = get_object_or_404(Event, id=event_id, is_active=True)
        
        # Check if already participated
        if AlumniEventParticipation.objects.filter(alumni=alumni, event=event).exists():
            messages.warning(request, 'You are already registered for this event.')
            return redirect('alumni:events')
        
        if request.method == 'POST':
            form = AlumniEventParticipationForm(request.POST)
            if form.is_valid():
                participation = form.save(commit=False)
                participation.alumni = alumni
                participation.event = event
                participation.participation_date = timezone.now()
                participation.save()
                
                messages.success(request, f'Successfully registered for {event.name}!')
                return redirect('alumni:events')
        else:
            form = AlumniEventParticipationForm()
        
        context = {
            'form': form,
            'event': event,
            'alumni': alumni,
        }
        return render(request, 'alumni/join_event.html', context)
        
    except Alumni.DoesNotExist:
        messages.error(request, 'Alumni profile not found.')
        return redirect('alumni:dashboard')

@login_required
def leave_event(request, event_id):
    """Leave event view"""
    try:
        alumni = Alumni.objects.get(user=request.user)
        event = get_object_or_404(Event, id=event_id)
        
        participation = get_object_or_404(
            AlumniEventParticipation, 
            alumni=alumni, 
            event=event
        )
        
        if request.method == 'POST':
            participation.delete()
            messages.success(request, f'Successfully cancelled registration for {event.name}.')
            return redirect('alumni:events')
        
        context = {
            'event': event,
            'alumni': alumni,
            'participation': participation,
        }
        return render(request, 'alumni/leave_event.html', context)
        
    except (Alumni.DoesNotExist, AlumniEventParticipation.DoesNotExist):
        messages.error(request, 'Registration not found.')
        return redirect('alumni:events')

@login_required
def alumni_directory(request):
    """Alumni directory view"""
    search_query = request.GET.get('search', '')
    graduation_year = request.GET.get('graduation_year', '')
    department = request.GET.get('department', '')
    
    # Base queryset
    alumni_list = Alumni.objects.select_related('user').filter(is_active=True)
    
    # Apply filters
    if search_query:
        alumni_list = alumni_list.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(course__icontains=search_query) |
            Q(current_position__icontains=search_query) |
            Q(company__icontains=search_query)
        )
    
    if graduation_year:
        alumni_list = alumni_list.filter(graduation_year=graduation_year)
    
    if department:
        alumni_list = alumni_list.filter(department__icontains=department)
    
    # Get unique graduation years and departments for filters
    graduation_years = Alumni.objects.values_list('graduation_year', flat=True).distinct().order_by('-graduation_year')
    departments = Alumni.objects.values_list('department', flat=True).distinct().order_by('department')
    
    # Paginate results
    paginator = Paginator(alumni_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'alumni_list': page_obj,
        'search_query': search_query,
        'selected_graduation_year': graduation_year,
        'selected_department': department,
        'graduation_years': graduation_years,
        'departments': departments,
    }
    return render(request, 'alumni/directory.html', context)

@login_required
def alumni_detail(request, alumni_id):
    """Alumni detail view"""
    alumni = get_object_or_404(Alumni, id=alumni_id, is_active=True)
    
    # Get alumni's event participation history
    event_participations = AlumniEventParticipation.objects.filter(
        alumni=alumni
    ).select_related('event').order_by('-participation_date')[:10]
    
    # Get networking connections (if current user is connected or is the alumni themselves)
    show_connections = False
    networking_connections = []
    
    try:
        current_alumni = Alumni.objects.get(user=request.user)
        if current_alumni == alumni or AlumniNetworking.objects.filter(
            Q(alumni1=current_alumni, alumni2=alumni) | 
            Q(alumni1=alumni, alumni2=current_alumni)
        ).exists():
            show_connections = True
            networking_connections = AlumniNetworking.objects.filter(
                Q(alumni1=alumni) | Q(alumni2=alumni)
            )[:5]
    except Alumni.DoesNotExist:
        pass
    
    # Get job postings by this alumni (if any)
    job_postings = AlumniJobPosting.objects.filter(
        posted_by=alumni, 
        is_active=True
    ).order_by('-created_at')[:5]
    
    context = {
        'alumni': alumni,
        'event_participations': event_participations,
        'show_connections': show_connections,
        'networking_connections': networking_connections,
        'job_postings': job_postings,
    }
    return render(request, 'alumni/detail.html', context)

@login_required
@teacher_required
def alumni_analytics(request):
    """Alumni analytics view"""
    # Get overall statistics
    total_alumni = Alumni.objects.count()
    active_alumni = Alumni.objects.filter(is_active=True).count()
    inactive_alumni = Alumni.objects.filter(is_active=False).count()
    
    # Get graduation year distribution
    graduation_year_stats = Alumni.objects.values('graduation_year').annotate(
        count=Count('id')
    ).order_by('-graduation_year')
    
    # Get department distribution
    department_stats = Alumni.objects.values('department').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Get monthly event participation data
    monthly_participation = AlumniEventParticipation.objects.extra(
        select={'month': 'EXTRACT(month FROM participation_date)', 'year': 'EXTRACT(year FROM participation_date)'}
    ).values('month', 'year').annotate(count=Count('id')).order_by('-year', '-month')[:12]
    
    # Get most active alumni (by event participation)
    most_active_alumni = Alumni.objects.annotate(
        participation_count=Count('alumnieventparticipation')
    ).order_by('-participation_count')[:10]
    
    # Get recent registrations
    recent_registrations = Alumni.objects.select_related('user').order_by('-created_at')[:10]
    
    # Get networking statistics
    total_connections = AlumniNetworking.objects.count()
    
    # Get job postings statistics
    total_job_postings = AlumniJobPosting.objects.count()
    active_job_postings = AlumniJobPosting.objects.filter(is_active=True).count()
    
    context = {
        'total_alumni': total_alumni,
        'active_alumni': active_alumni,
        'inactive_alumni': inactive_alumni,
        'graduation_year_stats': graduation_year_stats,
        'department_stats': department_stats,
        'monthly_participation': list(monthly_participation),
        'most_active_alumni': most_active_alumni,
        'recent_registrations': recent_registrations,
        'total_connections': total_connections,
        'total_job_postings': total_job_postings,
        'active_job_postings': active_job_postings,
    }
    return render(request, 'alumni/analytics.html', context)

@login_required
@teacher_required
def export_alumni_data(request):
    """Export alumni data to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="alumni_data_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Student ID', 'Name', 'Email', 'Course', 'Department', 
        'Graduation Year', 'Graduation Date', 'Current Position', 
        'Company', 'Contact Number', 'LinkedIn Profile', 'Status'
    ])
    
    # Write alumni data
    alumni_list = Alumni.objects.select_related('user').all()
    for alumni in alumni_list:
        writer.writerow([
            alumni.student_id,
            f"{alumni.user.first_name} {alumni.user.last_name}",
            alumni.user.email,
            alumni.course,
            alumni.department,
            alumni.graduation_year,
            alumni.graduation_date.strftime('%Y-%m-%d') if alumni.graduation_date else '',
            alumni.current_position,
            alumni.company,
            alumni.contact_number,
            alumni.linkedin_profile,
            'Active' if alumni.is_active else 'Inactive'
        ])
    
    return response
