from django.shortcuts import redirect
from django.contrib import messages

def student_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.groups.filter(name='Students').exists():
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Access denied. Student privileges required.")
            return redirect('dashboard_redirect')
    return _wrapped_view

def teacher_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.groups.filter(name='Teachers').exists() or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Access denied. Teacher privileges required.")
            return redirect('dashboard_redirect')
    return _wrapped_view
