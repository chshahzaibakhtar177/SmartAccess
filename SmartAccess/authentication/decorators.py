"""
Authentication decorators for SmartAccess modular architecture.

These decorators handle role-based access control for different user types.
Moved from legacy student app to authentication app for proper modularization.
"""

from django.shortcuts import redirect
from django.contrib import messages


def student_required(view_func):
    """
    Decorator to require student privileges for a view.
    
    Checks if the user belongs to the 'Students' group.
    Redirects to dashboard_redirect with error message if access denied.
    """
    def _wrapped_view(request, *args, **kwargs):
        if request.user.groups.filter(name='Students').exists():
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Access denied. Student privileges required.")
            return redirect('dashboard_redirect')
    return _wrapped_view


def teacher_required(view_func):
    """
    Decorator to require teacher privileges for a view.
    
    Checks if the user belongs to the 'Teachers' group or is a superuser.
    Redirects to dashboard_redirect with error message if access denied.
    """
    def _wrapped_view(request, *args, **kwargs):
        if request.user.groups.filter(name='Teachers').exists() or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Access denied. Teacher privileges required.")
            return redirect('dashboard_redirect')
    return _wrapped_view


def admin_required(view_func):
    """
    Decorator to require admin/superuser privileges for a view.
    
    Checks if the user is a superuser.
    Redirects to dashboard_redirect with error message if access denied.
    """
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Access denied. Administrator privileges required.")
            return redirect('dashboard_redirect')
    return _wrapped_view