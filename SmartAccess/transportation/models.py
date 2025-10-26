from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Bus(models.Model):
    bus_number = models.CharField(max_length=20, unique=True)
    driver_name = models.CharField(max_length=100)
    driver_contact = models.CharField(max_length=15)
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    route = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bus"
        verbose_name_plural = "Buses"
        ordering = ['bus_number']

    def __str__(self):
        return f"Bus {self.bus_number} - {self.route}"


class Route(models.Model):
    ROUTE_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
    ]
    
    route_name = models.CharField(max_length=100, unique=True)
    start_location = models.CharField(max_length=200)
    end_location = models.CharField(max_length=200)
    total_distance = models.FloatField(help_text="Distance in kilometers")
    estimated_time = models.DurationField(help_text="Estimated travel time")
    status = models.CharField(max_length=20, choices=ROUTE_STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Route"
        verbose_name_plural = "Routes"
        ordering = ['route_name']

    def __str__(self):
        return f"{self.route_name} ({self.start_location} → {self.end_location})"


class TransportLog(models.Model):
    BOARDING_STATUS_CHOICES = [
        ('boarded', 'Boarded'),
        ('alighted', 'Alighted'),
        ('no_show', 'No Show'),
    ]
    
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('staff', 'Staff'),
    ]
    
    # User identification
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transport_logs')
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    
    # NFC identification (linking to existing NFC system)
    nfc_uid = models.CharField(max_length=50, db_index=True)
    
    # Transport details
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='transport_logs')
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='transport_logs')
    
    # Boarding information
    boarding_status = models.CharField(max_length=20, choices=BOARDING_STATUS_CHOICES)
    boarding_location = models.CharField(max_length=200)
    boarding_time = models.DateTimeField()
    alighting_time = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Additional notes or remarks")

    class Meta:
        verbose_name = "Transport Log"
        verbose_name_plural = "Transport Logs"
        ordering = ['-boarding_time']
        indexes = [
            models.Index(fields=['nfc_uid', 'boarding_time']),
            models.Index(fields=['bus', 'boarding_time']),
            models.Index(fields=['user', 'boarding_time']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.bus} ({self.boarding_time.strftime('%Y-%m-%d %H:%M')})"

    def get_user_profile(self):
        """Get the specific user profile (Student/Teacher) based on user_type"""
        if self.user_type == 'student':
            try:
                return self.user.student_profile
            except AttributeError:
                return None
        elif self.user_type == 'teacher':
            try:
                return self.user.teacher_profile
            except AttributeError:
                return None
        return None

    def get_travel_duration(self):
        """Calculate travel duration if both boarding and alighting times are available"""
        if self.alighting_time and self.boarding_time:
            return self.alighting_time - self.boarding_time
        return None


class BusSchedule(models.Model):
    SCHEDULE_TYPE_CHOICES = [
        ('morning', 'Morning'),
        ('evening', 'Evening'),
        ('special', 'Special'),
    ]
    
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='schedules')
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='schedules')
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPE_CHOICES)
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    weekdays = models.JSONField(default=list, help_text="List of weekday numbers (0=Monday, 6=Sunday)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bus Schedule"
        verbose_name_plural = "Bus Schedules"
        ordering = ['departure_time']
        unique_together = ['bus', 'route', 'schedule_type', 'departure_time']

    def __str__(self):
        return f"{self.bus.bus_number} - {self.route.route_name} ({self.get_schedule_type_display()} {self.departure_time})"
