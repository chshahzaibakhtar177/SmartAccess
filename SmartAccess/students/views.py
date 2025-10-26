from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import timedelta
import requests
import json

# Import from the modular models
from students.models import Student
from students.forms import StudentForm, StudentPhotoForm
from authentication.decorators import student_required, teacher_required
from attendance.models import EntryLog

# All student-related functions are now implemented in this module

# Students management views - migrated from legacy student app

def register_student(request):
    """Student registration view - migrated from legacy student app"""
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)

            # 1. Create User account
            username = student.roll_number
            raw_password = student.name

            user = User.objects.create_user(username=username, password=raw_password)
            user.save()

            # 2. Assign the user to "Students" group
            group, created = Group.objects.get_or_create(name='Students')
            user.groups.add(group)

            # 3. Link the user to the student
            student.user = user
            student.save()

            form = StudentForm()  # Clear the form
            return render(request, 'students/register.html', {
                'form': form,
                'students': Student.objects.all(),
                'message': f"Student created. Login: {username}, Password: {raw_password}"
            })
    else:
        form = StudentForm()

    students = Student.objects.all()
    return render(request, 'students/register.html', {'form': form, 'students': students})


@teacher_required
def edit_student(request, student_id):
    """Edit student view - migrated from legacy student app"""
    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('register_student')
    else:
        form = StudentForm(instance=student)

    students = Student.objects.all()
    return render(request, 'students/register.html', {
        'form': form,
        'students': students,
        'edit_mode': True,
        'editing_student': student,
    })


@teacher_required
def delete_student(request, student_id):
    """Delete student view - migrated from legacy student app"""
    student = get_object_or_404(Student, id=student_id)
    student.delete()
    return redirect('register_student')


def student_detail(request, student_id):
    """Student detail view - migrated from legacy student app"""
    student = get_object_or_404(Student, id=student_id)
    logs = EntryLog.objects.filter(student=student).order_by('-timestamp')

    total_visits = logs.filter(action='in').count()

    visits = []
    check_in_time = None
    for log in logs.order_by('timestamp'):
        if log.action == 'in':
            check_in_time = log.timestamp
        elif log.action == 'out' and check_in_time:
            visits.append((check_in_time, log.timestamp))
            check_in_time = None

    if check_in_time:
        visits.append((check_in_time, timezone.now()))

    total_duration = sum([(out - inn).total_seconds() for inn, out in visits])
    average_duration = (total_duration / total_visits) if total_visits > 0 else 0

    # Calculate hours and minutes from average_duration seconds
    avg_hours = int(average_duration // 3600)
    avg_minutes = int((average_duration % 3600) // 60)

    context = {
        'student': student,
        'logs': logs,
        'total_visits': total_visits,
        'average_duration': average_duration,  # seconds, optional if needed
        'avg_hours': avg_hours,
        'avg_minutes': avg_minutes,
    }
    return render(request, 'students/student_detail.html', context)


@login_required
@student_required
def update_photo(request):
    """Update student photo view - migrated from legacy student app"""
    if request.method == 'POST':
        try:
            form = StudentPhotoForm(request.POST, request.FILES, instance=request.user.student_profile)
        except Student.DoesNotExist:
            messages.error(request, "Student profile not found. Please contact administrator.")
            return redirect('login')
        if form.is_valid():
            form.save()
            messages.success(request, 'Photo updated successfully!')
            return redirect('student_dashboard')
    return redirect('student_dashboard')


def student_search(request):
    """Student search view - migrated from legacy student app"""
    query = request.GET.get('q', '')
    students = Student.objects.filter(
        Q(name__icontains=query) |
        Q(roll_number__icontains=query)
    )
    return JsonResponse({'students': list(students.values())})


def student_search_api(request):
    """Student search API view - migrated from legacy student app"""
    q = request.GET.get('q', '')
    students = Student.objects.filter(name__icontains=q)[:10]
    results = [{'id': s.id, 'name': s.name, 'roll_number': s.roll_number} for s in students]
    return JsonResponse(results, safe=False)


# ===================================================================
# NFC CARD MANAGEMENT FUNCTIONS
# Migrated from legacy student app for complete modularization
# ===================================================================

@login_required
def assign_card_page(request, student_id):
    """NFC Card assignment page for students"""
    student = get_object_or_404(Student, id=student_id)
    context = {
        'student': student,
    }
    return render(request, 'students/assign_card.html', context)


def nfc_scanner_interface(request):
    """Interface for NFC scanner communication"""
    try:
        # Basic connectivity check to Raspberry Pi
        response = requests.get('http://192.168.1.100:5000/status', timeout=5)
        if response.status_code == 200:
            return {'success': True, 'status': 'Scanner online'}
        else:
            return {'success': False, 'error': 'Scanner not responding'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'Cannot connect to NFC scanner. Please check if Raspberry Pi Flask server is running on port 5000.'}
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Scanner timeout - no card detected within 30 seconds'}
    except Exception as e:
        return {'success': False, 'error': f'Scanner error: {str(e)}'}


@login_required
def assign_card_request(request, student_id):
    """Process card assignment request to Raspberry Pi"""
    # Check permissions
    if not (request.user.is_superuser or request.user.groups.filter(name='Teachers').exists()):
        messages.error(request, "Access denied. Teacher or admin privileges required.")
        return redirect('login')  # Redirect to login instead of dashboard_redirect
    
    try:
        student = Student.objects.get(id=student_id)
        
        # Check if student already has a card
        if student.nfc_uid:
            messages.warning(request, f"{student.name} already has an assigned NFC card.")
            return redirect('login')
        
        # Send request to Raspberry Pi to scan card
        pi_response = request_card_scan_from_pi(student.roll_number)
        
        if pi_response.get('success'):
            # Card scanned successfully, update student
            new_uid = pi_response.get('card_id')
            
            # Check if card is already assigned to another student
            existing_student = Student.objects.filter(nfc_uid=new_uid).first()
            if existing_student:
                messages.error(request, f"Card already assigned to {existing_student.name} ({existing_student.roll_number}). Please scan a new card.")
                return redirect('assign_card_page', student_id=student_id)
            
            student.nfc_uid = new_uid
            student.save()
            messages.success(request, f"NFC card successfully assigned to {student.name}!")
            
        else:
            error_msg = pi_response.get('error', 'Unknown error')
            if 'timeout' in error_msg.lower():
                messages.error(request, "No card detected within 30 seconds. Please try again.")
            else:
                messages.error(request, f"Failed to assign card: {error_msg}")
            return redirect('assign_card_page', student_id=student_id)
            
    except Student.DoesNotExist:
        messages.error(request, "Student not found")
    
    return redirect('login')


@login_required  
def remove_card(request, student_id):
    """Remove NFC card assignment from student"""
    # Check permissions
    if not (request.user.is_superuser or request.user.groups.filter(name='Teachers').exists()):
        messages.error(request, "Access denied. Teacher or admin privileges required.")
        return redirect('login')
    
    try:
        student = Student.objects.get(id=student_id)
        if student.nfc_uid:
            student.nfc_uid = None
            student.save()
            messages.success(request, f"NFC card removed from {student.name}")
        else:
            messages.warning(request, f"{student.name} has no assigned NFC card")
            
    except Student.DoesNotExist:
        messages.error(request, "Student not found")
    
    return redirect('login')


def request_card_scan_from_pi(roll_number):
    """Send request to Raspberry Pi to scan a card for assignment"""
    try:
        # Replace with your actual Pi IP
        pi_url = "http://172.20.10.2:5000/scan-for-assignment"
        payload = {
            'roll_number': roll_number,
            'action': 'assign_card'
        }
        
        print(f"DEBUG: Sending request to {pi_url}")  # Debug info
        response = requests.post(pi_url, json=payload, timeout=35)  # 35 second timeout (30 + buffer)
        
        print(f"DEBUG: Response status: {response.status_code}")  # Debug info
        print(f"DEBUG: Response text: {response.text}")  # Debug info
        
        # Check if response is successful
        if response.status_code != 200:
            return {'success': False, 'error': f'Pi server error: {response.status_code}'}
        
        # Try to parse JSON
        try:
            return response.json()
        except json.JSONDecodeError:
            return {'success': False, 'error': f'Invalid response from Pi scanner: {response.text[:100]}'}
        
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'Cannot connect to NFC scanner. Please check if Raspberry Pi Flask server is running on port 5000.'}
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Scanner timeout - no card detected within 30 seconds'}
    except Exception as e:
        return {'success': False, 'error': f'Scanner error: {str(e)}'}


# ===================================================================
# PROFILE VIEW FUNCTION
# Migrated from legacy student app for complete modularization
# ===================================================================

@login_required
def profile_view(request):
    """Profile view for all user types"""
    user = request.user
    
    # Get today and last 30 days for statistics
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    context = {}
    
    if user.groups.filter(name='Students').exists():
        try:
            student = user.student_profile
            entry_logs = EntryLog.objects.filter(
                student=student,
                timestamp__date__gte=last_30_days
            ).order_by('-timestamp')[:10]
            
            context = {
                'user_type': 'student',
                'student': student,
                'recent_entries': entry_logs,
                'entries_count': entry_logs.count()
            }
        except Student.DoesNotExist:
            context = {'user_type': 'student', 'error': 'Student profile not found'}
    
    elif user.groups.filter(name='Teachers').exists():
        context = {
            'user_type': 'teacher',
            'teacher_name': user.get_full_name() or user.username
        }
    
    else:
        context = {
            'user_type': 'admin',
            'admin_name': user.get_full_name() or user.username
        }
    
    return render(request, 'authentication/profile.html', context)
