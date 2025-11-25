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
from authentication.decorators import teacher_required, alumni_required


# Alumni Views Implementation
@login_required
@alumni_required
def alumni_dashboard(request):
    """Alumni dashboard with statistics and recent activities"""
    try:
        alumni = Alumni.objects.get(user=request.user)
    except Alumni.DoesNotExist:
        messages.error(request, 'Alumni profile not found. Please contact administrator.')
        return redirect('dashboard_redirect')
    
    # Get recent alumni activities
    recent_activities = AlumniEventParticipation.objects.filter(
        alumni=alumni
    ).select_related('event').order_by('-participation_date')[:5]
    
    # Get alumni statistics
    total_events = AlumniEventParticipation.objects.filter(alumni=alumni).count()
    
    # Get upcoming events - use start_datetime instead of date
    upcoming_events = Event.objects.filter(
        start_datetime__gte=timezone.now(),
        is_active=True
    ).order_by('start_datetime')[:5]
    
    # Get networking connections count (using correct field names: requester and recipient)
    networking_connections = AlumniNetworking.objects.filter(
        Q(requester=alumni) | Q(recipient=alumni),
        status='accepted'  # Only count accepted connections
    ).count()
    
    # Get job postings count
    job_postings_count = AlumniJobPosting.objects.filter(posted_by=alumni).count()
    
    context = {
        'alumni': alumni,
        'recent_activities': recent_activities,
        'total_events': total_events,
        'total_events_participated': total_events,  # For template compatibility
        'upcoming_events': upcoming_events,
        'networking_connections': networking_connections,
        'job_postings_count': job_postings_count,
    }
    return render(request, 'alumni/dashboard.html', context)

@login_required
@alumni_required
def alumni_profile(request):
    """Alumni profile view"""
    alumni = Alumni.objects.get(user=request.user)
    context = {
        'alumni': alumni,
    }
    return render(request, 'alumni/profile.html', context)

@login_required
@alumni_required
def edit_alumni_profile(request):
    """Edit alumni profile view"""
    alumni = Alumni.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = AlumniProfileUpdateForm(request.POST, request.FILES, instance=alumni)
        if form.is_valid():
            # Update user info
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            
            # Update alumni profile
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('alumni:profile')
    else:
        form = AlumniProfileUpdateForm(instance=alumni, user=request.user)
    
    context = {
        'form': form,
        'alumni': alumni,
    }
    return render(request, 'alumni/edit_profile.html', context)

@login_required
@teacher_required
def select_students_for_alumni(request):
    """View to select students and convert them to alumni"""
    from students.models import Student
    
    # Get all students (Student model doesn't have is_active field)
    students = Student.objects.all().select_related('user').order_by('roll_number')
    
    # Check which students already have alumni profiles
    students_with_status = []
    for student in students:
        has_alumni = Alumni.objects.filter(user=student.user).exists()
        students_with_status.append({
            'student': student,
            'has_alumni': has_alumni
        })
    
    context = {
        'students_with_status': students_with_status,
    }
    return render(request, 'alumni/select_students.html', context)

@login_required
@teacher_required
def register_alumni(request):
    """Register new alumni view - Creates user account automatically"""
    if request.method == 'POST':
        form = AlumniRegistrationForm(request.POST, request.FILES)
        
        # Get additional user fields from POST
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        
        if form.is_valid() and first_name and last_name and email:
            try:
                # Check if user already exists
                if User.objects.filter(email=email).exists():
                    messages.error(request, 'A user with this email already exists.')
                    return render(request, 'alumni/register.html', {
                        'form': form,
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email
                    })
                
                # Create user account with auto-generated password
                username = email.split('@')[0]
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Auto-generate password: FirstNameLastNameYear (e.g., JohnDoe2024)
                auto_password = f"{first_name}{last_name}{form.cleaned_data['graduation_year']}"
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=auto_password
                )
                
                # Add to Alumni group
                from django.contrib.auth.models import Group
                alumni_group, created = Group.objects.get_or_create(name='Alumni')
                user.groups.add(alumni_group)
                
                # Create alumni profile
                alumni = form.save(commit=False)
                alumni.user = user
                alumni.is_active = True
                alumni.save()
                
                messages.success(request, f'Alumni profile created successfully for {user.get_full_name()}! Login credentials: Username: {username}, Password: {auto_password}')
                return redirect('alumni:directory')
                
            except Exception as e:
                messages.error(request, f'Error creating alumni profile: {str(e)}')
        else:
            if not first_name or not last_name or not email:
                messages.error(request, 'Please provide first name, last name, and email.')
    else:
        form = AlumniRegistrationForm()
        first_name = ''
        last_name = ''
        email = ''
    
    context = {
        'form': form,
        'first_name': first_name,
        'last_name': last_name,
        'email': email
    }
    return render(request, 'alumni/register.html', context)

@login_required
@teacher_required
def convert_student_to_alumni(request, student_id):
    """Convert student to alumni - keeps student account active (POST only from modal)"""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('alumni:select_students_for_alumni')
    
    student = get_object_or_404(Student, id=student_id)
    form = ConvertStudentForm(request.POST)
    
    if form.is_valid():
        try:
            # Check if alumni profile already exists
            if Alumni.objects.filter(user=student.user).exists():
                messages.warning(request, f'{student.name} is already an alumni.')
                return redirect('alumni:select_students_for_alumni')
            
            # Create alumni profile (student account remains active)
            alumni = Alumni.objects.create(
                user=student.user,
                graduation_year=form.cleaned_data['graduation_year'],
                degree_program=form.cleaned_data['degree_program'],
                final_gpa=form.cleaned_data.get('final_gpa'),
                phone_number='',
                current_address='',
                is_active=True,
                is_public_profile=True
            )
            
            # Keep student profile active so they can still use NFC and entry/exit
            # Just add Alumni group alongside Students group
            from django.contrib.auth.models import Group
            
            # Create Alumni group if it doesn't exist
            alumni_group, created = Group.objects.get_or_create(name='Alumni')
            student.user.groups.add(alumni_group)
            
            messages.success(request, f'✓ Successfully converted {student.name} to alumni! They can login with existing credentials, enroll in events, and use entry/exit with their NFC card.')
            return redirect('alumni:select_students_for_alumni')
            
        except Exception as e:
            import traceback
            messages.error(request, f'Error converting student to alumni: {str(e)}')
            print(f"Conversion error: {str(e)}")
            print(traceback.format_exc())
            return redirect('alumni:select_students_for_alumni')
    else:
        # Show form errors
        error_msgs = []
        for field, errors in form.errors.items():
            for error in errors:
                error_msgs.append(f"{field}: {error}")
        messages.error(request, f'Form validation failed: {", ".join(error_msgs)}')
        return redirect('alumni:select_students_for_alumni')

@login_required
@teacher_required
def revert_alumni_to_student(request, student_id):
    """Revert alumni back to student-only status (POST only from modal)"""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('alumni:select_students_for_alumni')
    
    student = get_object_or_404(Student, id=student_id)
    
    try:
        # Check if student has alumni profile
        alumni = Alumni.objects.filter(user=student.user).first()
        if not alumni:
            messages.error(request, f'{student.name} is not an alumni.')
            return redirect('alumni:select_students_for_alumni')
        
        # Remove Alumni group from user
        from django.contrib.auth.models import Group
        alumni_group = Group.objects.filter(name='Alumni').first()
        if alumni_group:
            student.user.groups.remove(alumni_group)
        
        # Delete alumni profile
        alumni.delete()
        
        messages.success(request, f'✓ Successfully reverted {student.name} from alumni to student status.')
        return redirect('alumni:select_students_for_alumni')
        
    except Exception as e:
        messages.error(request, f'Error reverting alumni to student: {str(e)}')
        return redirect('alumni:select_students_for_alumni')

@login_required
@alumni_required
def alumni_events(request):
    """Alumni events view"""
    alumni = Alumni.objects.get(user=request.user)
    
    # Get all available events
    available_events = Event.objects.filter(
        is_active=True,
        start_datetime__gte=timezone.now()
    ).order_by('start_datetime')
    
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

@login_required
@alumni_required
def join_event(request, event_id):
    """Join event view"""
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


@login_required
@alumni_required
def leave_event(request, event_id):
    """Leave event view"""
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

@login_required
def alumni_directory(request):
    """Alumni directory view"""
    search_query = request.GET.get('search', '')
    graduation_year = request.GET.get('graduation_year', '')
    degree_program = request.GET.get('degree_program', '')
    
    # Base queryset
    alumni_list = Alumni.objects.select_related('user').filter(is_active=True)
    
    # Apply filters
    if search_query:
        alumni_list = alumni_list.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(degree_program__icontains=search_query) |
            Q(current_job_title__icontains=search_query) |
            Q(current_company__icontains=search_query) |
            Q(industry__icontains=search_query)
        )
    
    if graduation_year:
        alumni_list = alumni_list.filter(graduation_year=graduation_year)
    
    if degree_program:
        alumni_list = alumni_list.filter(degree_program__icontains=degree_program)
    
    # Get unique graduation years and degree programs for filters
    graduation_years = Alumni.objects.values_list('graduation_year', flat=True).distinct().order_by('-graduation_year')
    degree_programs = Alumni.objects.values_list('degree_program', flat=True).distinct().order_by('degree_program')
    
    # Paginate results
    paginator = Paginator(alumni_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'alumni_list': page_obj,
        'search_query': search_query,
        'selected_graduation_year': graduation_year,
        'selected_degree_program': degree_program,
        'graduation_years': graduation_years,
        'degree_programs': degree_programs,
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
            (Q(requester=current_alumni, recipient=alumni) | 
             Q(requester=alumni, recipient=current_alumni)),
            status='accepted'
        ).exists():
            show_connections = True
            networking_connections = AlumniNetworking.objects.filter(
                Q(requester=alumni) | Q(recipient=alumni),
                status='accepted'
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


def test_demo(request):
    """
    Alumni system test and demo page for teachers.
    """
    if not request.user.groups.filter(name='Teachers').exists():
        messages.error(request, 'Only teachers can access this feature.')
        return redirect('teacher_dashboard')
    
    return render(request, 'alumni/test_demo.html')
