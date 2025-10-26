from django import forms

from .models import Fine


class FineForm(forms.ModelForm):
    class Meta:
        model = Fine
        fields = ['student', 'amount', 'description', 'is_paid']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control select2'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }