from django import forms
import re

from .models import Student,Fine, Teacher
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

