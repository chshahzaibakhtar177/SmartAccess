from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from students.models import Student

class Command(BaseCommand):
    help = 'Validate student accounts and fix any missing profile linkages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Fix any broken student account linkages',
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 Validating student accounts...")
        
        # Get Students group
        try:
            students_group = Group.objects.get(name='Students')
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Students group does not exist! Creating...')
            )
            students_group = Group.objects.create(name='Students')
            self.stdout.write(
                self.style.SUCCESS('✅ Students group created')
            )

        # Check all users in Students group
        student_users = User.objects.filter(groups=students_group)
        self.stdout.write(f"Found {student_users.count()} users in Students group")
        
        broken_accounts = []
        working_accounts = []
        
        for user in student_users:
            try:
                profile = user.student_profile
                working_accounts.append((user.username, profile.name))
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {user.username}: Has profile ({profile.name})')
                )
            except Student.DoesNotExist:
                broken_accounts.append(user)
                self.stdout.write(
                    self.style.ERROR(f'❌ {user.username}: NO PROFILE!')
                )

        # Check all Student objects without users
        orphaned_students = Student.objects.filter(user__isnull=True)
        if orphaned_students:
            self.stdout.write(f"\nFound {orphaned_students.count()} orphaned Student records:")
            for student in orphaned_students:
                self.stdout.write(f"- {student.roll_number} ({student.name}) - no user linked")

        # Summary
        self.stdout.write(f"\n📊 Summary:")
        self.stdout.write(f"- Working student accounts: {len(working_accounts)}")
        self.stdout.write(f"- Broken student accounts: {len(broken_accounts)}")
        self.stdout.write(f"- Orphaned student profiles: {orphaned_students.count()}")

        if options['fix'] and (broken_accounts or orphaned_students):
            self.stdout.write(f"\n🔧 Attempting to fix issues...")
            
            # Try to match broken accounts with orphaned students
            for user in broken_accounts:
                # Try to find a student with matching username/roll_number
                matching_student = None
                for student in orphaned_students:
                    if student.roll_number == user.username:
                        matching_student = student
                        break
                
                if matching_student:
                    matching_student.user = user
                    matching_student.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Fixed: Linked {user.username} to {matching_student.name}')
                    )
                else:
                    # Create a new student profile for the user
                    student = Student.objects.create(
                        user=user,
                        name=user.username,  # Use username as name temporarily
                        roll_number=user.username
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Created: New profile for {user.username}')
                    )
            
            self.stdout.write(f"\n🎉 Fix operation completed!")
        elif broken_accounts or orphaned_students:
            self.stdout.write(f"\n💡 Run with --fix flag to attempt automatic repairs")
        else:
            self.stdout.write(f"\n🎉 All student accounts are properly configured!")