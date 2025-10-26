from django.db import models
from django.utils import timezone
from students.models import Student
from teachers.models import Teacher

# Event Management Models
class EventCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff', help_text='Hex color code for category display')
    
    class Meta:
        verbose_name_plural = "Event Categories"
    
    def __str__(self):
        return self.name

class Event(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(EventCategory, on_delete=models.CASCADE, related_name='events')
    organizer = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='organized_events')
    
    # Event timing
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    registration_deadline = models.DateTimeField()
    
    # Event details
    venue = models.CharField(max_length=200)
    max_capacity = models.PositiveIntegerField(help_text='Maximum number of participants')
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Event status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='upcoming')
    is_active = models.BooleanField(default=True)
    requires_nfc_checkin = models.BooleanField(default=True, help_text='Require NFC check-in for attendance')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Event image
    image = models.ImageField(upload_to='event_images/', null=True, blank=True)
    
    class Meta:
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['start_datetime']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.start_datetime.strftime('%Y-%m-%d')}"
    
    @property
    def is_registration_open(self):
        """Check if registration is still open"""
        return timezone.now() < self.registration_deadline and self.is_active
    
    @property
    def registered_count(self):
        """Get number of registered participants"""
        return self.registrations.filter(status='confirmed').count()
    
    @property
    def checked_in_count(self):
        """Get number of participants who checked in"""
        return self.attendances.count()
    
    @property
    def attendance_percentage(self):
        """Calculate attendance percentage"""
        if self.registered_count == 0:
            return 0
        return round((self.checked_in_count / self.registered_count) * 100, 2)

class EventRegistration(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('waitlist', 'Waitlist'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='event_registrations')
    
    # Registration details
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Payment details
    payment_status = models.CharField(
        max_length=10, 
        choices=[('pending', 'Pending'), ('paid', 'Paid'), ('refunded', 'Refunded')],
        default='pending'
    )
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Additional info
    notes = models.TextField(blank=True, help_text='Any special requirements or notes')
    
    class Meta:
        unique_together = ['event', 'student']
        ordering = ['-registration_date']
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['student', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.event.title} ({self.status})"

class EventAttendance(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='event_attendances')
    registration = models.OneToOneField(EventRegistration, on_delete=models.CASCADE, related_name='attendance')
    
    # Check-in details
    checkin_time = models.DateTimeField(auto_now_add=True)
    checkout_time = models.DateTimeField(null=True, blank=True)
    
    # NFC scan details
    checkin_method = models.CharField(
        max_length=10,
        choices=[('nfc', 'NFC Scan'), ('manual', 'Manual Entry')],
        default='nfc'
    )
    
    # Additional tracking
    duration_minutes = models.PositiveIntegerField(null=True, blank=True, help_text='Event attendance duration')
    feedback_rating = models.PositiveSmallIntegerField(
        null=True, blank=True,
        choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)],
        help_text='Student feedback rating (1-5 stars)'
    )
    feedback_comments = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['event', 'student']
        ordering = ['-checkin_time']
        indexes = [
            models.Index(fields=['event', 'checkin_time']),
            models.Index(fields=['student', 'checkin_time']),
        ]
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.event.title} - {self.checkin_time.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Calculate duration if checkout time is set
        if self.checkout_time and self.checkin_time:
            duration = self.checkout_time - self.checkin_time
            self.duration_minutes = int(duration.total_seconds() / 60)
        super().save(*args, **kwargs)
