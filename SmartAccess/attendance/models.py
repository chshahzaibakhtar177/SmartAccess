from django.db import models
from django.utils import timezone
from students.models import Student

class EntryLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    action = models.CharField(max_length=3, choices=[('in', 'In'), ('out', 'Out')])
    auto_generated = models.BooleanField(default=False)  # Add this field

    def __str__(self):
        return f"{self.student.roll_number} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.action}"
