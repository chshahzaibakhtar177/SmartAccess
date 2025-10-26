from django import forms
import re

from .models import Student


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