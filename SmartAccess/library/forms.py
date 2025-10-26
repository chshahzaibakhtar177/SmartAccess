from django import forms
import re
from datetime import date, timedelta

from .models import Book, BookCategory, BookBorrow, BookReservation


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