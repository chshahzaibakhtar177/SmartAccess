from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Create required user groups for SmartAccess system'

    def handle(self, *args, **kwargs):
        groups = ['Students', 'Teachers', 'Alumni']
        
        created_groups = []
        existing_groups = []
        
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                created_groups.append(group_name)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created group: {group_name}')
                )
            else:
                existing_groups.append(group_name)
                self.stdout.write(
                    self.style.WARNING(f'○ Group already exists: {group_name}')
                )
        
        self.stdout.write('\n' + '='*50)
        if created_groups:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Created {len(created_groups)} new group(s): {", ".join(created_groups)}'
                )
            )
        if existing_groups:
            self.stdout.write(
                self.style.WARNING(
                    f'\n○ {len(existing_groups)} group(s) already existed: {", ".join(existing_groups)}'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ All required groups are now available!\n'
            )
        )
