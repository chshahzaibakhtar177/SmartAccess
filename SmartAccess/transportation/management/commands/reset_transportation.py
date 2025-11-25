from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Resets transportation data by deleting all existing records using raw SQL'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('='*60))
        self.stdout.write(self.style.WARNING('RESETTING TRANSPORTATION DATA'))
        self.stdout.write(self.style.WARNING('='*60))
        
        # Delete all transportation data using raw SQL
        self.stdout.write('\nDeleting existing transportation data using raw SQL...')
        
        with connection.cursor() as cursor:
            # Get counts before deletion
            cursor.execute("SELECT COUNT(*) FROM transportation_transportlog")
            transport_logs_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM transportation_studentbusassignment")
            assignments_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM transportation_busschedule")
            schedules_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM transportation_bus")
            buses_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM transportation_route")
            routes_count = cursor.fetchone()[0]
            
            # Delete in correct order (respecting foreign keys)
            cursor.execute("DELETE FROM transportation_transportlog")
            self.stdout.write(self.style.SUCCESS(f'✓ Deleted {transport_logs_count} transport logs'))
            
            cursor.execute("DELETE FROM transportation_studentbusassignment")
            self.stdout.write(self.style.SUCCESS(f'✓ Deleted {assignments_count} student assignments'))
            
            cursor.execute("DELETE FROM transportation_busschedule")
            self.stdout.write(self.style.SUCCESS(f'✓ Deleted {schedules_count} bus schedules'))
            
            cursor.execute("DELETE FROM transportation_bus")
            self.stdout.write(self.style.SUCCESS(f'✓ Deleted {buses_count} buses'))
            
            cursor.execute("DELETE FROM transportation_route")
            self.stdout.write(self.style.SUCCESS(f'✓ Deleted {routes_count} routes'))
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Transportation data reset complete!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.WARNING('\nNext steps:'))
        self.stdout.write(self.style.WARNING('1. python manage.py makemigrations transportation'))
        self.stdout.write(self.style.WARNING('2. python manage.py migrate'))
        self.stdout.write(self.style.WARNING('3. python manage.py seed_transportation\n'))
