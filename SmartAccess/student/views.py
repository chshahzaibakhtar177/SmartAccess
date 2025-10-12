from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
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

from .forms import StudentForm, FineForm, TeacherCreationForm, StudentPhotoForm, TeacherPhotoForm
from .models import Student, Fine, EntryLog, Teacher
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