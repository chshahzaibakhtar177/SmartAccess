from django.core.management.base import BaseCommand
from django.utils import timezone
from attendance.models import EntryLog
from datetime import time
from django.core.mail import send_mail

class Command(BaseCommand):
    help = 'Auto checkout students who forgot to scan out'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        evening_cutoff = timezone.make_aware(timezone.datetime.combine(today, time(18, 0)))  # 6:00 PM

        # Get all latest logs for each student
        latest_logs = {}
        for log in EntryLog.objects.filter(timestamp__date=today).order_by('student', '-timestamp'):
            if log.student_id not in latest_logs:
                latest_logs[log.student_id] = log

        count = 0
        for student_id, log in latest_logs.items():
            if log.action == 'in':
                # Create checkout log
                EntryLog.objects.create(
                    student=log.student,
                    timestamp=evening_cutoff,
                    action='out',
                    auto_generated=True  # Add this field to EntryLog model
                )
                
                # Send notification
                send_mail(
                    'Automatic Checkout Notification',
                    'You were automatically checked out at 6:00 PM',
                    'noreply@smartaccess.com',
                    [log.student.user.email],
                    fail_silently=True,
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Auto-checked out {count} students at 6:00 PM.'))