"""
Management command to test email notifications
Usage: python manage.py test_transport_email
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from transportation.models import StudentBusAssignment
from transportation.api_views import send_transport_email


class Command(BaseCommand):
    help = 'Test transportation email notification system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('TESTING TRANSPORTATION EMAIL SYSTEM'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # Get a student with bus assignment
        try:
            assignment = StudentBusAssignment.objects.filter(is_active=True).first()
            if not assignment:
                self.stdout.write(self.style.ERROR('❌ No active bus assignments found'))
                return
            
            student = assignment.student
            bus = assignment.bus
            route = assignment.route
            
            self.stdout.write('\nTest Data:')
            self.stdout.write(f'  Student: {student.name}')
            self.stdout.write(f'  Roll Number: {student.roll_number}')
            self.stdout.write(f'  Email: {student.roll_number}@students.cuisahiwal.edu.pk')
            self.stdout.write(f'  Bus: {bus.bus_number}')
            self.stdout.write(f'  Route: {route.route_name}')
            
            # Test boarding email
            self.stdout.write('\n' + '-' * 70)
            self.stdout.write('Testing BOARDING email...')
            try:
                send_transport_email(
                    student=student,
                    bus=bus,
                    route=route,
                    action='board',
                    timestamp=timezone.now()
                )
                self.stdout.write(self.style.SUCCESS('✅ Boarding email sent successfully'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Boarding email failed: {str(e)}'))
            
            # Test alighting email
            self.stdout.write('\n' + '-' * 70)
            self.stdout.write('Testing ALIGHTING email...')
            try:
                send_transport_email(
                    student=student,
                    bus=bus,
                    route=route,
                    action='alight',
                    timestamp=timezone.now()
                )
                self.stdout.write(self.style.SUCCESS('✅ Alighting email sent successfully'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Alighting email failed: {str(e)}'))
            
            self.stdout.write('\n' + '=' * 70)
            self.stdout.write(self.style.SUCCESS('TEST COMPLETED'))
            self.stdout.write('=' * 70)
            self.stdout.write('\nCheck the console output above for email content')
            self.stdout.write('(Using console backend - emails are printed, not sent)')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error: {str(e)}'))
