from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.http import JsonResponse
from django.db import models
from django.contrib.auth.decorators import login_required
from .decorators import student_required, teacher_required
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, password_validation, update_session_auth_hash, logout
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import csv
import xlsxwriter
import json
import requests
from io import BytesIO

from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Max
from django.utils.dateparse import parse_date
from datetime import timedelta

from django.utils.timezone import now
from django.db.models import Count
from django.db.models import Max

from .forms import (StudentForm, FineForm, TeacherCreationForm, StudentPhotoForm, TeacherPhotoForm, 
                    EventForm, EventCategoryForm, EventRegistrationForm, EventAttendanceForm, EventSearchForm,
                    BookForm, BookCategoryForm, BookBorrowForm, BookReturnForm, BookReservationForm, BookSearchForm)
from .models import (Student, Fine, EntryLog, Teacher, Event, EventCategory, EventRegistration, EventAttendance,
                     Book, BookCategory, BookBorrow, BookReservation)
from django.http import JsonResponse
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy

@login_required
@teacher_required
def register_student(request):
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
            return render(request, 'student/register.html', {
                'form': form,
                'students': Student.objects.all(),
                'message': f"Student created. Login: {username}, Password: {raw_password}"
            })
    else:
        form = StudentForm()

    students = Student.objects.all()
    return render(request, 'student/register.html', {'form': form, 'students': students})



def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('register_student')
    else:
        form = StudentForm(instance=student)

    students = Student.objects.all()
    return render(request, 'student/register.html', {
        'form': form,
        'students': students,
        'edit_mode': True,
        'editing_student': student,
    })


def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    student.delete()
    return redirect('register_student')



@login_required
def change_password_manual(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        user = request.user
        errors = []

        # Check old password
        if not user.check_password(old_password):
            errors.append("Incorrect old password.")

        # Check if new passwords match
        if new_password1 != new_password2:
            errors.append("New passwords do not match.")

        # Validate password strength
        if new_password1:
            try:
                validate_password(new_password1, user)
            except ValidationError as e:
                errors.extend(e.messages)

        if errors:
            return render(request, 'student/change_password_manual.html', {'errors': errors})

        # Set and save new password
        user.set_password(new_password1)
        user.save()

        # Keep user logged in
        update_session_auth_hash(request, user)

        messages.success(request, "Your password has been changed successfully.")
        return redirect('student_dashboard')

    return render(request, 'student/change_password_manual.html')




def add_fine(request):
    search_query = request.GET.get('search', '')  # Get search term from URL param

    if request.method == 'POST':
        form = FineForm(request.POST)
        if form.is_valid():
            form.save()
            form = FineForm()
    else:
        form = FineForm()

    # Filter fines based on search query if provided
    if search_query:
        fines = Fine.objects.filter(
            student__name__icontains=search_query
        ) | Fine.objects.filter(
            student__roll_number__icontains=search_query
        )
    else:
        fines = Fine.objects.all()

    return render(request, 'fine/add_fine.html', {'form': form, 'fines': fines, 'search_query': search_query})


def edit_fine(request, fine_id):
    fine = get_object_or_404(Fine, id=fine_id)

    if request.method == 'POST':
        form = FineForm(request.POST, instance=fine)
        if form.is_valid():
            form.save()
            return redirect('add_fine')
    else:
        form = FineForm(instance=fine)

    fines = Fine.objects.select_related('student').all()
    return render(request, 'fine/add_fine.html', {
        'form': form,
        'fines': fines,
        'edit_mode': True,
        'editing_fine': fine,
    })


def delete_fine(request, fine_id):
    fine = get_object_or_404(Fine, id=fine_id)
    fine.delete()
    return redirect('add_fine')


def toggle_fine_payment(request, fine_id):
    fine = get_object_or_404(Fine, id=fine_id)
    fine.is_paid = not fine.is_paid
    fine.save()
    return redirect('add_fine')  

def student_search_api(request):
    q = request.GET.get('q', '')
    students = Student.objects.filter(name__icontains=q)[:10]
    results = [{'id': s.id, 'name': s.name, 'roll_number': s.roll_number} for s in students]
    return JsonResponse(results, safe=False)

@login_required
def dashboard_redirect(request):
    user = request.user
    
    # Check if user is superuser first
    if user.is_superuser:
        return redirect('admin_dashboard')
    elif user.groups.filter(name='Teachers').exists():
        return redirect('teacher_dashboard')
    elif user.groups.filter(name='Students').exists():
        return redirect('student_dashboard')
    else:
        messages.error(request, "No dashboard access. Please contact administrator.")
        return redirect('login')  # Redirect to login instead of add_fine
    

@login_required
@student_required
def student_dashboard(request):
    student = request.user.student_profile
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)  # Add this line
    
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
        'show_photo_form': not student.photo  # Only show form if no photo exists
    }
    
    return render(request, 'student/dashboard.html', context)

@login_required
@teacher_required  # Uncomment this
def teacher_dashboard(request):
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
    
    return render(request, 'teacher/dashboard.html', context)






@login_required
def admin_dashboard(request):
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

    # Weekly statistics - Fixed the annotation
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

    # Recent activity
    recent_logs = EntryLog.objects.select_related('student').order_by(
        '-timestamp'
    )[:10]

    # Late entries today
    late_entries = today_entries.filter(
        action='in',
        timestamp__time__hour__gte=9,
        timestamp__time__minute__gte=0
    ).count()

    context = {
        'students_inside': students_inside,
        'today_checkins': today_checkins,
        'today_checkouts': today_checkouts,
        'weekly_logs': weekly_logs,
        'total_fines': total_fines['total'] or 0,
        'unpaid_fines': total_fines['unpaid'] or 0,
        'recent_logs': recent_logs,
        'late_entries': late_entries,
        'total_students': Student.objects.count(),
    }

    return render(request, 'admin/admin_dashboard.html', context)



def simulate_card_scan(request):
    if request.method == 'POST':
        card_id = request.POST.get('card_id')
        try:
            student = Student.objects.get(nfc_uid=card_id)
        except Student.DoesNotExist:
            messages.error(request, "Card not recognized.")
            return redirect('simulate_card_scan')

        now = timezone.now()
        time_gap = timedelta(minutes=0.5)

        last_log = EntryLog.objects.filter(student=student).order_by('-timestamp').first()

        # Prevent duplicate scans
        if last_log and (now - last_log.timestamp < time_gap):
            messages.warning(request, f"Please wait before scanning again.")
            return redirect('simulate_card_scan')

        # Decide next action
        if last_log and last_log.action == 'in':
            action = 'out'
            student.is_in_university = False
            messages.success(request, f"{student.name} checked out.")
        else:
            action = 'in'
            student.is_in_university = True
            messages.success(request, f"{student.name} checked in.")

        # Save new entry
        EntryLog.objects.create(student=student, action=action)
        student.save()

        return redirect('simulate_card_scan')

    return render(request, 'student/simulate_scan.html')

def student_detail(request, student_id):
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
        from django.utils import timezone
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
    return render(request, 'student/student_detail.html', context)





def view_logs(request):
    query = request.GET.get('q', '')
    date_filter = request.GET.get('date', '')

    logs = EntryLog.objects.select_related('student')

    # Apply search filter
    if query:
        logs = logs.filter(
            Q(student__name__icontains=query) |
            Q(student__roll_number__icontains=query)
        )

    # Apply date filter
    if date_filter:
        try:
            parsed_date = parse_date(date_filter)
            logs = logs.filter(timestamp__date=parsed_date)
        except:
            pass

    logs = logs.order_by('-timestamp')

    # Pagination
    paginator = Paginator(logs, 10)  # 10 logs per page
    page_number = request.GET.get('page')
    page_logs = paginator.get_page(page_number)

    return render(request, 'student/view_logs.html', {
        'logs': page_logs,
        'query': query,
        'date_filter': date_filter
    })



@login_required
def add_teacher(request):
    # Restrict access to superusers only
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard_redirect')
        
    if request.method == 'POST':
        form = TeacherCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Create user
            user = User.objects.create_user(username=username, password=password)
            
            # Add to Teachers group
            group, created = Group.objects.get_or_create(name='Teachers')
            user.groups.add(group)
            
            # Create and save teacher profile
            teacher = form.save(commit=False)
            teacher.user = user
            teacher.save()
            
            messages.success(request, f"Teacher {teacher.name} created successfully.")
            return redirect('add_teacher')
    else:
        form = TeacherCreationForm()
    return render(request, 'admin/add_teacher.html', {'form': form})





def export_logs_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="entry_logs.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student Reg #', 'Student Name', 'Date', 'Time', 'Action'])

    logs = EntryLog.objects.all().order_by('-timestamp')
    for log in logs:
        writer.writerow([
            log.student.roll_number,
            log.student.name,
            log.timestamp.date(),
            log.timestamp.time().strftime('%H:%M:%S'),
            log.action,
        ])

    return response

@login_required
@student_required
def update_photo(request):
    if request.method == 'POST':
        form = StudentPhotoForm(request.POST, request.FILES, instance=request.user.student_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Photo updated successfully!')
            return redirect('student_dashboard')
    return redirect('student_dashboard')

@login_required
@teacher_required
def update_teacher_photo(request):
    if request.method == 'POST':
        form = TeacherPhotoForm(request.POST, request.FILES, instance=request.user.teacher_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Photo updated successfully!')
    return redirect('teacher_dashboard')

def student_search(request):
    query = request.GET.get('q', '')
    students = Student.objects.filter(
        Q(name__icontains=query) |
        Q(roll_number__icontains=query)
    )
    return JsonResponse({'students': list(students.values())})

@login_required
def generate_attendance_report(request):
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # Add headers
    headers = ['Date', 'Student Name', 'Roll Number', 'Check In', 'Check Out', 'Duration', 'Status']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)

    # Get data
    logs = EntryLog.objects.select_related('student').order_by('timestamp')
    row = 1
    for log in logs:
        worksheet.write(row, 0, log.timestamp.date().strftime('%Y-%m-%d'))
        worksheet.write(row, 1, log.student.name)
        worksheet.write(row, 2, log.student.roll_number)
        worksheet.write(row, 3, log.timestamp.time().strftime('%H:%M'))
        row += 1

    workbook.close()
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=attendance_report.xlsx'
    return response

@login_required
def profile_view(request):
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
                'profile': student,
                'entry_logs': entry_logs,
                'show_photo_form': not student.photo
            }
        except Student.DoesNotExist:
            messages.error(request, "Student profile not found.")
            context = {'user_type': 'admin', 'profile': None}
            
    elif user.groups.filter(name='Teachers').exists():
        try:
            teacher = user.teacher_profile
            context = {
                'user_type': 'teacher',
                'profile': teacher,
                'show_photo_form': not teacher.photo
            }
        except Teacher.DoesNotExist:
            messages.error(request, "Teacher profile not found.")
            context = {'user_type': 'admin', 'profile': None}
    else:
        # Default for admin or other users
        context = {
            'user_type': 'admin',
            'profile': None,
            'show_photo_form': False
        }
        
    return render(request, 'student/profile.html', context)

def attendance_analytics(request):
    today = timezone.now().date()
    start_date = today - timedelta(days=30)
    
    # Get attendance data
    daily_attendance = EntryLog.objects.filter(
        timestamp__date__gte=start_date,
        action='in'
    ).values('timestamp__date').annotate(
        count=Count('id'),
        on_time=Count('id', filter=Q(timestamp__time__hour__lt=9)),
        late=Count('id', filter=Q(timestamp__time__hour__gte=9))
    ).order_by('timestamp__date')
    
    # Create template context
    context = {
        'daily_attendance': daily_attendance,
        'date_range': f"{start_date.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}"
    }
    
    return render(request, 'student/attendance_analytics.html', context)

# Password Reset Views
class StudentPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('login')

class StudentPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset.html'
    success_url = reverse_lazy('login')

# NFC API Endpoint for Raspberry Pi
@csrf_exempt
def nfc_scan_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            card_id = data.get('card_id')
            
            if not card_id:
                return JsonResponse({'success': False, 'error': 'No card_id provided'})
            
            # Convert UID format to match your database
            # Your Pi sends: ['0x4', '0xa7', '0x8a', '0x2a']
            # Database expects: string format
            
            try:
                student = Student.objects.get(nfc_uid=card_id)
            except Student.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Card not recognized'})

            now = timezone.now()
            time_gap = timedelta(minutes=0.5)

            last_log = EntryLog.objects.filter(student=student).order_by('-timestamp').first()

            # Prevent duplicate scans
            if last_log and (now - last_log.timestamp < time_gap):
                return JsonResponse({
                    'success': False, 
                    'error': 'Please wait before scanning again'
                })

            # Decide next action
            if last_log and last_log.action == 'in':
                action = 'out'
                student.is_in_university = False
                status_message = f"{student.name} checked out"
            else:
                action = 'in'
                student.is_in_university = True
                status_message = f"{student.name} checked in"

            # Save new entry
            EntryLog.objects.create(student=student, action=action)
            student.save()

            return JsonResponse({
                'success': True,
                'student_name': student.name,
                'roll_number': student.roll_number,
                'action': action,
                'status': 'in' if student.is_in_university else 'out',
                'message': status_message,
                'timestamp': now.isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Only POST method allowed'})

# Card Assignment System
@login_required
def assign_card_page(request, student_id):
    """Show card assignment confirmation page"""
    # Check permissions
    if not (request.user.is_superuser or request.user.groups.filter(name='Teachers').exists()):
        messages.error(request, "Access denied. Teacher or admin privileges required.")
        return redirect('dashboard_redirect')
    
    try:
        student = Student.objects.get(id=student_id)
        
        # Check if student already has a card
        if student.nfc_uid:
            messages.warning(request, f"{student.name} already has an assigned NFC card.")
            return redirect('dashboard_redirect')
            
        context = {
            'student': student,
            'timeout_seconds': 30
        }
        return render(request, 'student/assign_card.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, "Student not found")
        return redirect('dashboard_redirect')

@login_required
def assign_card_request(request, student_id):
    """Process card assignment request to Raspberry Pi"""
    # Check permissions
    if not (request.user.is_superuser or request.user.groups.filter(name='Teachers').exists()):
        messages.error(request, "Access denied. Teacher or admin privileges required.")
        return redirect('dashboard_redirect')
    
    try:
        student = Student.objects.get(id=student_id)
        
        # Check if student already has a card
        if student.nfc_uid:
            messages.warning(request, f"{student.name} already has an assigned NFC card.")
            return redirect('dashboard_redirect')
        
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
    
    return redirect('dashboard_redirect')

@login_required  
def remove_card(request, student_id):
    """Remove NFC card assignment from student"""
    # Check permissions
    if not (request.user.is_superuser or request.user.groups.filter(name='Teachers').exists()):
        messages.error(request, "Access denied. Teacher or admin privileges required.")
        return redirect('dashboard_redirect')
    
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
    
    return redirect('dashboard_redirect')

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


# ========================
# EVENT MANAGEMENT VIEWS
# ========================

@login_required
def event_list(request):
    """List all events with filtering and search functionality"""
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
    paginator = Paginator(events, 10)  # 10 events per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_events': events.count()
    }
    return render(request, 'student/events/event_list.html', context)


@login_required
def event_detail(request, event_id):
    """View event details and handle registration"""
    event = get_object_or_404(Event, id=event_id, is_active=True)
    user_registration = None
    user_attendance = None
    registered_students = None
    attendance_stats = None
    
    # Check if user is a student
    if hasattr(request.user, 'student_profile'):
        try:
            user_registration = EventRegistration.objects.get(
                event=event, 
                student=request.user.student_profile
            )
            # Check if they attended
            try:
                user_attendance = EventAttendance.objects.get(
                    event=event,
                    student=request.user.student_profile
                )
            except EventAttendance.DoesNotExist:
                pass
        except EventRegistration.DoesNotExist:
            pass
    
    # If user is a teacher and event organizer, show registered students
    is_teacher = hasattr(request.user, 'teacher_profile')
    is_event_organizer = is_teacher and event.organizer == request.user.teacher_profile
    
    if is_event_organizer:
        # Get all registered students with their attendance status
        registered_students = EventRegistration.objects.filter(
            event=event,
            status__in=['confirmed', 'pending']
        ).select_related('student__user', 'attendance').order_by('registration_date')
        
        # Calculate attendance statistics
        total_registered = registered_students.count()
        total_attended = EventAttendance.objects.filter(event=event).count()
        attendance_stats = {
            'total_registered': total_registered,
            'total_attended': total_attended,
            'pending_checkin': total_registered - total_attended,
            'attendance_rate': round((total_attended / total_registered * 100) if total_registered > 0 else 0, 1)
        }
    
    # Calculate registration percentage
    registration_percentage = 0
    if event.max_capacity > 0:
        registration_percentage = round((event.registered_count / event.max_capacity) * 100, 1)
    
    context = {
        'event': event,
        'user_registration': user_registration,
        'user_attendance': user_attendance,
        'can_register': event.is_registration_open and not user_registration,
        'is_student': hasattr(request.user, 'student_profile'),
        'is_teacher': is_teacher,
        'is_event_organizer': is_event_organizer,
        'registered_students': registered_students,
        'attendance_stats': attendance_stats,
        'registration_percentage': registration_percentage
    }
    return render(request, 'student/events/event_detail.html', context)


@login_required
@teacher_required
def create_event(request):
    """Create a new event (Teachers and Admin only)"""
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            # Set the organizer to current teacher
            if hasattr(request.user, 'teacher_profile'):
                event.organizer = request.user.teacher_profile
            event.save()
            messages.success(request, f'Event "{event.title}" created successfully!')
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm()
    
    return render(request, 'student/events/create_event.html', {'form': form})


@login_required
@teacher_required
def edit_event(request, event_id):
    """Edit an existing event (Teachers and Admin only)"""
    event = get_object_or_404(Event, id=event_id)
    
    # Check if user can edit this event
    if not request.user.is_superuser and event.organizer != request.user.teacher_profile:
        messages.error(request, 'You can only edit events you created.')
        return redirect('event_detail', event_id=event.id)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, f'Event "{event.title}" updated successfully!')
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm(instance=event)
    
    context = {
        'form': form,
        'event': event,
        'editing': True
    }
    return render(request, 'student/events/create_event.html', context)


@login_required
@student_required
def register_for_event(request, event_id):
    """Register student for an event"""
    event = get_object_or_404(Event, id=event_id, is_active=True)
    student = request.user.student_profile
    
    # Check if registration is open
    if not event.is_registration_open:
        messages.error(request, 'Registration is closed for this event.')
        return redirect('event_detail', event_id=event.id)
    
    # Check if already registered
    if EventRegistration.objects.filter(event=event, student=student).exists():
        messages.warning(request, 'You are already registered for this event.')
        return redirect('event_detail', event_id=event.id)
    
    # Check capacity
    if event.registered_count >= event.max_capacity:
        messages.error(request, 'This event has reached maximum capacity.')
        return redirect('event_detail', event_id=event.id)
    
    if request.method == 'POST':
        form = EventRegistrationForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.event = event
            registration.student = student
            registration.status = 'confirmed'  # Auto-confirm for now
            registration.save()
            
            messages.success(request, f'Successfully registered for "{event.title}"!')
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventRegistrationForm()
    
    # Calculate registration percentage
    registration_percentage = 0
    if event.max_capacity > 0:
        registration_percentage = round((event.registered_count / event.max_capacity) * 100, 1)
    
    context = {
        'form': form,
        'event': event,
        'registration_percentage': registration_percentage
    }
    return render(request, 'student/events/register_event.html', context)


@login_required
def cancel_event_registration(request, event_id):
    """Cancel event registration"""
    event = get_object_or_404(Event, id=event_id)
    student = request.user.student_profile
    
    try:
        registration = EventRegistration.objects.get(event=event, student=student)
        registration.delete()
        messages.success(request, f'Registration for "{event.title}" cancelled successfully.')
    except EventRegistration.DoesNotExist:
        messages.error(request, 'No registration found for this event.')
    
    return redirect('event_detail', event_id=event.id)


@csrf_exempt
@login_required
def event_nfc_checkin_api(request):
    """API endpoint for NFC-based event check-in"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    try:
        data = json.loads(request.body)
        card_id = data.get('card_id')
        event_id = data.get('event_id')
        
        if not card_id or not event_id:
            return JsonResponse({'success': False, 'error': 'Missing card_id or event_id'})
        
        # Find student by NFC UID
        try:
            student = Student.objects.get(nfc_uid=card_id)
        except Student.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': 'Student not found. Please register this NFC card first.'
            })
        
        # Find event
        try:
            event = Event.objects.get(id=event_id, is_active=True)
        except Event.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Event not found or inactive'})
        
        # Check if student is registered for this event
        try:
            registration = EventRegistration.objects.get(
                event=event, 
                student=student,
                status='confirmed'
            )
        except EventRegistration.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': f'Student {student.name} is not registered for this event'
            })
        
        # Check if already checked in
        if EventAttendance.objects.filter(event=event, student=student).exists():
            return JsonResponse({
                'success': False,
                'error': f'Student {student.name} already checked in for this event'
            })
        
        # Create attendance record
        attendance = EventAttendance.objects.create(
            event=event,
            student=student,
            registration=registration,
            checkin_method='nfc'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Check-in successful for {student.name}',
            'student_name': student.name,
            'student_roll': student.roll_number,
            'event_title': event.title,
            'checkin_time': attendance.checkin_time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})

# ========================
# LIBRARY MANAGEMENT VIEWS
# ========================

@login_required
def library_dashboard(request):
    """Library management dashboard"""
    # Get library statistics
    total_books = Book.objects.count()
    available_books = Book.objects.filter(status='available').count()
    borrowed_books = Book.objects.filter(status='borrowed').count()
    overdue_books = BookBorrow.objects.filter(status='overdue').count()
    
    # Recent borrowings
    recent_borrowings = BookBorrow.objects.select_related(
        'book', 'student__user'
    ).order_by('-borrow_date')[:10]
    
    # Books due soon (next 3 days)
    from datetime import date, timedelta
    due_soon = BookBorrow.objects.filter(
        status='active',
        due_date__lte=date.today() + timedelta(days=3)
    ).select_related('book', 'student__user').order_by('due_date')
    
    # Popular books (most borrowed)
    from django.db.models import Count
    popular_books = Book.objects.annotate(
        borrow_count=Count('borrows')
    ).order_by('-borrow_count')[:5]
    
    context = {
        'total_books': total_books,
        'available_books': available_books,
        'borrowed_books': borrowed_books,
        'overdue_books': overdue_books,
        'recent_borrowings': recent_borrowings,
        'due_soon': due_soon,
        'popular_books': popular_books,
    }
    return render(request, 'student/library/dashboard.html', context)

@login_required
def book_list(request):
    """List all books with search and filter functionality"""
    books = Book.objects.select_related('category').order_by('title')
    categories = BookCategory.objects.all()
    
    # Handle both form and raw GET parameters
    search_query = request.GET.get('search', '').strip()
    selected_category = request.GET.get('category', '')
    selected_status = request.GET.get('status', '')
    
    # Apply filters
    if search_query:
        books = books.filter(
            models.Q(title__icontains=search_query) |
            models.Q(author__icontains=search_query) |
            models.Q(isbn__icontains=search_query)
        )
    
    if selected_category:
        try:
            category_id = int(selected_category)
            books = books.filter(category_id=category_id)
        except ValueError:
            pass
    
    if selected_status and selected_status != '':
        books = books.filter(status=selected_status)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(books, 20)  # Show 20 books per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    total_books = Book.objects.count()
    
    context = {
        'page_obj': page_obj,
        'books': page_obj.object_list,
        'categories': categories,
        'search_query': search_query,
        'selected_category': selected_category,
        'selected_status': selected_status,
        'total_books': total_books,
    }
    return render(request, 'student/library/book_list.html', context)

@login_required
def book_detail(request, pk):
    """View book details and handle reservations"""
    book = get_object_or_404(Book, id=pk)
    user_reservation = None
    user_borrow = None
    
    # Check if user is a student
    if hasattr(request.user, 'student_profile'):
        # Check existing reservation
        try:
            user_reservation = BookReservation.objects.get(
                book=book,
                student=request.user.student_profile,
                status='pending'
            )
        except BookReservation.DoesNotExist:
            pass
        
        # Check if currently borrowed by user
        try:
            user_borrow = BookBorrow.objects.get(
                book=book,
                student=request.user.student_profile,
                status__in=['active', 'overdue']
            )
        except BookBorrow.DoesNotExist:
            pass
    
    # Get borrowing history
    borrow_history = BookBorrow.objects.filter(
        book=book
    ).select_related('student__user').order_by('-borrow_date')[:5]
    
    context = {
        'book': book,
        'user_reservation': user_reservation,
        'user_borrow': user_borrow,
        'can_reserve': book.status == 'borrowed' and not user_reservation and not user_borrow,
        'can_borrow': book.status == 'available' and not user_borrow,
        'borrow_history': borrow_history,
    }
    return render(request, 'student/library/book_detail.html', context)

@login_required
@teacher_required
@login_required
@teacher_required
def add_book(request):
    """Add new book to library (Teachers and Admin only)"""
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" added successfully!')
            return redirect('book_detail', pk=book.id)
    else:
        form = BookForm()
    
    return render(request, 'student/library/book_form.html', {'form': form})

@login_required
@teacher_required
def edit_book(request, pk):
    """Edit existing book (Teachers and Admin only)"""
    book = get_object_or_404(Book, id=pk)
    
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" updated successfully!')
            return redirect('book_detail', pk=book.id)
    else:
        form = BookForm(instance=book)
    
    context = {'form': form, 'book': book}
    return render(request, 'student/library/book_form.html', context)

@login_required
@teacher_required
def delete_book(request, pk):
    """Delete book (Teachers and Admin only)"""
    book = get_object_or_404(Book, id=pk)
    
    # Check if book has active borrowings
    if BookBorrow.objects.filter(book=book, status__in=['active', 'overdue']).exists():
        messages.error(request, f'Cannot delete "{book.title}" - book is currently borrowed.')
        return redirect('book_detail', pk=book.id)
    
    if request.method == 'POST':
        title = book.title
        book.delete()
        messages.success(request, f'Book "{title}" deleted successfully!')
        return redirect('book_list')
    
    return render(request, 'student/library/delete_book.html', {'book': book})

@login_required
@student_required
def borrow_book(request, pk):
    """Borrow a book (Students only)"""
    book = get_object_or_404(Book, id=pk)
    student = request.user.student_profile
    
    # Check if book is available
    if book.status != 'available':
        messages.error(request, f'"{book.title}" is not available for borrowing.')
        return redirect('book_detail', pk=book.id)
    
    # Check if student already has this book
    if BookBorrow.objects.filter(book=book, student=student, status__in=['active', 'overdue']).exists():
        messages.error(request, f'You already have this book borrowed.')
        return redirect('book_detail', pk=book.id)
    
    # Check borrowing limit
    active_borrows = BookBorrow.objects.filter(student=student, status__in=['active', 'overdue']).count()
    if active_borrows >= student.borrowing_limit:
        messages.error(request, f'You have reached the maximum borrowing limit of {student.borrowing_limit} books.')
        return redirect('book_detail', pk=book.id)
    
    if request.method == 'POST':
        form = BookBorrowForm(request.POST)
        if form.is_valid():
            borrow = form.save(commit=False)
            borrow.book = book
            borrow.student = student
            borrow.save()
            
            # Update book status
            book.status = 'borrowed'
            book.save()
            
            messages.success(request, f'Successfully borrowed "{book.title}"! Due date: {borrow.due_date}')
            return redirect('student_library_dashboard')
    else:
        form = BookBorrowForm()
    
    # Get current borrowings count for template
    current_borrowings_count = BookBorrow.objects.filter(student=student, status__in=['active', 'overdue']).count()
    
    context = {
        'form': form, 
        'book': book,
        'current_borrowings_count': current_borrowings_count,
        'max_borrowings': student.borrowing_limit
    }
    return render(request, 'student/library/borrow_book.html', context)

@login_required
def return_book(request, borrow_id):
    """Return a borrowed book"""
    borrow = get_object_or_404(BookBorrow, id=borrow_id)
    
    # Check permissions
    if not (request.user.is_superuser or 
            hasattr(request.user, 'teacher_profile') or
            (hasattr(request.user, 'student_profile') and borrow.student == request.user.student_profile)):
        messages.error(request, "You don't have permission to return this book.")
        return redirect('book_detail', pk=borrow.book.id)
    
    if borrow.status not in ['active', 'overdue']:
        messages.error(request, 'This book has already been returned.')
        return redirect('book_detail', pk=borrow.book.id)
    
    if request.method == 'POST':
        form = BookReturnForm(request.POST, instance=borrow)
        if form.is_valid():
            borrow = form.save(commit=False)
            borrow.return_date = timezone.now()
            borrow.status = 'returned'
            
            # Calculate final fine if overdue
            if borrow.is_overdue:
                borrow.fine_amount = borrow.calculate_fine()
                # Create a Fine record if there's a fine amount
                if borrow.fine_amount > 0:
                    Fine.objects.create(
                        student=borrow.student,
                        amount=borrow.fine_amount,
                        description=f'Overdue fine for "{borrow.book.title}" - {borrow.days_overdue} days late'
                    )
            
            borrow.save()
            
            # Update book status
            book = borrow.book
            book.status = 'available'
            book.save()
            
            # Check for pending reservations and notify
            pending_reservation = BookReservation.objects.filter(
                book=book, status='pending'
            ).order_by('reservation_date').first()
            
            if pending_reservation:
                # TODO: Send notification to student with reservation
                messages.info(request, f'Book returned successfully. Student {pending_reservation.student.roll_number} has a pending reservation.')
            else:
                messages.success(request, f'Book "{book.title}" returned successfully!')
            
            return redirect('book_detail', pk=book.id)
    else:
        form = BookReturnForm()
    
    context = {'form': form, 'borrow': borrow}
    return render(request, 'student/library/return_book.html', context)

@login_required
@student_required
@login_required
@student_required
def reserve_book(request, pk):
    """Reserve a book (Students only)"""
    book = get_object_or_404(Book, id=pk)
    student = request.user.student_profile
    
    # Check if book can be reserved
    if book.status == 'available':
        messages.error(request, f'"{book.title}" is available for immediate borrowing. No need to reserve.')
        return redirect('book_detail', pk=book.id)
    
    # Check if student already has a reservation
    if BookReservation.objects.filter(book=book, student=student, status='pending').exists():
        messages.error(request, f'You already have a pending reservation for "{book.title}".')
        return redirect('book_detail', pk=book.id)
    
    # Check if student already has the book
    if BookBorrow.objects.filter(book=book, student=student, status__in=['active', 'overdue']).exists():
        messages.error(request, f'You already have this book borrowed.')
        return redirect('book_detail', pk=book.id)
    
    if request.method == 'POST':
        form = BookReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.book = book
            reservation.student = student
            
            # Set expiry date (7 days from now)
            from datetime import timedelta
            reservation.expiry_date = timezone.now() + timedelta(days=7)
            reservation.save()
            
            messages.success(request, f'Reservation placed for "{book.title}". You will be notified when it becomes available.')
            return redirect('student_library_dashboard')
    else:
        form = BookReservationForm()
    
    context = {'form': form, 'book': book}
    return render(request, 'student/library/reserve_book.html', context)

@login_required
@student_required
def cancel_reservation(request, reservation_id):
    """Cancel a book reservation"""
    reservation = get_object_or_404(BookReservation, id=reservation_id)
    
    # Check permissions
    if reservation.student != request.user.student_profile:
        messages.error(request, "You don't have permission to cancel this reservation.")
        return redirect('book_detail', pk=reservation.book.id)
    
    if reservation.status != 'pending':
        messages.error(request, 'This reservation cannot be cancelled.')
        return redirect('book_detail', pk=reservation.book.id)
    
    book_title = reservation.book.title
    reservation.status = 'cancelled'
    reservation.save()
    
    messages.success(request, f'Reservation for "{book_title}" cancelled successfully.')
    return redirect('student_library_dashboard')

@login_required
@student_required
@login_required
@student_required
def student_library_dashboard(request):
    """Student's personal library dashboard"""
    student = request.user.student_profile
    
    # Current borrowings
    current_borrows = BookBorrow.objects.filter(
        student=student,
        status__in=['active', 'overdue']
    ).select_related('book').order_by('due_date')
    
    # Current reservations
    current_reservations = BookReservation.objects.filter(
        student=student,
        status='pending'
    ).select_related('book').order_by('reservation_date')
    
    # Borrowing history (all borrows including active ones)
    borrow_history = BookBorrow.objects.filter(
        student=student
    ).select_related('book').order_by('-borrow_date')[:10]
    
    # Overdue books
    overdue_books = current_borrows.filter(status='overdue')
    
    # Calculate total fines
    total_fines = Fine.objects.filter(
        student=student,
        is_paid=False,
        description__icontains='Overdue fine'
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    context = {
        'student': student,
        'current_borrowings': current_borrows,  # Fixed: template expects current_borrowings
        'current_reservations': current_reservations,
        'borrowing_history': borrow_history,  # Fixed variable name to match template
        'overdue_books': overdue_books,
        'total_fines': total_fines,
    }
    return render(request, 'student/library/student_dashboard.html', context)

@csrf_exempt
@login_required
def book_nfc_checkout_api(request):
    """API endpoint for NFC-based book checkout"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    try:
        data = json.loads(request.body)
        student_card_id = data.get('student_card_id')
        book_nfc_uid = data.get('book_nfc_uid')
        action = data.get('action', 'checkout')  # 'checkout' or 'return'
        
        if not student_card_id or not book_nfc_uid:
            return JsonResponse({'success': False, 'error': 'Missing student_card_id or book_nfc_uid'})
        
        # Find student by NFC UID
        try:
            student = Student.objects.get(nfc_uid=student_card_id)
        except Student.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Student not found. Please register this NFC card first.'
            })
        
        # Find book by NFC tag UID
        try:
            book = Book.objects.get(nfc_tag_uid=book_nfc_uid)
        except Book.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Book not found. Please check the NFC tag.'
            })
        
        if action == 'checkout':
            # Check if book is available
            if book.status != 'available':
                return JsonResponse({
                    'success': False,
                    'error': f'"{book.title}" is not available for borrowing.'
                })
            
            # Check borrowing limit
            active_borrows = BookBorrow.objects.filter(student=student, status__in=['active', 'overdue']).count()
            if active_borrows >= 5:
                return JsonResponse({
                    'success': False,
                    'error': 'Borrowing limit exceeded (maximum 5 books).'
                })
            
            # Create borrowing record
            from datetime import date, timedelta
            borrow = BookBorrow.objects.create(
                book=book,
                student=student,
                due_date=date.today() + timedelta(days=14),
                nfc_checkout=True,
                checkout_notes='Checked out via NFC'
            )
            
            # Update book status
            book.status = 'borrowed'
            book.save()
            
            return JsonResponse({
                'success': True,
                'action': 'checkout',
                'message': f'Successfully checked out "{book.title}"',
                'book_title': book.title,
                'student_name': student.name,
                'due_date': borrow.due_date.strftime('%Y-%m-%d'),
                'borrow_id': borrow.id
            })
        
        elif action == 'return':
            # Find active borrowing
            try:
                borrow = BookBorrow.objects.get(
                    book=book,
                    student=student,
                    status__in=['active', 'overdue']
                )
            except BookBorrow.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'No active borrowing found for "{book.title}".'
                })
            
            # Process return
            borrow.return_date = timezone.now()
            borrow.status = 'returned'
            borrow.nfc_checkin = True
            
            # Calculate fine if overdue
            fine_amount = 0
            if borrow.is_overdue:
                fine_amount = borrow.calculate_fine()
                borrow.fine_amount = fine_amount
                
                # Create Fine record
                if fine_amount > 0:
                    Fine.objects.create(
                        student=student,
                        amount=fine_amount,
                        description=f'Overdue fine for "{book.title}" - {borrow.days_overdue} days late'
                    )
            
            borrow.save()
            
            # Update book status
            book.status = 'available'
            book.save()
            
            return JsonResponse({
                'success': True,
                'action': 'return',
                'message': f'Successfully returned "{book.title}"',
                'book_title': book.title,
                'student_name': student.name,
                'fine_amount': float(fine_amount),
                'was_overdue': borrow.is_overdue,
                'days_overdue': borrow.days_overdue if borrow.is_overdue else 0
            })
        
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action. Use "checkout" or "return".'})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})

@login_required
def overdue_books_report(request):
    """Generate report of overdue books"""
    # Check permissions (teachers and admin only)
    if not (request.user.is_superuser or hasattr(request.user, 'teacher_profile')):
        messages.error(request, "Access denied. Teacher or admin privileges required.")
        return redirect('library_dashboard')
    
    overdue_borrows = BookBorrow.objects.filter(
        status='overdue'
    ).select_related('book', 'student__user').order_by('due_date')
    
    # Calculate total fine amounts
    total_fine_amount = sum(borrow.calculate_fine() for borrow in overdue_borrows)
    
    context = {
        'overdue_borrows': overdue_borrows,
        'total_fine_amount': total_fine_amount,
    }
    return render(request, 'student/library/overdue_report.html', context)