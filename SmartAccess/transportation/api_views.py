"""
API views for transportation NFC scanning
Handles bus boarding/alighting scans from Raspberry Pi devices
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import json
import logging

from students.models import Student
from .models import TransportLog, StudentBusAssignment

logger = logging.getLogger(__name__)


def send_transport_email(student, bus, route, action, timestamp):
    """Send email notification to student about bus boarding/alighting"""
    # Generate student email
    student_email = f"{student.roll_number}@{settings.STUDENT_EMAIL_DOMAIN}"
    
    # Email subject
    subject = f"Bus {action.capitalize()} Notification - {bus.bus_number}"
    
    # Email body
    action_text = "boarded" if action == "board" else "alighted from"
    time_str = timestamp.strftime("%I:%M %p, %B %d, %Y")
    
    message = f"""
Dear {student.name},

This is to confirm that you have {action_text} the bus.

Details:
- Student: {student.name}
- Roll Number: {student.roll_number}
- Bus Number: {bus.bus_number}
- Route: {route.route_name}
- Action: {action.capitalize()}
- Time: {time_str}

If you did not perform this action, please contact the transportation office immediately.

Best regards,
SmartAccess Transportation System
COMSATS University Islamabad, Sahiwal Campus
"""
    
    # Send email
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[student_email],
        fail_silently=False
    )
    
    logger.info(f"Email sent to {student_email} for {action} action")


@csrf_exempt
@require_http_methods(["POST"])
def process_bus_scan(request):
    """
    Process NFC scan from bus scanner
    Backend automatically determines student's assigned bus and records the scan.
    Expected data:
    {
        "nfc_uid": "123456789",
        "action": "board" or "alight",
        "timestamp": "2025-11-23T10:30:00"
    }
    """
    try:
        # Parse JSON data
        data = json.loads(request.body)
        nfc_uid = data.get('nfc_uid')
        action = data.get('action', 'board')
        scan_time = data.get('timestamp')
        
        if not nfc_uid:
            return JsonResponse(
                {'status': 'error', 'error': 'Missing required field: nfc_uid'},
                status=400
            )
        
        # Find student by NFC UID
        try:
            student = Student.objects.get(nfc_uid=nfc_uid)
        except Student.DoesNotExist:
            logger.warning(f"Unknown NFC card scanned: {nfc_uid}")
            return JsonResponse(
                {
                    'status': 'error',
                    'error': 'Student not found',
                    'message': 'This card is not registered in the system'
                },
                status=404
            )
        
        # Get student's assigned bus
        try:
            assignment = StudentBusAssignment.objects.get(
                student=student,
                is_active=True
            )
            bus = assignment.bus
            route = assignment.route
            location = f'Bus {bus.bus_number}'
        except StudentBusAssignment.DoesNotExist:
            logger.warning(f"Student {student.roll_number} has no active bus assignment")
            return JsonResponse(
                {
                    'status': 'error',
                    'error': 'No bus assignment',
                    'message': f'{student.name} has no active bus assignment'
                },
                status=404
            )
        
        # Create transport log
        transport_log = TransportLog.objects.create(
            user=student.user,
            user_type='student',
            nfc_uid=nfc_uid,
            bus=bus,
            route=route,
            boarding_status=action,
            boarding_location=location,
            boarding_time=timezone.now() if not scan_time else scan_time
        )
        
        logger.info(
            f"Transport log created: {student.roll_number} "
            f"{action} {bus.bus_number}"
        )
        
        # Send email notification
        try:
            send_transport_email(student, bus, route, action, transport_log.boarding_time)
        except Exception as email_error:
            logger.error(f"Failed to send email: {email_error}")
            # Don't fail the request if email fails
        
        # Prepare response
        response_data = {
            'status': 'success',
            'message': f'{action.capitalize()} recorded successfully',
            'student_name': student.name,
            'roll_number': student.roll_number,
            'bus_number': bus.bus_number,
            'route_name': route.route_name,
            'action': action,
            'timestamp': transport_log.boarding_time.isoformat()
        }
        
        return JsonResponse(response_data, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse(
            {'status': 'error', 'error': 'Invalid JSON'},
            status=400
        )
    except Exception as e:
        logger.error(f"Error processing bus scan: {str(e)}")
        return JsonResponse(
            {
                'status': 'error',
                'error': 'Internal server error',
                'message': str(e)
            },
            status=500
        )
