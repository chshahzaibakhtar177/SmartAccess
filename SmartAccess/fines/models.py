from django.db import models
from students.models import Student

class Fine(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    date_issued = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Fine for {self.student.roll_number} - {self.amount} - {'Paid' if self.is_paid else 'Unpaid'}"
