from django import forms
from django.contrib.auth.models import User
from .models import Alumni, AlumniEventParticipation


class AlumniRegistrationForm(forms.ModelForm):
    """Form for registering new alumni or converting students to alumni"""
    
    class Meta:
        model = Alumni
        fields = [
            'graduation_year', 'degree_program', 'current_job_title',
            'current_company', 'industry', 'linkedin_profile',
            'phone_number', 'alternative_email', 'current_address',
            'achievements', 'is_public_profile'
        ]
        widgets = {
            'graduation_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1950',
                'max': '2030'
            }),
            'degree_program': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Computer Science, Business Administration'
            }),
            'current_job_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Software Engineer, Manager'
            }),
            'current_company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company name'
            }),
            'industry': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Technology, Finance, Healthcare'
            }),
            'linkedin_profile': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/yourprofile'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'alternative_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'alternative@email.com'
            }),
            'current_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Current residential address'
            }),
            'achievements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Notable achievements, awards, or accomplishments'
            }),
            'is_public_profile': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_graduation_year(self):
        year = self.cleaned_data.get('graduation_year')
        if year and (year < 1950 or year > 2030):
            raise forms.ValidationError('Please enter a valid graduation year.')
        return year


class AlumniProfileUpdateForm(forms.ModelForm):
    """Form for updating alumni profile information"""
    
    # Add user fields for updating basic info
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control'
    }))
    
    class Meta:
        model = Alumni
        fields = [
            'current_job_title', 'current_company', 'industry',
            'linkedin_profile', 'phone_number', 'alternative_email',
            'current_address', 'achievements', 'is_public_profile'
        ]
        widgets = {
            'current_job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'current_company': forms.TextInput(attrs={'class': 'form-control'}),
            'industry': forms.TextInput(attrs={'class': 'form-control'}),
            'linkedin_profile': forms.URLInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'alternative_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'current_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'achievements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_public_profile': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email


class AlumniEventParticipationForm(forms.ModelForm):
    """Form for alumni event participation"""
    
    class Meta:
        model = AlumniEventParticipation
        fields = ['participation_type', 'notes']
        widgets = {
            'participation_type': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any additional notes about your participation'
            })
        }


class AlumniSearchForm(forms.Form):
    """Form for searching alumni directory"""
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, company, or degree program'
        })
    )
    
    graduation_year = forms.CharField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Graduation Year'
        })
    )
    
    industry = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Industry'
        })
    )
    
    degree_program = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Degree Program'
        })
    )


class ConvertStudentForm(forms.Form):
    """Form for converting a student to alumni status"""
    
    graduation_year = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1950',
            'max': '2030'
        })
    )
    
    degree_program = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Degree program completed'
        })
    )
    
    final_gpa = forms.DecimalField(
        max_digits=4,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'max': '4.0',
            'placeholder': 'Final GPA (optional)'
        })
    )
    
    create_alumni_profile = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Create alumni profile for networking and events'
    )