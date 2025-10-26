from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from datetime import timedelta
from io import BytesIO
import csv
import xlsxwriter
import json

# Import from the modular models
from .models import EntryLog
from students.models import Student

# Import student_detail from students app
from students.views import student_detail

# Attendance management views - migrated from legacy student app

def simulate_card_scan(request):
    """Simulate card scan view - migrated from legacy student app"""
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
            messages.warning(request, "Please wait before scanning again.")
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

    return render(request, 'attendance/simulate_scan.html')


def view_logs(request):
    """View logs view - migrated from legacy student app"""
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
        except Exception:
            pass

    logs = logs.order_by('-timestamp')

    # Pagination
    paginator = Paginator(logs, 10)  # 10 logs per page
    page_number = request.GET.get('page')
    page_logs = paginator.get_page(page_number)

    return render(request, 'attendance/view_logs.html', {
        'logs': page_logs,
        'students': Student.objects.all()
    })


def export_logs_csv(request):
    """Export logs CSV view - migrated from legacy student app"""
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
def generate_attendance_report(request):
    """Generate attendance report - migrated from legacy student app"""
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


def attendance_analytics(request):
    """Attendance analytics view - migrated from legacy student app"""
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
    
    return render(request, 'attendance/attendance_analytics.html', context)


@csrf_exempt
def nfc_scan_api(request):
    """NFC scan API view - migrated from legacy student app"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            card_id = data.get('card_id')
            
            if not card_id:
                return JsonResponse({'success': False, 'error': 'No card_id provided'})
            
            try:
                student = Student.objects.get(nfc_uid=card_id)
            except Student.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Card not recognized'})

            now = timezone.now()
            time_gap = timedelta(minutes=0.5)

            last_log = EntryLog.objects.filter(student=student).order_by('-timestamp').first()

            # Prevent duplicate scans
            if last_log and (now - last_log.timestamp < time_gap):
                return JsonResponse({'success': False, 'error': 'Please wait before scanning again'})

            # Decide next action
            if last_log and last_log.action == 'in':
                action = 'out'
                student.is_in_university = False
                message = f"{student.name} checked out"
            else:
                action = 'in'
                student.is_in_university = True
                message = f"{student.name} checked in"

            # Save new entry
            EntryLog.objects.create(student=student, action=action)
            student.save()

            return JsonResponse({'success': True, 'message': message})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
