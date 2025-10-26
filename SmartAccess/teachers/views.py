from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages

# Import from the modular models
from teachers.models import Teacher
from teachers.forms import TeacherCreationForm, TeacherPhotoForm
from authentication.decorators import teacher_required

# Teachers management views - migrated from legacy student app

@login_required
def add_teacher(request):
    """Add teacher view - migrated from legacy student app"""
    # Restrict access to superusers only
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard_redirect')
        
    if request.method == 'POST':
        form = TeacherCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Create user
            user = User.objects.create_user(username=username, password=password)
            
            # Add to Teachers group
            group, created = Group.objects.get_or_create(name='Teachers')
            user.groups.add(group)
            
            # Create and save teacher profile
            teacher = form.save(commit=False)
            teacher.user = user
            teacher.save()
            
            messages.success(request, f"Teacher {teacher.name} created successfully.")
            return redirect('add_teacher')
    else:
        form = TeacherCreationForm()
    return render(request, 'admin/add_teacher.html', {'form': form})


@login_required
@teacher_required
def update_teacher_photo(request):
    """Update teacher photo view - migrated from legacy student app"""
    if request.method == 'POST':
        form = TeacherPhotoForm(request.POST, request.FILES, instance=request.user.teacher_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Photo updated successfully!')
    return redirect('teacher_dashboard')
