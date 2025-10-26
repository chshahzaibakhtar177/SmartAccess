from django import forms
import re

from .models import (Student, Fine, Teacher, Event, EventCategory, EventRegistration, 
                     EventAttendance, Book, BookCategory, BookBorrow, BookReservation)
from django.contrib.auth.models import User



class StudentForm(forms.ModelForm):
    def clean_nfc_uid(self):
        nfc_uid = self.cleaned_data['nfc_uid']
        
        # Allow None/empty values since nfc_uid is now nullable
        if nfc_uid is None or nfc_uid == '':
            return nfc_uid
            
        # Validate format only if value is provided
        if not re.match(r'^[A-Fa-f0-9]+$', nfc_uid):
            raise forms.ValidationError("NFC UID must be hexadecimal")
        return nfc_uid
    
    class Meta:
        model = Student
        fields = ['name', 'roll_number', 'is_in_university']  # Removed nfc_uid from form
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'roll_number': forms.TextInput(attrs={'class': 'form-control'}),
            'is_in_university': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    
class FineForm(forms.ModelForm):
    class Meta:
        model = Fine
        fields = ['student', 'amount', 'description', 'is_paid'
        ]
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control select2'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }





class TeacherCreationForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Teacher
        fields = ['name', 'department']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username


class StudentPhotoForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['photo']
        widgets = {
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }


class TeacherPhotoForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['photo']
        widgets = {
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }


# Event Management Forms

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'category', 'organizer',
            'start_datetime', 'end_datetime', 'registration_deadline',
            'venue', 'max_capacity', 'registration_fee',
            'requires_nfc_checkin', 'image'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'organizer': forms.Select(attrs={'class': 'form-control'}),
            'start_datetime': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_datetime': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'registration_deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'venue': forms.TextInput(attrs={'class': 'form-control'}),
            'max_capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'registration_fee': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'requires_nfc_checkin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        registration_deadline = cleaned_data.get('registration_deadline')

        # Validate datetime relationships
        if start_datetime and end_datetime:
            if start_datetime >= end_datetime:
                raise forms.ValidationError("End time must be after start time.")

        if start_datetime and registration_deadline:
            if registration_deadline >= start_datetime:
                raise forms.ValidationError("Registration deadline must be before event start time.")

        return cleaned_data


class EventCategoryForm(forms.ModelForm):
    class Meta:
        model = EventCategory
        fields = ['name', 'description', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            })
        }


class EventRegistrationForm(forms.ModelForm):
    class Meta:
        model = EventRegistration
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any special requirements or dietary restrictions...'
            })
        }


class EventAttendanceForm(forms.ModelForm):
    class Meta:
        model = EventAttendance
        fields = ['feedback_rating', 'feedback_comments']
        widgets = {
            'feedback_rating': forms.Select(attrs={'class': 'form-control'}),
            'feedback_comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Share your feedback about this event...'
            })
        }


class EventSearchForm(forms.Form):
    SEARCH_CHOICES = [
        ('all', 'All Events'),
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ]
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search events...'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=EventCategory.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=SEARCH_CHOICES,
        required=False,
        initial='all',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

# Library Management Forms
class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['isbn', 'title', 'author', 'publisher', 'publication_year', 'edition', 
                 'category', 'pages', 'location', 'copy_number', 'status', 'price', 
                 'cover_image', 'nfc_tag_uid']
        widgets = {
            'isbn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ISBN-13 format (e.g., 9781234567890)'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Book title'
            }),
            'author': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Author name'
            }),
            'publisher': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Publisher name'
            }),
            'publication_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1900',
                'max': '2030'
            }),
            'edition': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Edition (optional)'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'pages': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Shelf/Section location'
            }),
            'copy_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'nfc_tag_uid': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'NFC Tag UID (optional)'
            })
        }
    
    def clean_isbn(self):
        isbn = self.cleaned_data['isbn']
        # Remove any hyphens or spaces
        isbn = isbn.replace('-', '').replace(' ', '')
        
        # Check if it's exactly 13 digits
        if not isbn.isdigit() or len(isbn) != 13:
            raise forms.ValidationError("ISBN must be exactly 13 digits")
        
        return isbn
    
    def clean_nfc_tag_uid(self):
        nfc_uid = self.cleaned_data['nfc_tag_uid']
        if nfc_uid and not re.match(r'^[A-Fa-f0-9]+$', nfc_uid):
            raise forms.ValidationError("NFC UID must be hexadecimal")
        return nfc_uid

class BookCategoryForm(forms.ModelForm):
    class Meta:
        model = BookCategory
        fields = ['name', 'description', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            })
        }

class BookBorrowForm(forms.ModelForm):
    class Meta:
        model = BookBorrow
        fields = ['due_date', 'checkout_notes']
        widgets = {
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'checkout_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any special notes for this borrowing...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default due date to 14 days from now
        from datetime import date, timedelta
        default_due = date.today() + timedelta(days=14)
        self.fields['due_date'].initial = default_due

class BookReturnForm(forms.ModelForm):
    class Meta:
        model = BookBorrow
        fields = ['return_notes']
        widgets = {
            'return_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Book condition and return notes...'
            })
        }

class BookReservationForm(forms.ModelForm):
    class Meta:
        model = BookReservation
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any special requirements or notes...'
            })
        }

class BookSearchForm(forms.Form):
    SEARCH_CHOICES = [
        ('all', 'All Books'),
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('reserved', 'Reserved'),
        ('maintenance', 'Under Maintenance'),
    ]
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title, author, ISBN...'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=BookCategory.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=SEARCH_CHOICES,
        required=False,
        initial='all',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

