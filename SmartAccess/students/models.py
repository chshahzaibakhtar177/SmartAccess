from django.db import models
from django.contrib.auth.models import User

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='student_profile')
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, unique=True)
    nfc_uid = models.CharField(max_length=50, unique=True, null=True, blank=True, db_index=True)  # Now nullable by default
    is_in_university = models.BooleanField(default=False)
    photo = models.ImageField(upload_to='student_photos/', null=True, blank=True)
    borrowing_limit = models.PositiveIntegerField(default=10)  # Default borrowing limit of 10 books

    def __str__(self):
        return f"{self.roll_number} - {self.name}"
