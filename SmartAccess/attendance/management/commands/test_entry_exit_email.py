"""
Management command to test entry/exit email notifications
Usage: python manage.py test_entry_exit_email
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from students.models import Student
from attendance.views import send_entry_exit_email


class Command(BaseCommand):
    help = 'Test entry/exit email notification system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('TESTING ENTRY/EXIT EMAIL SYSTEM'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # Get a student with NFC card
        try:
            student = Student.objects.filter(nfc_uid__isnull=False).first()
            if not student:
                self.stdout.write(self.style.ERROR('❌ No students with NFC cards found'))
                return
            
            self.stdout.write('\nTest Data:')
            self.stdout.write(f'  Student: {student.name}')
            self.stdout.write(f'  Roll Number: {student.roll_number}')
            self.stdout.write(f'  Email: {student.roll_number}@students.cuisahiwal.edu.pk')
            
            # Test entry email
            self.stdout.write('\n' + '-' * 70)
            self.stdout.write('Testing ENTRY email...')
            try:
                send_entry_exit_email(
                    student=student,
                    action='in',
                    timestamp=timezone.now()
                )
                self.stdout.write(self.style.SUCCESS('✅ Entry email sent successfully'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Entry email failed: {str(e)}'))
            
            # Test exit email
            self.stdout.write('\n' + '-' * 70)
            self.stdout.write('Testing EXIT email...')
            try:
                send_entry_exit_email(
                    student=student,
                    action='out',
                    timestamp=timezone.now()
                )
                self.stdout.write(self.style.SUCCESS('✅ Exit email sent successfully'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Exit email failed: {str(e)}'))
            
            self.stdout.write('\n' + '=' * 70)
            self.stdout.write(self.style.SUCCESS('TEST COMPLETED'))
            self.stdout.write('=' * 70)
            self.stdout.write(f'\nCheck inbox: {student.roll_number}@students.cuisahiwal.edu.pk')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error: {str(e)}'))
