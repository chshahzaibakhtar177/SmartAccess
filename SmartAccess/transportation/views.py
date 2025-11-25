from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import json
import logging
import threading

from .models import Bus, Route, TransportLog, StudentBusAssignment
from .forms import BusForm, RouteForm, StudentBusAssignmentForm
from authentication.decorators import teacher_required, student_required
from students.models import Student
from teachers.models import Teacher

# Setup logging
logger = logging.getLogger(__name__)


def send_transport_email(user, user_type, action, bus, route, timestamp, location):
    """
    Send email notification when user boards or alights from bus
    
    Args:
        user: User object (Student or Teacher)
        user_type: 'student' or 'teacher'
        action: 'board' or 'alight'
        bus: Bus object
        route: Route object (can be None)
        timestamp: datetime of the action
        location: boarding/alighting location
    """
    try:
        # Generate email address
        if user_type == 'student':
            student = user.student_profile
            email_address = f"{student.roll_number}@{settings.STUDENT_EMAIL_DOMAIN}"
            user_name = student.name
            user_id = student.roll_number
        else:
            teacher = user.teacher_profile
            email_address = user.email  # Teachers use their account email
            user_name = teacher.name
            user_id = teacher.employee_id
        
        # Determine action text
        action_text = "boarded" if action == 'board' else "alighted from"
        action_title = "Bus Boarding" if action == 'board' else "Bus Alighting"
        
        # Email subject
        subject = f"Transportation {action_title} Notification - {user_id}"
        
        # Email message
        route_info = f"Route: {route.name}" if route else "Route: Not assigned"
        message = f"""
Dear {user_name},

This is to confirm that you have {action_text} the university bus.

Details:
- Bus Number: {bus.bus_number}
- {route_info}
- Driver: {bus.driver_name}
- Location: {location}
- Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- User Type: {user_type.title()}

If this was not you, please contact the transport office immediately.

Best regards,
SmartAccess Transportation System
CUI Sahiwal
"""
        
        # Send email in background thread to avoid blocking response
        def send_email_async():
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email_address],
                    fail_silently=False,
                )
                logger.info(f"Transport email sent to {email_address} for {action} action")
            except Exception as email_error:
                logger.error(f"Failed to send transport email in background: {email_error}")
        
        # Start email sending in background
        email_thread = threading.Thread(target=send_email_async, daemon=True)
        email_thread.start()
        logger.info(f"Transport email queued for {email_address} for {action} action")
        
    except Exception as e:
        logger.error(f"Failed to queue transport email: {str(e)}")


# ============ TEACHER VIEWS ============

@login_required
@teacher_required
def transportation_dashboard(request):
    """Transportation dashboard showing buses, routes, and recent logs"""
    today = timezone.now().date()
    
    # Get statistics
    total_buses = Bus.objects.filter(is_active=True).count()
    total_routes = Route.objects.filter(status='active').count()
    total_assigned_students = StudentBusAssignment.objects.filter(is_active=True).count()
    today_logs = TransportLog.objects.filter(boarding_time__date=today).count()
    
    # Recent transport logs
    recent_logs = TransportLog.objects.select_related(
        'user', 'bus', 'route'
    ).order_by('-boarding_time')[:10]
    
    # Bus utilization data
    bus_utilization = Bus.objects.filter(is_active=True).annotate(
        today_usage=Count('transport_logs', filter=Q(transport_logs__boarding_time__date=today)),
        assigned_students_count=Count('assigned_students', filter=Q(assigned_students__is_active=True))
    ).order_by('-today_usage')[:5]
    
    # Popular routes
    popular_routes = Route.objects.filter(status='active').annotate(
        usage_count=Count('transport_logs', filter=Q(transport_logs__boarding_time__date=today))
    ).order_by('-usage_count')[:5]
    
    context = {
        'total_buses': total_buses,
        'total_routes': total_routes,
        'total_assigned_students': total_assigned_students,
        'today_logs': today_logs,
        'recent_logs': recent_logs,
        'bus_utilization': bus_utilization,
        'popular_routes': popular_routes,
        'today': today,
    }
    
    return render(request, 'transportation/dashboard.html', context)


@login_required
@teacher_required
def bus_list(request):
    """List all buses"""
    buses = Bus.objects.all().annotate(
        assigned_students_count=Count('assigned_students', filter=Q(assigned_students__is_active=True))
    ).order_by('bus_number')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        buses = buses.filter(
            Q(bus_number__icontains=search_query) |
            Q(driver_name__icontains=search_query) |
            Q(route__icontains=search_query)
        )
    
    # Calculate statistics
    total_buses = Bus.objects.count()
    active_buses = Bus.objects.filter(is_active=True).count()
    inactive_buses = Bus.objects.filter(is_active=False).count()
    
    # Pagination
    paginator = Paginator(buses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_buses': total_buses,
        'active_buses': active_buses,
        'inactive_buses': inactive_buses,
        'maintenance_buses': 0,  # Bus model doesn't have maintenance status
    }
    
    return render(request, 'transportation/bus_list.html', context)


@login_required
@teacher_required
def bus_create(request):
    """Create a new bus"""
    if request.method == 'POST':
        form = BusForm(request.POST)
        if form.is_valid():
            bus = form.save()
            messages.success(request, f'Bus {bus.bus_number} added successfully!')
            return redirect('transportation:bus_list')
    else:
        form = BusForm()
    
    context = {'form': form, 'action': 'Create'}
    return render(request, 'transportation/bus_form.html', context)


@login_required
@teacher_required
def bus_edit(request, pk):
    """Edit an existing bus"""
    bus = get_object_or_404(Bus, pk=pk)
    
    if request.method == 'POST':
        form = BusForm(request.POST, instance=bus)
        if form.is_valid():
            bus = form.save()
            messages.success(request, f'Bus {bus.bus_number} updated successfully!')
            return redirect('transportation:bus_detail', pk=bus.pk)
    else:
        form = BusForm(instance=bus)
    
    context = {'form': form, 'bus': bus, 'action': 'Edit'}
    return render(request, 'transportation/bus_form.html', context)


@login_required
@teacher_required
def bus_delete(request, pk):
    """Delete a bus"""
    bus = get_object_or_404(Bus, pk=pk)
    
    # Check if bus has assigned students
    assigned_count = StudentBusAssignment.objects.filter(bus=bus, is_active=True).count()
    if assigned_count > 0:
        messages.error(request, f'Cannot delete bus {bus.bus_number}. It has {assigned_count} assigned student(s). Please reassign them first.')
        return redirect('transportation:bus_detail', pk=pk)
    
    bus_number = bus.bus_number
    bus.delete()
    messages.success(request, f'Bus {bus_number} deleted successfully!')
    return redirect('transportation:bus_list')


@login_required
@teacher_required
def bus_detail(request, pk):
    """View bus details"""
    bus = get_object_or_404(Bus, pk=pk)
    assigned_students = StudentBusAssignment.objects.filter(
        bus=bus
    ).select_related('student', 'student__user').order_by('student__roll_number')
    
    # Recent logs for this bus
    recent_logs = TransportLog.objects.filter(
        bus=bus
    ).select_related('user', 'route').order_by('-boarding_time')[:10]
    
    # Calculate total trips this month
    from datetime import datetime
    this_month = datetime.now().date().replace(day=1)
    total_trips = TransportLog.objects.filter(
        bus=bus,
        boarding_time__date__gte=this_month
    ).count()
    
    context = {
        'bus': bus,
        'assigned_students': assigned_students,
        'recent_logs': recent_logs,
        'total_trips': total_trips,
    }
    return render(request, 'transportation/bus_detail.html', context)


# ============ ROUTE VIEWS ============

@login_required
@teacher_required
def route_list(request):
    """List all routes"""
    routes = Route.objects.all().annotate(
        assigned_students_count=Count('assigned_students', filter=Q(assigned_students__is_active=True))
    ).order_by('route_name')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        routes = routes.filter(
            Q(route_name__icontains=search_query) |
            Q(start_location__icontains=search_query) |
            Q(end_location__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(routes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'transportation/route_list.html', context)


@login_required
@teacher_required
def route_create(request):
    """Create a new route"""
    if request.method == 'POST':
        form = RouteForm(request.POST)
        if form.is_valid():
            route = form.save()
            messages.success(request, f'Route "{route.route_name}" created successfully!')
            return redirect('transportation:route_list')
    else:
        form = RouteForm()
    
    context = {'form': form, 'action': 'Create'}
    return render(request, 'transportation/route_form.html', context)


@login_required
@teacher_required
def route_edit(request, pk):
    """Edit an existing route"""
    route = get_object_or_404(Route, pk=pk)
    
    if request.method == 'POST':
        form = RouteForm(request.POST, instance=route)
        if form.is_valid():
            route = form.save()
            messages.success(request, f'Route "{route.route_name}" updated successfully!')
            return redirect('transportation:route_detail', pk=route.pk)
    else:
        form = RouteForm(instance=route)
    
    context = {'form': form, 'route': route, 'action': 'Edit'}
    return render(request, 'transportation/route_form.html', context)


@login_required
@teacher_required
def route_delete(request, pk):
    """Delete a route"""
    route = get_object_or_404(Route, pk=pk)
    
    # Check if route has assigned students
    assigned_count = StudentBusAssignment.objects.filter(route=route, is_active=True).count()
    if assigned_count > 0:
        messages.error(request, f'Cannot delete route "{route.route_name}". It has {assigned_count} assigned student(s). Please reassign them first.')
        return redirect('transportation:route_detail', pk=pk)
    
    route_name = route.route_name
    route.delete()
    messages.success(request, f'Route "{route_name}" deleted successfully!')
    return redirect('transportation:route_list')


@login_required
@teacher_required
def route_detail(request, pk):
    """View route details"""
    route = get_object_or_404(Route, pk=pk)
    assigned_students = StudentBusAssignment.objects.filter(
        route=route, is_active=True
    ).select_related('student', 'student__user', 'bus').order_by('student__roll_number')
    
    context = {
        'route': route,
        'assigned_students': assigned_students,
    }
    return render(request, 'transportation/route_detail.html', context)


# ============ STUDENT ASSIGNMENT VIEWS ============

@login_required
@teacher_required
def student_assignment_list(request):
    """List all student bus assignments"""
    assignments = StudentBusAssignment.objects.filter(
        is_active=True
    ).select_related('student', 'bus', 'route').order_by('bus__bus_number', 'student__roll_number')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        assignments = assignments.filter(
            Q(student__roll_number__icontains=search_query) |
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(bus__bus_number__icontains=search_query) |
            Q(route__route_name__icontains=search_query)
        )
    
    # Filter by bus
    bus_filter = request.GET.get('bus', '')
    if bus_filter:
        assignments = assignments.filter(bus_id=bus_filter)
    
    # Pagination
    paginator = Paginator(assignments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all buses for filter dropdown
    buses = Bus.objects.filter(is_active=True).order_by('bus_number')
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'buses': buses,
        'bus_filter': bus_filter,
    }
    
    return render(request, 'transportation/student_assignment_list.html', context)


@login_required
@teacher_required
def student_assignment_create(request):
    """Create a new student bus assignment"""
    bus_id = request.GET.get('bus_id')
    initial_data = {}
    preselected_bus = None
    
    if bus_id:
        try:
            preselected_bus = Bus.objects.get(pk=bus_id)
            initial_data['bus'] = preselected_bus
        except Bus.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = StudentBusAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save()
            messages.success(request, f'Student {assignment.student.roll_number} assigned to bus {assignment.bus.bus_number} successfully!')
            if bus_id:
                return redirect('transportation:bus_detail', pk=bus_id)
            return redirect('transportation:student_assignment_list')
    else:
        form = StudentBusAssignmentForm(initial=initial_data)
    
    context = {
        'form': form, 
        'action': 'Assign Student to Bus',
        'preselected_bus': preselected_bus
    }
    return render(request, 'transportation/student_assignment_form.html', context)


@login_required
@teacher_required
def student_assignment_edit(request, pk):
    """Edit a student bus assignment"""
    assignment = get_object_or_404(StudentBusAssignment, pk=pk)
    
    if request.method == 'POST':
        form = StudentBusAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            assignment = form.save()
            messages.success(request, f'Assignment for {assignment.student.roll_number} updated successfully!')
            return redirect('transportation:student_assignment_list')
    else:
        form = StudentBusAssignmentForm(instance=assignment)
    
    context = {'form': form, 'assignment': assignment, 'action': 'Edit Assignment'}
    return render(request, 'transportation/student_assignment_form.html', context)


@login_required
@teacher_required
def student_assignment_delete(request, pk):
    """Delete/deactivate a student bus assignment"""
    assignment = get_object_or_404(StudentBusAssignment, pk=pk)
    
    student_roll = assignment.student.roll_number
    bus_number = assignment.bus.bus_number
    assignment.delete()
    
    messages.success(request, f'Assignment removed for student {student_roll} from bus {bus_number}!')
    return redirect('transportation:student_assignment_list')


# ============ TRANSPORT LOGS ============

@login_required
def transport_logs(request):
    """View transport logs - accessible to both students and teachers"""
    logs = TransportLog.objects.select_related('user', 'bus', 'route').order_by('-boarding_time')
    
    # Filter by user if student
    if hasattr(request.user, 'student_profile'):
        logs = logs.filter(user=request.user)
        template = 'transportation/student_transport_logs.html'
    else:
        template = 'transportation/transport_logs.html'
    
    # Search and filter functionality (for teachers)
    if not hasattr(request.user, 'student_profile'):
        search_query = request.GET.get('search', '')
        if search_query:
            logs = logs.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(bus__bus_number__icontains=search_query) |
                Q(route__route_name__icontains=search_query)
            )
        
        # Date filter
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        if date_from:
            logs = logs.filter(boarding_time__date__gte=date_from)
        if date_to:
            logs = logs.filter(boarding_time__date__lte=date_to)
    else:
        search_query = ''
        date_from = ''
        date_to = ''
    
    # Pagination
    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, template, context)


# ============ STUDENT VIEW ============

@login_required
@student_required
def student_transportation_dashboard(request):
    """Student transportation dashboard showing their assigned bus and usage logs"""
    try:
        student = request.user.student_profile
        assignment = StudentBusAssignment.objects.filter(
            student=student, is_active=True
        ).select_related('bus', 'route').first()
        
        # Get student's transport logs
        today = timezone.now().date()
        this_month = today.replace(day=1)
        
        logs_this_month = TransportLog.objects.filter(
            user=request.user,
            boarding_time__date__gte=this_month
        ).count()
        
        recent_logs = TransportLog.objects.filter(
            user=request.user
        ).select_related('bus', 'route').order_by('-boarding_time')[:10]
        
        context = {
            'assignment': assignment,
            'logs_this_month': logs_this_month,
            'recent_logs': recent_logs,
        }
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        context = {
            'assignment': None,
            'logs_this_month': 0,
            'recent_logs': [],
        }
    
    return render(request, 'transportation/student_dashboard.html', context)


# ============ ANALYTICS ============

@login_required
@teacher_required
def transportation_analytics(request):
    """Transportation analytics and reports"""
    today = timezone.now().date()
    last_week = today - timedelta(days=7)
    last_month = today - timedelta(days=30)
    
    # Daily usage statistics
    daily_stats = TransportLog.objects.filter(
        boarding_time__date__gte=last_week
    ).extra({
        'day': "date(boarding_time)"
    }).values('day').annotate(
        total_rides=Count('id'),
        unique_users=Count('user', distinct=True)
    ).order_by('day')
    
    # Bus utilization
    bus_stats = Bus.objects.filter(is_active=True).annotate(
        monthly_rides=Count('transport_logs', filter=Q(transport_logs__boarding_time__date__gte=last_month)),
        weekly_rides=Count('transport_logs', filter=Q(transport_logs__boarding_time__date__gte=last_week)),
        assigned_count=Count('assigned_students', filter=Q(assigned_students__is_active=True))
    ).order_by('-monthly_rides')
    
    # Route popularity
    route_stats = Route.objects.filter(status='active').annotate(
        monthly_usage=Count('transport_logs', filter=Q(transport_logs__boarding_time__date__gte=last_month))
    ).order_by('-monthly_usage')
    
    context = {
        'daily_stats': daily_stats,
        'bus_stats': bus_stats,
        'route_stats': route_stats,
        'today': today,
        'last_week': last_week,
        'last_month': last_month,
    }
    
    return render(request, 'transportation/analytics.html', context)


# ============ API ENDPOINTS ============

@login_required
def api_log_transport(request):
    """API endpoint for logging transport via NFC"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nfc_uid = data.get('nfc_uid')
            bus_id = data.get('bus_id')
            boarding_location = data.get('boarding_location', 'University Gate')
            action = data.get('action', 'board')
            
            # Find user by NFC UID
            user = None
            user_type = None
            
            try:
                student = Student.objects.get(nfc_uid=nfc_uid)
                user = student.user
                user_type = 'student'
            except Student.DoesNotExist:
                pass
            
            if not user:
                try:
                    teacher = Teacher.objects.get(nfc_uid=nfc_uid)
                    user = teacher.user
                    user_type = 'teacher'
                except Teacher.DoesNotExist:
                    pass
            
            if not user:
                return JsonResponse({
                    'success': False,
                    'message': 'NFC card not found in system'
                }, status=404)
            
            bus = get_object_or_404(Bus, id=bus_id)
            
            # Get user's assigned route if they're a student
            route = None
            if user_type == 'student':
                try:
                    assignment = StudentBusAssignment.objects.get(
                        student=user.student_profile,
                        is_active=True
                    )
                    route = assignment.route
                except StudentBusAssignment.DoesNotExist:
                    pass
            
            if action == 'board':
                existing_log = TransportLog.objects.filter(
                    user=user,
                    alighting_time__isnull=True
                ).first()
                
                if existing_log:
                    return JsonResponse({
                        'success': False,
                        'message': 'User is already on board a bus'
                    }, status=400)
                
                transport_log = TransportLog.objects.create(
                    user=user,
                    user_type=user_type,
                    nfc_uid=nfc_uid,
                    bus=bus,
                    route=route,
                    boarding_status='boarded',
                    boarding_location=boarding_location,
                    boarding_time=timezone.now()
                )
                
                # Send email notification (non-blocking)
                try:
                    send_transport_email(
                        user=user,
                        user_type=user_type,
                        action='board',
                        bus=bus,
                        route=route,
                        timestamp=transport_log.boarding_time,
                        location=boarding_location
                    )
                except Exception as e:
                    logger.error(f"Transport email notification failed: {str(e)}")
                    # Continue processing even if email fails
                
                return JsonResponse({
                    'success': True,
                    'message': f'{user.get_full_name()} boarded bus {bus.bus_number}',
                    'log_id': transport_log.id
                })
            
            elif action == 'alight':
                transport_log = TransportLog.objects.filter(
                    user=user,
                    alighting_time__isnull=True
                ).order_by('-boarding_time').first()
                
                if not transport_log:
                    return JsonResponse({
                        'success': False,
                        'message': 'No active boarding found for this user'
                    }, status=400)
                
                transport_log.alighting_time = timezone.now()
                transport_log.boarding_status = 'alighted'
                transport_log.save()
                
                # Send email notification (non-blocking)
                try:
                    send_transport_email(
                        user=user,
                        user_type=transport_log.user_type,
                        action='alight',
                        bus=transport_log.bus,
                        route=transport_log.route,
                        timestamp=transport_log.alighting_time,
                        location=boarding_location  # Use same location variable
                    )
                except Exception as e:
                    logger.error(f"Transport email notification failed: {str(e)}")
                    # Continue processing even if email fails
                
                return JsonResponse({
                    'success': True,
                    'message': f'{user.get_full_name()} alighted from bus {transport_log.bus.bus_number}',
                    'travel_duration': str(transport_log.get_travel_duration())
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Only POST method allowed'
    }, status=405)


@login_required
def api_bus_status(request, bus_id):
    """API endpoint to get current bus status"""
    try:
        bus = get_object_or_404(Bus, id=bus_id)
        current_passengers = TransportLog.objects.filter(
            bus=bus,
            alighting_time__isnull=True
        ).select_related('user')
        
        passengers_data = [{
            'name': log.user.get_full_name(),
            'user_type': log.user_type,
            'boarding_time': log.boarding_time.isoformat(),
            'boarding_location': log.boarding_location
        } for log in current_passengers]
        
        return JsonResponse({
            'success': True,
            'bus_number': bus.bus_number,
            'capacity': bus.capacity,
            'current_passengers': len(passengers_data),
            'passengers': passengers_data,
            'driver_name': bus.driver_name,
            'route': bus.route
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)
