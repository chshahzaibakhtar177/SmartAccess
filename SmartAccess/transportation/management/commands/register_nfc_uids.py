"""
Management command to register NFC UIDs for students
Usage: python manage.py register_nfc_uids
"""

from django.core.management.base import BaseCommand
from students.models import Student
import random


class Command(BaseCommand):
    help = 'Register NFC UIDs for students who do not have one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Force regenerate NFC UIDs for all students (including those who already have one)',
        )
        parser.add_argument(
            '--student',
            type=str,
            help='Register NFC UID for specific student by roll number',
        )

    def generate_nfc_uid(self):
        """Generate a unique 9-digit NFC UID"""
        while True:
            uid = ''.join([str(random.randint(0, 9)) for _ in range(9)])
            if not Student.objects.filter(nfc_uid=uid).exists():
                return uid

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('NFC UID REGISTRATION'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # Specific student
        if options['student']:
            roll_number = options['student']
            try:
                student = Student.objects.get(roll_number=roll_number)
                old_uid = student.nfc_uid
                new_uid = self.generate_nfc_uid()
                student.nfc_uid = new_uid
                student.save()
                
                if old_uid:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Updated {student.name} ({roll_number}): {old_uid} → {new_uid}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Registered {student.name} ({roll_number}): {new_uid}'
                        )
                    )
            except Student.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Student not found: {roll_number}')
                )
            return

        # All students (force regenerate)
        if options['all']:
            students = Student.objects.all()
            count = 0
            for student in students:
                new_uid = self.generate_nfc_uid()
                student.nfc_uid = new_uid
                student.save()
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ {count}. {student.name} ({student.roll_number}): {new_uid}'
                    )
                )
            self.stdout.write(self.style.SUCCESS(f'\nTotal regenerated: {count} students'))
            return

        # Only students without NFC UID
        students_without_nfc = Student.objects.filter(nfc_uid__isnull=True) | Student.objects.filter(nfc_uid='')
        
        if not students_without_nfc.exists():
            self.stdout.write(
                self.style.SUCCESS('✅ All students already have NFC UIDs registered!')
            )
            self.stdout.write(
                self.style.WARNING('Use --all flag to force regenerate all UIDs')
            )
            return

        self.stdout.write(f'Found {students_without_nfc.count()} students without NFC UID\n')
        
        count = 0
        for student in students_without_nfc:
            nfc_uid = self.generate_nfc_uid()
            student.nfc_uid = nfc_uid
            student.save()
            count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ {count}. {student.name} ({student.roll_number}): {nfc_uid}'
                )
            )

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS(f'Successfully registered {count} NFC UIDs'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        # Show summary
        total_students = Student.objects.count()
        with_nfc = Student.objects.exclude(nfc_uid__isnull=True).exclude(nfc_uid='').count()
        without_nfc = total_students - with_nfc
        
        self.stdout.write('\nSummary:')
        self.stdout.write(f'  Total Students: {total_students}')
        self.stdout.write(f'  With NFC UID: {with_nfc}')
        self.stdout.write(f'  Without NFC UID: {without_nfc}')
