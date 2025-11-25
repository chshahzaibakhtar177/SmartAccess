from django import forms
from .models import Bus, Route, StudentBusAssignment
from students.models import Student


class BusForm(forms.ModelForm):
    class Meta:
        model = Bus
        fields = ['bus_number', 'driver_name', 'driver_contact', 'capacity', 'route', 'is_active']
        widgets = {
            'bus_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., BUS-001'
            }),
            'driver_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Driver full name'
            }),
            'driver_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '100'
            }),
            'route': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active routes
        from .models import Route
        self.fields['route'].queryset = Route.objects.filter(status='active').order_by('route_name')
    
    def clean_bus_number(self):
        bus_number = self.cleaned_data['bus_number']
        # Check if bus number already exists (excluding current instance when editing)
        qs = Bus.objects.filter(bus_number=bus_number)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Bus number already exists!")
        return bus_number
    
    def clean_capacity(self):
        capacity = self.cleaned_data['capacity']
        if capacity < 1:
            raise forms.ValidationError("Capacity must be at least 1")
        if capacity > 100:
            raise forms.ValidationError("Capacity cannot exceed 100")
        return capacity


class RouteForm(forms.ModelForm):
    estimated_hours = forms.IntegerField(
        min_value=0,
        max_value=23,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Hours'
        })
    )
    estimated_minutes = forms.IntegerField(
        min_value=0,
        max_value=59,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minutes'
        })
    )
    
    class Meta:
        model = Route
        fields = ['route_name', 'start_location', 'end_location', 'total_distance', 'status']
        widgets = {
            'route_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Route A - City Center'
            }),
            'start_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Starting location'
            }),
            'end_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ending location'
            }),
            'total_distance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0.1',
                'placeholder': 'Distance in km'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.estimated_time:
            total_seconds = int(self.instance.estimated_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            self.fields['estimated_hours'].initial = hours
            self.fields['estimated_minutes'].initial = minutes
    
    def clean_route_name(self):
        route_name = self.cleaned_data['route_name']
        qs = Route.objects.filter(route_name=route_name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Route name already exists!")
        return route_name
    
    def save(self, commit=True):
        from datetime import timedelta
        instance = super().save(commit=False)
        
        hours = self.cleaned_data.get('estimated_hours', 0) or 0
        minutes = self.cleaned_data.get('estimated_minutes', 0) or 0
        instance.estimated_time = timedelta(hours=hours, minutes=minutes)
        
        if commit:
            instance.save()
        return instance


class StudentBusAssignmentForm(forms.ModelForm):
    class Meta:
        model = StudentBusAssignment
        fields = ['student', 'bus', 'pickup_location', 'notes']
        widgets = {
            'student': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Select a student'
            }),
            'bus': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Select a bus'
            }),
            'pickup_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Student pickup/drop location'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes (optional)'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show students who don't have an active assignment (or current student if editing)
        if self.instance.pk:
            assigned_students = StudentBusAssignment.objects.filter(
                is_active=True
            ).exclude(pk=self.instance.pk).values_list('student_id', flat=True)
        else:
            assigned_students = StudentBusAssignment.objects.filter(
                is_active=True
            ).values_list('student_id', flat=True)
        
        self.fields['student'].queryset = Student.objects.exclude(
            id__in=assigned_students
        ).order_by('roll_number')
        
        # Only show active buses
        self.fields['bus'].queryset = Bus.objects.filter(is_active=True).order_by('bus_number')
        
        # Add help text explaining bus already has route
        self.fields['bus'].help_text = 'Select a bus - each bus has its assigned route'
    
    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        bus = cleaned_data.get('bus')
        
        # Auto-set is_active to True for new assignments
        if not self.instance.pk:
            cleaned_data['is_active'] = True
        
        # Check if student already has an active assignment
        if student:
            existing = StudentBusAssignment.objects.filter(
                student=student,
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            
            if existing.exists():
                raise forms.ValidationError(
                    f"Student {student.roll_number} already has an active bus assignment!"
                )
        
        # Check bus capacity
        if bus:
            active_count = StudentBusAssignment.objects.filter(
                bus=bus,
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance.pk else None).count()
            
            if active_count >= bus.capacity:
                raise forms.ValidationError(
                    f"Bus {bus.bus_number} is at full capacity ({bus.capacity} students)"
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Auto-assign route from the selected bus
        if instance.bus and not instance.route_id:
            instance.route = instance.bus.route
        
        # Ensure is_active is True for new assignments
        if not instance.pk:
            instance.is_active = True
        
        if commit:
            instance.save()
        return instance


class BulkStudentAssignmentForm(forms.Form):
    """Form for bulk assigning students to a bus"""
    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=True
    )
    bus = forms.ModelChoiceField(
        queryset=Bus.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=True
    )
    route = forms.ModelChoiceField(
        queryset=Route.objects.filter(status='active'),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=True
    )
    pickup_location = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Common pickup location for selected students'
        }),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show students without active assignments
        assigned_students = StudentBusAssignment.objects.filter(
            is_active=True
        ).values_list('student_id', flat=True)
        
        self.fields['students'].queryset = Student.objects.exclude(
            id__in=assigned_students
        ).order_by('roll_number')
