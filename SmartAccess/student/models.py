from django.db import models
from django.contrib.auth.models import User

from django.utils import timezone

class Student(models.Model):
    user= models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='student_profile')
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, unique=True)
    nfc_uid = models.CharField(max_length=50, unique=True, null=True, blank=True, db_index=True)  # Now nullable by default
    is_in_university = models.BooleanField(default=False)
    photo = models.ImageField(upload_to='student_photos/', null=True, blank=True)

    def __str__(self):
        return f"{self.roll_number} - {self.name}"

class Fine(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    date_issued = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    def __str__(self):
        return f"Fine for {self.student.roll_number} - {self.amount} - {'Paid' if self.is_paid else 'Unpaid'}"
    
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='teacher_photos/', null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.pk:  # If updating
            try:
                old_instance = Teacher.objects.get(pk=self.pk)
                if old_instance.photo and self.photo != old_instance.photo:
                    old_instance.photo.delete(save=False)
            except Teacher.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class EntryLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    action = models.CharField(max_length=3, choices=[('in', 'In'), ('out', 'Out')])
    auto_generated = models.BooleanField(default=False)  # Add this field

    def __str__(self):
        return f"{self.student.roll_number} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.action}"


