from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy


@login_required
def dashboard_redirect(request):
    """Redirect users to their appropriate dashboard based on their role"""
    user = request.user
    
    # Check if user is superuser first
    if user.is_superuser:
        return redirect('admin_dashboard')
    elif user.groups.filter(name='Teachers').exists():
        return redirect('teacher_dashboard')
    elif user.groups.filter(name='Students').exists():
        return redirect('student_dashboard')
    else:
        messages.error(request, "No dashboard access. Please contact administrator.")
        return redirect('login')


@login_required
def change_password_manual(request):
    """Manual password change functionality"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        user = request.user
        errors = []

        # Check old password
        if not user.check_password(old_password):
            errors.append("Incorrect old password.")

        # Check if new passwords match
        if new_password1 != new_password2:
            errors.append("New passwords do not match.")

        # Validate password strength
        if new_password1:
            try:
                validate_password(new_password1, user)
            except ValidationError as e:
                errors.extend(e.messages)

        if errors:
            return render(request, 'authentication/change_password_manual.html', {'errors': errors})

        # Set and save new password
        user.set_password(new_password1)
        user.save()
        
        # Update session to prevent logout
        update_session_auth_hash(request, user)
        
        messages.success(request, 'Password changed successfully.')
        return redirect('profile')

    return render(request, 'authentication/change_password_manual.html')


@login_required
def profile_view(request):
    """User profile view"""
    user = request.user
    context = {'user': user}
    
    # Add role-specific profile data
    if hasattr(user, 'student_profile'):
        context['profile'] = user.student_profile
        context['profile_type'] = 'student'
    elif hasattr(user, 'teacher_profile'):
        context['profile'] = user.teacher_profile
        context['profile_type'] = 'teacher'
    else:
        context['profile_type'] = 'admin'
    
    return render(request, 'authentication/profile.html', context)


# Password Reset Views
class StudentPasswordResetView(PasswordResetView):
    """Custom password reset view"""
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('login')


class StudentPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirmation view"""
    template_name = 'registration/password_reset.html'
    success_url = reverse_lazy('login')


def home_redirect(request):
    """Redirect home requests to login"""
    return redirect('login')
