from django.db import models
from django.utils import timezone
from students.models import Student

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
                name='unique_pending_library_reservation'
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
