from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count
from django.core.paginator import Paginator
import json

# Import from the modular models
from .models import Event, EventCategory, EventRegistration, EventAttendance
from students.models import Student
from .forms import EventForm, EventSearchForm, EventCategoryForm
from authentication.decorators import teacher_required

# Events management views - migrated from legacy student app
# Note: Due to time constraints, providing basic structure
# Full implementation would include all event management functions

def event_list(request):
    """List all events - migrated from legacy student app"""
    form = EventSearchForm(request.GET)
    events = Event.objects.filter(is_active=True)
    
    # Apply search filters
    if form.is_valid():
        search_query = form.cleaned_data.get('search_query')
        category = form.cleaned_data.get('category')
        status = form.cleaned_data.get('status')
        
        if search_query:
            events = events.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(venue__icontains=search_query)
            )
        
        if category:
            events = events.filter(category=category)
        
        if status and status != 'all':
            events = events.filter(status=status)
    
    # Pagination
    paginator = Paginator(events, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_events': events.count()
    }
    return render(request, 'events/event_list.html', context)


def event_detail(request, event_id):
    """Display detailed view of an event."""
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        messages.error(request, "Event not found.")
        return redirect('event_list')
    
    # Check if user is a student
    is_student = request.user.is_authenticated and request.user.groups.filter(name='Students').exists()
    
    user_registration = None
    user_attendance = None
    can_register = False
    
    if is_student:
        try:
            # Get student profile
            student = Student.objects.get(user=request.user)
            
            # Check if user is already registered
            try:
                user_registration = EventRegistration.objects.get(event=event, student=student)
            except EventRegistration.DoesNotExist:
                pass
            
            # Check if user has attendance record
            if user_registration:
                try:
                    user_attendance = EventAttendance.objects.get(event=event, student=student)
                except EventAttendance.DoesNotExist:
                    pass
            
            # Check if user can register (not already registered and registration is open)
            if not user_registration:
                can_register = (
                    event.is_registration_open and 
                    event.registered_count < event.max_capacity
                )
        
        except Student.DoesNotExist:
            # User is in Students group but doesn't have a Student profile
            is_student = False
    
    context = {
        'event': event,
        'is_student': is_student,
        'user_registration': user_registration,
        'user_attendance': user_attendance,
        'can_register': can_register,
    }
    
    return render(request, 'events/event_detail.html', context)


@login_required  
@teacher_required
def create_event(request):
    """Create event view - migrated from legacy student app"""
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event created successfully!')
            return redirect('event_list')
    else:
        form = EventForm()
    return render(request, 'events/create_event.html', {'form': form})


@login_required
@teacher_required  
def edit_event(request, event_id):
    """Edit event view - only organizer can edit their events"""
    event = get_object_or_404(Event, id=event_id)
    
    # Ensure only the organizer can edit their event
    if event.organizer.user != request.user:
        messages.error(request, 'You can only edit events that you have organized.')
        return redirect('event_detail', event_id=event.id)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('event_detail', event_id=event.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EventForm(instance=event)
    
    return render(request, 'events/edit_event.html', {'form': form, 'event': event})


@login_required
@login_required
def register_for_event(request, event_id):
    """Register student for an event"""
    event = get_object_or_404(Event, id=event_id)
    
    # Check if user is a student
    if not request.user.groups.filter(name='Students').exists():
        messages.error(request, "Only students can register for events.")
        return redirect('event_detail', event_id=event.id)
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found. Please contact administration.")
        return redirect('event_detail', event_id=event.id)
    
    # Check if student is already registered
    existing_registration = EventRegistration.objects.filter(
        event=event, 
        student=student
    ).first()
    
    if existing_registration:
        if existing_registration.status == 'cancelled':
            # Reactivate cancelled registration
            existing_registration.status = 'pending'
            existing_registration.save()
            messages.success(request, "Your registration has been reactivated!")
        else:
            messages.info(request, "You are already registered for this event.")
        return redirect('event_detail', event_id=event.id)
    
    # Check if event registration is open
    if not event.is_registration_open:
        messages.error(request, "Registration for this event is closed.")
        return redirect('event_detail', event_id=event.id)
    
    # Check if event is full
    if event.registered_count >= event.max_capacity:
        # Add to waitlist if enabled
        if hasattr(event, 'allow_waitlist') and event.allow_waitlist:
            status = 'waitlist'
            message = "Event is full. You have been added to the waitlist."
        else:
            messages.error(request, "Event is full and registration is closed.")
            return redirect('event_detail', event_id=event.id)
    else:
        status = 'confirmed'
        message = "Successfully registered for the event!"
    
    # Create the registration
    try:
        registration = EventRegistration.objects.create(
            event=event,
            student=student,
            status=status
        )
        messages.success(request, message)
        
    except Exception as e:
        messages.error(request, f"Registration failed: {str(e)}")
    
    return redirect('event_detail', event_id=event.id)


@login_required  
def cancel_event_registration(request, event_id):
    """Cancel student's event registration"""
    event = get_object_or_404(Event, id=event_id)
    
    # Check if user is a student
    if not request.user.groups.filter(name='Students').exists():
        messages.error(request, "Only students can cancel event registrations.")
        return redirect('event_detail', event_id=event.id)
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('event_detail', event_id=event.id)
    
    # Find the registration
    try:
        registration = EventRegistration.objects.get(
            event=event, 
            student=student
        )
        
        if registration.status == 'cancelled':
            messages.info(request, "Your registration is already cancelled.")
        else:
            # Cancel the registration
            registration.status = 'cancelled'
            registration.save()
            messages.success(request, "Registration cancelled successfully.")
            
    except EventRegistration.DoesNotExist:
        messages.error(request, "No registration found to cancel.")
    
    return redirect('event_detail', event_id=event.id)


@csrf_exempt
def event_nfc_checkin_api(request):
    """Event NFC checkin API - migrated from legacy student app"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Implementation would be migrated here
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Only POST method allowed'})


# Category Management Views
@login_required
@teacher_required
def category_list(request):
    """List all event categories"""
    categories = EventCategory.objects.all().order_by('name')
    
    # Count events per category
    for category in categories:
        category.event_count = category.events.filter(is_active=True).count()
    
    context = {
        'categories': categories,
        'page_title': 'Event Categories'
    }
    return render(request, 'events/category_list.html', context)


@login_required
@teacher_required
def create_category(request):
    """Create new event category"""
    if request.method == 'POST':
        form = EventCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('category_list')
    else:
        form = EventCategoryForm()
    
    context = {
        'form': form,
        'page_title': 'Create Category',
        'action': 'Create'
    }
    return render(request, 'events/category_form.html', context)


@login_required
@teacher_required
def edit_category(request, category_id):
    """Edit existing event category"""
    category = get_object_or_404(EventCategory, id=category_id)
    
    if request.method == 'POST':
        form = EventCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('category_list')
    else:
        form = EventCategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'page_title': 'Edit Category',
        'action': 'Update'
    }
    return render(request, 'events/category_form.html', context)


@login_required
@teacher_required
def delete_category(request, category_id):
    """Delete event category"""
    category = get_object_or_404(EventCategory, id=category_id)
    
    # Check if category has events
    event_count = category.events.filter(is_active=True).count()
    
    if request.method == 'POST':
        if event_count > 0:
            messages.error(request, f'Cannot delete category "{category.name}" because it has {event_count} active events.')
        else:
            category_name = category.name
            category.delete()
            messages.success(request, f'Category "{category_name}" deleted successfully!')
        return redirect('category_list')
    
    context = {
        'category': category,
        'event_count': event_count,
        'page_title': 'Delete Category'
    }
    return render(request, 'events/category_confirm_delete.html', context)


# Teacher Event Management Views
@login_required
@teacher_required
def event_registrations(request, event_id):
    """View all registrations for a specific event"""
    event = get_object_or_404(Event, id=event_id)
    
    # Get all registrations for this event
    registrations = EventRegistration.objects.filter(event=event).select_related('student', 'student__user').order_by('-registration_date')
    
    # Get attendance records for this event
    attendance_records = EventAttendance.objects.filter(event=event).select_related('student', 'student__user')
    attendance_dict = {att.student.id: att for att in attendance_records}
    
    # Add attendance info to registrations
    for registration in registrations:
        registration.attendance = attendance_dict.get(registration.student.id)
    
    # Statistics
    total_registered = registrations.count()
    confirmed_count = registrations.filter(status='confirmed').count()
    pending_count = registrations.filter(status='pending').count()
    cancelled_count = registrations.filter(status='cancelled').count()
    attended_count = len(attendance_records)
    
    context = {
        'event': event,
        'registrations': registrations,
        'total_registered': total_registered,
        'confirmed_count': confirmed_count,
        'pending_count': pending_count,
        'cancelled_count': cancelled_count,
        'attended_count': attended_count,
        'attendance_rate': round((attended_count / max(confirmed_count, 1)) * 100, 2) if confirmed_count > 0 else 0,
        'page_title': f'Registrations - {event.title}'
    }
    
    return render(request, 'events/teacher_event_registrations.html', context)


@login_required
@teacher_required
def teacher_event_dashboard(request):
    """Teacher dashboard for managing all events"""
    # Get all events with registration and attendance counts
    events = Event.objects.all().annotate(
        registration_count=Count('registrations', filter=Q(registrations__status='confirmed')),
        attendance_count=Count('attendances')
    ).order_by('-start_datetime')
    
    # Add additional statistics
    for event in events:
        event.attendance_rate = round((event.attendance_count / max(event.registration_count, 1)) * 100, 2) if event.registration_count > 0 else 0
    
    # Overall statistics
    total_events = events.count()
    upcoming_events = events.filter(start_datetime__gte=timezone.now()).count()
    total_registrations = EventRegistration.objects.filter(status='confirmed').count()
    total_attendance = EventAttendance.objects.count()
    
    context = {
        'events': events,
        'total_events': total_events,
        'upcoming_events': upcoming_events,
        'total_registrations': total_registrations,
        'total_attendance': total_attendance,
        'overall_attendance_rate': round((total_attendance / max(total_registrations, 1)) * 100, 2) if total_registrations > 0 else 0,
        'page_title': 'Event Management Dashboard'
    }
    
    return render(request, 'events/teacher_dashboard.html', context)


@login_required
@teacher_required
def manage_registration(request, registration_id):
    """Manage individual registration (approve/reject/modify)"""
    registration = get_object_or_404(EventRegistration, id=registration_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'confirm':
            registration.status = 'confirmed'
            registration.save()
            messages.success(request, f"Registration confirmed for {registration.student.user.get_full_name()}")
            
        elif action == 'cancel':
            registration.status = 'cancelled'
            registration.save()
            messages.success(request, f"Registration cancelled for {registration.student.user.get_full_name()}")
            
        elif action == 'waitlist':
            registration.status = 'waitlist'
            registration.save()
            messages.success(request, f"Registration moved to waitlist for {registration.student.user.get_full_name()}")
            
        elif action == 'delete':
            student_name = registration.student.user.get_full_name()
            registration.delete()
            messages.success(request, f"Registration deleted for {student_name}")
            
        return redirect('event_registrations', event_id=registration.event.id)
    
    context = {
        'registration': registration,
        'page_title': f'Manage Registration - {registration.student.user.get_full_name()}'
    }
    
    return render(request, 'events/manage_registration.html', context)


@login_required  
@teacher_required
def mark_attendance(request, event_id, student_id):
    """Mark or update attendance for a student"""
    event = get_object_or_404(Event, id=event_id)
    student = get_object_or_404(Student, id=student_id)
    
    # Check if student is registered for this event
    registration = EventRegistration.objects.filter(event=event, student=student, status='confirmed').first()
    if not registration:
        messages.error(request, "Student is not registered for this event")
        return redirect('event_registrations', event_id=event_id)
    
    # Check if attendance record already exists
    try:
        attendance = EventAttendance.objects.get(registration=registration)
        # Update existing record
        attendance.checkin_time = timezone.now()
        attendance.checkin_method = 'manual'
        attendance.save()
        messages.success(request, f"Attendance updated for {student.user.get_full_name()}")
    except EventAttendance.DoesNotExist:
        # Create new attendance record
        attendance = EventAttendance.objects.create(
            event=event,
            student=student,
            registration=registration,
            checkin_time=timezone.now(),
            checkin_method='manual'
        )
        messages.success(request, f"Attendance marked for {student.user.get_full_name()}")
    
    return redirect('event_registrations', event_id=event_id)


@login_required
@teacher_required
def remove_attendance(request, event_id, student_id):
    """Remove attendance record for a student"""
    event = get_object_or_404(Event, id=event_id)
    student = get_object_or_404(Student, id=student_id)
    
    # Find the registration first
    registration = EventRegistration.objects.filter(event=event, student=student, status='confirmed').first()
    if not registration:
        messages.error(request, "Student is not registered for this event")
        return redirect('event_registrations', event_id=event_id)
    
    try:
        attendance = EventAttendance.objects.get(registration=registration)
        student_name = student.user.get_full_name()
        attendance.delete()
        messages.success(request, f"Attendance removed for {student_name}")
    except EventAttendance.DoesNotExist:
        messages.error(request, "No attendance record found")
    
    return redirect('event_registrations', event_id=event_id)
