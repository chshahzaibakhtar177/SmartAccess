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
from authentication.decorators import teacher_required, student_required

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
            
            # Check if user is already registered (exclude cancelled registrations)
            try:
                user_registration = EventRegistration.objects.get(
                    event=event, 
                    student=student
                )
                # If registration is cancelled, treat as not registered
                if user_registration.status == 'cancelled':
                    user_registration = None
            except EventRegistration.DoesNotExist:
                pass
            
            # Check if user has attendance record
            if user_registration:
                try:
                    user_attendance = EventAttendance.objects.get(
                        registration=user_registration
                    )
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
        'registration_percentage': round((event.registered_count / event.max_capacity) * 100, 2) if event.max_capacity > 0 else 0,
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
@student_required
def register_for_event(request, event_id):
    """Register student for an event"""
    event = get_object_or_404(Event, id=event_id)
    
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
            # Check if event is still open and has capacity
            if not event.is_registration_open:
                messages.error(request, "Registration for this event is closed.")
                return redirect('event_detail', event_id=event.id)
            
            # Check capacity before reactivating
            if event.registered_count >= event.max_capacity:
                messages.error(request, "Event is full and registration is closed.")
                return redirect('event_detail', event_id=event.id)
            
            # Reactivate cancelled registration
            existing_registration.status = 'confirmed'
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
@student_required
def cancel_event_registration(request, event_id):
    """Cancel student's event registration"""
    event = get_object_or_404(Event, id=event_id)
    
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
    """NFC Event Check-in API for Raspberry Pi scanners"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            card_id = data.get('card_id')
            event_id = data.get('event_id')
            checkin_method = data.get('checkin_method', 'nfc')
            
            if not card_id or not event_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing card_id or event_id'
                }, status=400)
            
            # Find student by card_id
            try:
                student = Student.objects.get(nfc_card_id=card_id)
            except Student.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'No student found with card ID: {card_id}'
                }, status=404)
            
            # Find event
            try:
                event = Event.objects.get(id=event_id, is_active=True)
            except Event.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Event not found or inactive: {event_id}'
                }, status=404)
            
            # Check if student is registered
            try:
                registration = EventRegistration.objects.get(
                    event=event,
                    student=student,
                    status='confirmed'
                )
            except EventRegistration.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Student {student.roll_number} is not registered for this event'
                }, status=400)
            
            # Check if already checked in
            existing_attendance = EventAttendance.objects.filter(
                event=event,
                student=student
            ).first()
            
            if existing_attendance:
                return JsonResponse({
                    'success': False,
                    'error': f'Student {student.roll_number} already checked in at {existing_attendance.checkin_time.strftime("%H:%M:%S")}'
                }, status=400)
            
            # Create attendance record
            attendance = EventAttendance.objects.create(
                event=event,
                student=student,
                registration=registration,
                checkin_method=checkin_method
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Check-in successful',
                'student_name': student.user.get_full_name() or student.user.username,
                'roll_number': student.roll_number,
                'event_title': event.title,
                'checkin_time': attendance.checkin_time.strftime('%Y-%m-%d %H:%M:%S'),
                'registration_status': registration.status
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Only POST requests allowed'
    }, status=405)


@csrf_exempt
def event_nfc_checkout_api(request):
    """NFC Event Check-out API for Raspberry Pi scanners"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            card_id = data.get('card_id')
            event_id = data.get('event_id')
            
            if not card_id or not event_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing card_id or event_id'
                }, status=400)
            
            # Find student by card_id
            try:
                student = Student.objects.get(nfc_card_id=card_id)
            except Student.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'No student found with card ID: {card_id}'
                }, status=404)
            
            # Find event
            try:
                event = Event.objects.get(id=event_id)
            except Event.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Event not found: {event_id}'
                }, status=404)
            
            # Find attendance record
            try:
                attendance = EventAttendance.objects.get(
                    event=event,
                    student=student
                )
            except EventAttendance.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Student {student.roll_number} has not checked in for this event'
                }, status=400)
            
            # Check if already checked out
            if attendance.checkout_time:
                return JsonResponse({
                    'success': False,
                    'error': f'Student {student.roll_number} already checked out at {attendance.checkout_time.strftime("%H:%M:%S")}'
                }, status=400)
            
            # Update checkout time
            attendance.checkout_time = timezone.now()
            attendance.save()  # This will trigger duration calculation in model
            
            return JsonResponse({
                'success': True,
                'message': 'Check-out successful',
                'student_name': student.user.get_full_name() or student.user.username,
                'roll_number': student.roll_number,
                'event_title': event.title,
                'checkin_time': attendance.checkin_time.strftime('%Y-%m-%d %H:%M:%S'),
                'checkout_time': attendance.checkout_time.strftime('%Y-%m-%d %H:%M:%S'),
                'duration_minutes': attendance.duration_minutes
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Only POST requests allowed'
    }, status=405)


@csrf_exempt
def active_events_api(request):
    """API to get list of active events for scanner selection"""
    if request.method == 'GET':
        try:
            # Get active events that are happening today or in the future
            active_events = Event.objects.filter(
                is_active=True,
                start_datetime__gte=timezone.now() - timezone.timedelta(days=1)
            ).order_by('start_datetime')
            
            events_data = []
            for event in active_events:
                events_data.append({
                    'id': event.id,
                    'title': event.title,
                    'start_datetime': event.start_datetime.strftime('%Y-%m-%d %H:%M'),
                    'venue': event.venue,
                    'category': event.category.name if event.category else 'N/A',
                    'registered_count': event.registered_count,
                    'max_capacity': event.max_capacity,
                    'requires_nfc_checkin': event.requires_nfc_checkin
                })
            
            return JsonResponse({
                'success': True,
                'events': events_data,
                'count': len(events_data)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Only GET requests allowed'
    }, status=405)


@csrf_exempt
def nfc_attendance_api(request):
    """
    Simplified NFC attendance API - Auto-detects active event
    Event must be within 30 min of start time and not ended
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        card_id = data.get('card_id')
        
        if not card_id:
            return JsonResponse({'success': False, 'error': 'Missing card_id'}, status=400)
        
        # Find student by NFC card ID
        try:
            student = Student.objects.get(nfc_card_id=card_id)
        except Student.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Student not found. Register your NFC card first.'}, status=404)
        
        # Find active event (30 min before start to end time)
        now = timezone.now()
        active_event = Event.objects.filter(
            is_active=True,
            start_datetime__lte=now + timezone.timedelta(minutes=30),
            end_datetime__gte=now
        ).order_by('start_datetime').first()
        
        if not active_event:
            return JsonResponse({
                'success': False,
                'error': 'No active event. Event must be within 30 min of start time.'
            }, status=404)
        
        # Check if student is registered
        try:
            registration = EventRegistration.objects.get(
                event=active_event,
                student=student,
                status='confirmed'
            )
        except EventRegistration.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': f'Not registered for "{active_event.title}"'
            }, status=403)
        
        # Mark attendance (prevent duplicates)
        attendance, created = EventAttendance.objects.get_or_create(
            registration=registration,
            defaults={
                'event': active_event,
                'student': student,
                'checkin_method': 'nfc'
            }
        )
        
        if not created:
            return JsonResponse({
                'success': False,
                'error': f'Already present at {attendance.checkin_time.strftime("%I:%M %p")}'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'student_name': f"{student.user.first_name} {student.user.last_name}",
            'roll_number': student.roll_number,
            'event_title': active_event.title,
            'attendance_time': attendance.checkin_time.strftime('%I:%M %p'),
            'event_time': f"{active_event.start_datetime.strftime('%I:%M %p')} - {active_event.end_datetime.strftime('%I:%M %p')}"
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


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


@login_required
@teacher_required
def delete_event(request, event_id):
    """Delete an event"""
    event = get_object_or_404(Event, id=event_id)
    
    # Check if there are any confirmed registrations
    confirmed_registrations = event.registrations.filter(status='confirmed').count()
    
    if request.method == 'POST':
        if confirmed_registrations > 0:
            messages.error(request, f'Cannot delete event "{event.title}" because it has {confirmed_registrations} confirmed registrations.')
        else:
            event_title = event.title
            event.delete()
            messages.success(request, f'Event "{event_title}" deleted successfully!')
        return redirect('teacher_event_dashboard')
    
    context = {
        'event': event,
        'confirmed_registrations': confirmed_registrations,
        'page_title': 'Delete Event'
    }
    return render(request, 'events/event_confirm_delete.html', context)
