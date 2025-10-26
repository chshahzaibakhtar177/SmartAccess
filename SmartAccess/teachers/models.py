from django.db import models
from django.contrib.auth.models import User

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
