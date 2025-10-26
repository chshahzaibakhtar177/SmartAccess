from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from events.models import Event


class Alumni(models.Model):
    """Alumni model for tracking university graduates"""
    
    # Link to Django User model
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='alumni_profile')
    
    # Academic Information
    graduation_year = models.PositiveIntegerField(help_text='Year of graduation from the university')
    degree_program = models.CharField(max_length=100, help_text='Degree program completed')
    final_gpa = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True,
        help_text='Final GPA at graduation'
    )
    
    # Professional Information
    current_job_title = models.CharField(max_length=100, blank=True, help_text='Current job title')
    current_company = models.CharField(max_length=100, blank=True, help_text='Current employer')
    industry = models.CharField(max_length=50, blank=True, help_text='Industry sector')
    linkedin_profile = models.URLField(blank=True, help_text='LinkedIn profile URL')
    
    # Contact Information
    phone_number = models.CharField(max_length=20, blank=True, help_text='Current phone number')
    alternative_email = models.EmailField(blank=True, help_text='Alternative email address')
    current_address = models.TextField(blank=True, help_text='Current residential address')
    
    # Additional Information
    achievements = models.TextField(blank=True, help_text='Notable achievements and accomplishments')
    profile_photo = models.ImageField(
        upload_to='alumni_photos/', null=True, blank=True,
        help_text='Profile photo for alumni directory'
    )
    
    # Status and Privacy
    is_active = models.BooleanField(default=True, help_text='Is alumni profile active')
    is_public_profile = models.BooleanField(
        default=True, help_text='Allow profile to be visible in alumni directory'
    )
    
    # Metadata
    registration_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Alumni'
        verbose_name_plural = 'Alumni'
        ordering = ['-graduation_year', 'user__last_name', 'user__first_name']
        indexes = [
            models.Index(fields=['graduation_year']),
            models.Index(fields=['degree_program']),
            models.Index(fields=['current_company']),
            models.Index(fields=['industry']),
            models.Index(fields=['is_active', 'is_public_profile']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Class of {self.graduation_year}"
    
    @property
    def full_name(self):
        """Get alumni's full name"""
        return self.user.get_full_name() or self.user.username
    
    @property
    def graduation_class(self):
        """Get graduation class description"""
        return f"Class of {self.graduation_year}"
    
    @property
    def years_since_graduation(self):
        """Calculate years since graduation"""
        current_year = timezone.now().year
        return current_year - self.graduation_year
    
    @property
    def event_participations_count(self):
        """Get count of event participations"""
        return self.event_participations.count()
    
    def get_recent_events(self, limit=5):
        """Get recent event participations"""
        return self.event_participations.select_related('event').order_by('-participation_date')[:limit]


class AlumniEventParticipation(models.Model):
    """Model to track alumni participation in university events"""
    
    PARTICIPATION_TYPES = [
        ('attendee', 'Attendee'),
        ('speaker', 'Speaker/Presenter'),
        ('organizer', 'Event Organizer'),
        ('volunteer', 'Volunteer'),
        ('sponsor', 'Event Sponsor'),
        ('mentor', 'Mentor/Judge'),
    ]
    
    # Relationships
    alumni = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='event_participations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='alumni_participations')
    
    # Participation Details
    participation_type = models.CharField(
        max_length=20, choices=PARTICIPATION_TYPES, default='attendee',
        help_text='Type of participation in the event'
    )
    participation_date = models.DateTimeField(auto_now_add=True)
    attendance_confirmed = models.BooleanField(
        default=False, help_text='Has attendance been confirmed'
    )
    
    # Additional Information
    notes = models.TextField(blank=True, help_text='Additional notes about participation')
    contribution_details = models.TextField(
        blank=True, help_text='Details about alumni contribution to the event'
    )
    
    # Rating and Feedback
    event_rating = models.PositiveSmallIntegerField(
        null=True, blank=True,
        choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)],
        help_text='Alumni rating of the event (1-5 stars)'
    )
    feedback = models.TextField(blank=True, help_text='Alumni feedback about the event')
    
    class Meta:
        unique_together = ['alumni', 'event']
        ordering = ['-participation_date']
        verbose_name = 'Alumni Event Participation'
        verbose_name_plural = 'Alumni Event Participations'
        indexes = [
            models.Index(fields=['alumni', 'participation_date']),
            models.Index(fields=['event', 'participation_type']),
            models.Index(fields=['participation_date']),
        ]
    
    def __str__(self):
        return f"{self.alumni.full_name} - {self.event.title} ({self.get_participation_type_display()})"
    
    @property
    def is_past_event(self):
        """Check if the event has already occurred"""
        return self.event.end_datetime < timezone.now()
    
    @property
    def can_provide_feedback(self):
        """Check if alumni can provide feedback (event is past and attended)"""
        return self.is_past_event and self.attendance_confirmed


class AlumniNetworking(models.Model):
    """Model for alumni networking connections and mentorship"""
    
    CONNECTION_TYPES = [
        ('professional', 'Professional Network'),
        ('mentorship', 'Mentorship'),
        ('collaboration', 'Business Collaboration'),
        ('friendship', 'Personal Connection'),
    ]
    
    # The alumni who initiated the connection
    requester = models.ForeignKey(
        Alumni, on_delete=models.CASCADE, related_name='sent_connections'
    )
    
    # The alumni who received the connection request
    recipient = models.ForeignKey(
        Alumni, on_delete=models.CASCADE, related_name='received_connections'
    )
    
    # Connection Details
    connection_type = models.CharField(
        max_length=20, choices=CONNECTION_TYPES, default='professional'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('declined', 'Declined'),
        ],
        default='pending'
    )
    
    # Messages
    request_message = models.TextField(
        blank=True, help_text='Message from requester'
    )
    response_message = models.TextField(
        blank=True, help_text='Response message'
    )
    
    # Metadata
    created_date = models.DateTimeField(auto_now_add=True)
    response_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['requester', 'recipient']
        ordering = ['-created_date']
        verbose_name = 'Alumni Connection'
        verbose_name_plural = 'Alumni Connections'
    
    def __str__(self):
        return f"{self.requester.full_name} → {self.recipient.full_name} ({self.status})"
    
    def accept_connection(self, response_message=''):
        """Accept the connection request"""
        self.status = 'accepted'
        self.response_message = response_message
        self.response_date = timezone.now()
        self.save()
    
    def decline_connection(self, response_message=''):
        """Decline the connection request"""
        self.status = 'declined'
        self.response_message = response_message
        self.response_date = timezone.now()
        self.save()


class AlumniJobPosting(models.Model):
    """Model for alumni to post job opportunities"""
    
    JOB_TYPES = [
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance'),
    ]
    
    # Posted by alumni
    posted_by = models.ForeignKey(
        Alumni, on_delete=models.CASCADE, related_name='job_postings'
    )
    
    # Job Details
    job_title = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES)
    location = models.CharField(max_length=100)
    salary_range = models.CharField(max_length=50, blank=True)
    
    # Job Description
    job_description = models.TextField(help_text='Detailed job description')
    requirements = models.TextField(help_text='Job requirements and qualifications')
    benefits = models.TextField(blank=True, help_text='Benefits and perks')
    
    # Application Details
    application_email = models.EmailField(help_text='Email for job applications')
    application_url = models.URLField(blank=True, help_text='Online application URL')
    application_deadline = models.DateField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text='Feature on alumni dashboard')
    
    # Metadata
    posted_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-posted_date']
        verbose_name = 'Alumni Job Posting'
        verbose_name_plural = 'Alumni Job Postings'
        indexes = [
            models.Index(fields=['is_active', 'posted_date']),
            models.Index(fields=['job_type', 'location']),
        ]
    
    def __str__(self):
        return f"{self.job_title} at {self.company_name}"
    
    @property
    def is_application_open(self):
        """Check if applications are still being accepted"""
        if not self.is_active:
            return False
        if self.application_deadline:
            return timezone.now().date() <= self.application_deadline
        return True
