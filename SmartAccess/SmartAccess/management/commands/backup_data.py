from django.core.management.base import BaseCommand
from django.core import serializers
import os
from students.models import Student
from attendance.models import EntryLog
from fines.models import Fine
from teachers.models import Teacher
from datetime import datetime

class Command(BaseCommand):
    help = 'Backup all data to JSON files'

    def handle(self, *args, **kwargs):
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = 'backups'
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        models = [Student, EntryLog, Fine, Teacher]
        
        for model in models:
            filename = f'{backup_dir}/{model.__name__}_{date_str}.json'
            with open(filename, 'w') as f:
                data = serializers.serialize('json', model.objects.all())
                f.write(data)
                
        self.stdout.write(self.style.SUCCESS(f'Backup completed. Files saved to {backup_dir}/'))