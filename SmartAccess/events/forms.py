from django import forms

from .models import Event, EventCategory, EventRegistration, EventAttendance


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
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter category description'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#007bff'
            })
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            # Check for duplicate names (case insensitive)
            existing = EventCategory.objects.filter(name__iexact=name)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError('A category with this name already exists.')
        return name


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
        choices=[('all', 'All Status')] + Event.STATUS_CHOICES,
        required=False,
        initial='all',
        widget=forms.Select(attrs={'class': 'form-control'})
    )