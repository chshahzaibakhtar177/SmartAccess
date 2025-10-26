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
    borrowing_limit = models.PositiveIntegerField(default=10)  # Default borrowing limit of 10 books

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
        from django.utils import timezone
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

# Library Management Models
class BookCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#6c757d', help_text='Hex color code for category display')
    
    class Meta:
        verbose_name_plural = "Book Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Book(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('reserved', 'Reserved'),
        ('maintenance', 'Under Maintenance'),
        ('lost', 'Lost'),
    ]
    
    # Book Information
    isbn = models.CharField(max_length=13, unique=True, help_text='ISBN-13 format')
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    publisher = models.CharField(max_length=100)
    publication_year = models.PositiveIntegerField()
    edition = models.CharField(max_length=50, blank=True)
    category = models.ForeignKey(BookCategory, on_delete=models.CASCADE, related_name='books')
    
    # Physical Information
    pages = models.PositiveIntegerField(null=True, blank=True)
    location = models.CharField(max_length=100, help_text='Shelf/Section location in library')
    copy_number = models.PositiveIntegerField(default=1, help_text='Copy number if multiple copies exist')
    
    # Library Management
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    acquisition_date = models.DateField(auto_now_add=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Book Cover
    cover_image = models.ImageField(upload_to='book_covers/', null=True, blank=True)
    
    # NFC Integration
    nfc_tag_uid = models.CharField(max_length=50, unique=True, null=True, blank=True, 
                                   help_text='NFC tag attached to book for quick checkout')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['title']
        unique_together = ['isbn', 'copy_number']
        indexes = [
            models.Index(fields=['isbn']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['nfc_tag_uid']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.author} (Copy #{self.copy_number})"
    
    @property
    def is_available(self):
        return self.status == 'available'
    
    @property
    def current_borrower(self):
        """Get current borrower if book is borrowed"""
        try:
            borrow = self.borrows.filter(status='active').first()
            return borrow.student if borrow else None
        except Exception:
            return None
    
    @property
    def current_borrow(self):
        """Get current borrow record if book is borrowed"""
        try:
            return self.borrows.filter(status__in=['active', 'overdue']).first()
        except Exception:
            return None

class BookBorrow(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
        ('lost', 'Lost'),
        ('renewed', 'Renewed'),
    ]
    
    # Borrowing Information
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrows')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='book_borrows')
    
    # Dates
    borrow_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateTimeField(null=True, blank=True)
    
    # Status and Details
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    renewal_count = models.PositiveIntegerField(default=0)
    max_renewals = models.PositiveIntegerField(default=2)
    
    # Fine Management
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fine_paid = models.BooleanField(default=False)
    
    # NFC Integration
    nfc_checkout = models.BooleanField(default=False, help_text='Was checked out using NFC')
    nfc_checkin = models.BooleanField(default=False, help_text='Was returned using NFC')
    
    # Notes
    checkout_notes = models.TextField(blank=True)
    return_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-borrow_date']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['book', 'status']),
            models.Index(fields=['due_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.book.title} ({self.status})"
    
    @property
    def is_overdue(self):
        """Check if book is overdue"""
        if self.status in ['returned', 'lost']:
            return False
        return timezone.now().date() > self.due_date
    
    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if not self.is_overdue:
            return 0
        return (timezone.now().date() - self.due_date).days
    
    @property
    def can_renew(self):
        """Check if book can be renewed"""
        return (self.renewal_count < self.max_renewals and 
                self.status == 'active' and 
                not self.is_overdue)
    
    def calculate_fine(self, fine_per_day=5.00):
        """Calculate fine for overdue book"""
        if self.is_overdue:
            return self.days_overdue * fine_per_day
        return 0.00
    
    def save(self, *args, **kwargs):
        # Calculate and update fine first
        if self.is_overdue and self.status == 'active':
            self.fine_amount = self.calculate_fine()
            self.status = 'overdue'
        
        # Save borrow record first
        super().save(*args, **kwargs)
        
        # Then update book status (prevents infinite loop)
        book_status_changed = False
        if self.status == 'active' and self.book.status != 'borrowed':
            self.book.status = 'borrowed'
            book_status_changed = True
        elif self.status == 'returned' and self.book.status != 'available':
            self.book.status = 'available'
            book_status_changed = True
        elif self.status == 'lost' and self.book.status != 'lost':
            self.book.status = 'lost'
            book_status_changed = True
        
        # Only save book if status actually changed
        if book_status_changed:
            Book.objects.filter(id=self.book.id).update(status=self.book.status)

class BookReservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='book_reservations')
    
    # Reservation Details
    reservation_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(help_text='Reservation expires if not collected by this date')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Fulfillment
    fulfilled_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-reservation_date']
        # Fixed: Only prevent duplicate pending reservations, not all statuses
        constraints = [
            models.UniqueConstraint(
                fields=['book', 'student'],
                condition=models.Q(status='pending'),
                name='unique_pending_reservation'
            )
        ]
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['book', 'status']),
            models.Index(fields=['expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.book.title} ({self.status})"
    
    @property
    def is_expired(self):
        """Check if reservation has expired"""
        return timezone.now() > self.expiry_date and self.status == 'pending'
    
    def save(self, *args, **kwargs):
        # Auto-expire old reservations
        if self.is_expired:
            self.status = 'expired'
        super().save(*args, **kwargs)


