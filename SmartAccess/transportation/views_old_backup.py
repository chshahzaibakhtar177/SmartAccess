from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from datetime import timedelta
import json

# Import from the modular models
from transportation.models import Bus, Route, TransportLog
from authentication.decorators import teacher_required
from students.models import Student
from teachers.models import Teacher


# Transportation Management Views

@login_required
@teacher_required
def transportation_dashboard(request):
    """Transportation dashboard showing buses, routes, and recent logs"""
    today = timezone.now().date()
    
    # Get statistics
    total_buses = Bus.objects.filter(is_active=True).count()
    total_routes = Route.objects.filter(status='active').count()
    today_logs = TransportLog.objects.filter(boarding_time__date=today).count()
    
    # Recent transport logs
    recent_logs = TransportLog.objects.select_related(
        'user', 'bus', 'route'
    ).order_by('-boarding_time')[:10]
    
    # Bus utilization data
    bus_utilization = Bus.objects.filter(is_active=True).annotate(
        today_usage=Count('transport_logs', filter=Q(transport_logs__boarding_time__date=today))
    ).order_by('-today_usage')[:5]
    
    # Popular routes
    popular_routes = Route.objects.filter(status='active').annotate(
        usage_count=Count('transport_logs', filter=Q(transport_logs__boarding_time__date=today))
    ).order_by('-usage_count')[:5]
    
    context = {
        'total_buses': total_buses,
        'total_routes': total_routes,
        'today_logs': today_logs,
        'recent_logs': recent_logs,
        'bus_utilization': bus_utilization,
        'popular_routes': popular_routes,
        'today': today,
    }
    
    return render(request, 'transportation/dashboard.html', context)


@login_required
@teacher_required
def bus_management(request):
    """Bus management view - list, add, edit buses"""
    buses = Bus.objects.all().order_by('bus_number')
    
    # Pagination
    paginator = Paginator(buses, 10)
    page_number = request.GET.get('page')
    buses = paginator.get_page(page_number)
    
    context = {
        'buses': buses,
    }
    
    return render(request, 'transportation/bus_management.html', context)


@login_required
@teacher_required
def add_bus(request):
    """Add a new bus"""
    if request.method == 'POST':
        bus_number = request.POST.get('bus_number')
        driver_name = request.POST.get('driver_name')
        driver_contact = request.POST.get('driver_contact')
        capacity = request.POST.get('capacity')
        route = request.POST.get('route')
        
        if Bus.objects.filter(bus_number=bus_number).exists():
            messages.error(request, 'Bus number already exists!')
        else:
            Bus.objects.create(
                bus_number=bus_number,
                driver_name=driver_name,
                driver_contact=driver_contact,
                capacity=int(capacity),
                route=route
            )
            messages.success(request, 'Bus added successfully!')
            return redirect('transportation:bus_management')
    
    return render(request, 'transportation/add_bus.html')


@login_required
@teacher_required
def route_management(request):
    """Route management view - list, add, edit routes"""
    routes = Route.objects.all().order_by('route_name')
    
    # Pagination
    paginator = Paginator(routes, 10)
    page_number = request.GET.get('page')
    routes = paginator.get_page(page_number)
    
    context = {
        'routes': routes,
    }
    
    return render(request, 'transportation/route_management.html', context)


@login_required
@teacher_required
def add_route(request):
    """Add a new route"""
    if request.method == 'POST':
        route_name = request.POST.get('route_name')
        start_location = request.POST.get('start_location')
        end_location = request.POST.get('end_location')
        total_distance = request.POST.get('total_distance')
        estimated_hours = request.POST.get('estimated_hours', '0')
        estimated_minutes = request.POST.get('estimated_minutes', '0')
        
        # Create duration object
        estimated_time = timedelta(
            hours=int(estimated_hours or 0),
            minutes=int(estimated_minutes or 0)
        )
        
        if Route.objects.filter(route_name=route_name).exists():
            messages.error(request, 'Route name already exists!')
        else:
            Route.objects.create(
                route_name=route_name,
                start_location=start_location,
                end_location=end_location,
                total_distance=float(total_distance),
                estimated_time=estimated_time
            )
            messages.success(request, 'Route added successfully!')
            return redirect('transportation:route_management')
    
    return render(request, 'transportation/add_route.html')


@login_required
def transport_logs(request):
    """View transport logs - accessible to both students and teachers"""
    logs = TransportLog.objects.select_related('user', 'bus', 'route').order_by('-boarding_time')
    
    # Filter by user if student
    if hasattr(request.user, 'student_profile'):
        logs = logs.filter(user=request.user)
    
    # Search and filter functionality
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
    
    # Pagination
    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page')
    logs = paginator.get_page(page_number)
    
    context = {
        'logs': logs,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'transportation/transport_logs.html', context)


# API Views for NFC Integration

@login_required
def api_log_transport(request):
    """API endpoint for logging transport via NFC"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nfc_uid = data.get('nfc_uid')
            bus_id = data.get('bus_id')
            boarding_location = data.get('boarding_location', 'University Gate')
            action = data.get('action', 'board')  # 'board' or 'alight'
            
            # Find user by NFC UID
            user = None
            user_type = None
            
            # Check if it's a student
            try:
                student = Student.objects.get(nfc_uid=nfc_uid)
                user = student.user
                user_type = 'student'
            except Student.DoesNotExist:
                pass
            
            # Check if it's a teacher
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
            
            # Get bus and route
            bus = get_object_or_404(Bus, id=bus_id)
            
            # For boarding, create new log
            if action == 'board':
                # Check if user is already on board (no alighting time)
                existing_log = TransportLog.objects.filter(
                    user=user,
                    bus=bus,
                    alighting_time__isnull=True
                ).first()
                
                if existing_log:
                    return JsonResponse({
                        'success': False,
                        'message': 'User is already on board this bus'
                    }, status=400)
                
                # Create new transport log
                transport_log = TransportLog.objects.create(
                    user=user,
                    user_type=user_type,
                    nfc_uid=nfc_uid,
                    bus=bus,
                    route=bus.route if hasattr(bus, 'route') else None,
                    boarding_status='boarded',
                    boarding_location=boarding_location,
                    boarding_time=timezone.now()
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'{user.get_full_name()} boarded bus {bus.bus_number}',
                    'log_id': transport_log.id
                })
            
            # For alighting, update existing log
            elif action == 'alight':
                # Find the most recent boarding log without alighting time
                transport_log = TransportLog.objects.filter(
                    user=user,
                    bus=bus,
                    alighting_time__isnull=True
                ).order_by('-boarding_time').first()
                
                if not transport_log:
                    return JsonResponse({
                        'success': False,
                        'message': 'No active boarding found for this user on this bus'
                    }, status=400)
                
                # Update with alighting time
                transport_log.alighting_time = timezone.now()
                transport_log.boarding_status = 'alighted'
                transport_log.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'{user.get_full_name()} alighted from bus {bus.bus_number}',
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
    """API endpoint to get current bus status and passenger count"""
    try:
        bus = get_object_or_404(Bus, id=bus_id)
        
        # Get current passengers (boarded but not alighted)
        current_passengers = TransportLog.objects.filter(
            bus=bus,
            alighting_time__isnull=True
        ).select_related('user')
        
        passengers_data = []
        for log in current_passengers:
            passengers_data.append({
                'name': log.user.get_full_name(),
                'user_type': log.user_type,
                'boarding_time': log.boarding_time.isoformat(),
                'boarding_location': log.boarding_location
            })
        
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
    
    # Calculate average rides per user
    for stat in daily_stats:
        if stat['unique_users'] > 0:
            stat['avg_rides_per_user'] = stat['total_rides'] / stat['unique_users']
        else:
            stat['avg_rides_per_user'] = 0
    
    # Bus utilization
    bus_stats = Bus.objects.filter(is_active=True).annotate(
        monthly_rides=Count('transport_logs', filter=Q(transport_logs__boarding_time__date__gte=last_month)),
        weekly_rides=Count('transport_logs', filter=Q(transport_logs__boarding_time__date__gte=last_week))
    ).order_by('-monthly_rides')
    
    # Calculate occupancy rate and progress bar width for each bus
    max_bus_rides = max([bus.monthly_rides for bus in bus_stats]) if bus_stats else 1
    for bus in bus_stats:
        if bus.capacity > 0:
            # Calculate average daily usage for the month
            avg_daily_usage = bus.monthly_rides / 30
            bus.occupancy_rate = (avg_daily_usage / bus.capacity) * 100
        else:
            bus.occupancy_rate = 0
        # Calculate progress bar width (0-100%)
        bus.progress_width = (bus.monthly_rides / max_bus_rides * 100) if max_bus_rides > 0 else 0
    
    # Route popularity
    route_stats = Route.objects.filter(status='active').annotate(
        monthly_usage=Count('transport_logs', filter=Q(transport_logs__boarding_time__date__gte=last_month))
    ).order_by('-monthly_usage')
    
    # Calculate progress bar width for routes
    max_route_usage = max([route.monthly_usage for route in route_stats]) if route_stats else 1
    for route in route_stats:
        route.progress_width = (route.monthly_usage / max_route_usage * 100) if max_route_usage > 0 else 0
    
    # Peak hours analysis
    peak_hours = TransportLog.objects.filter(
        boarding_time__date__gte=last_week
    ).extra({
        'hour': "strftime('%%H', boarding_time)"
    }).values('hour').annotate(
        rides_count=Count('id')
    ).order_by('-rides_count')
    
    # Calculate progress bar width for peak hours and avg rides per hour
    max_hour_rides = max([hour['rides_count'] for hour in peak_hours]) if peak_hours else 1
    total_rides_in_peak = sum([hour['rides_count'] for hour in peak_hours])
    avg_rides_per_hour = (total_rides_in_peak / len(peak_hours)) if peak_hours else 0
    
    for hour in peak_hours:
        hour['progress_width'] = (hour['rides_count'] / max_hour_rides * 100) if max_hour_rides > 0 else 0
    
    context = {
        'daily_stats': daily_stats,
        'bus_stats': bus_stats,
        'route_stats': route_stats,
        'peak_hours': peak_hours,
        'avg_rides_per_hour': avg_rides_per_hour,
        'today': today,
        'last_week': last_week,
        'last_month': last_month,
    }
    
    return render(request, 'transportation/analytics.html', context)
