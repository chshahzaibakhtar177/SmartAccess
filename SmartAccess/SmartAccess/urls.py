"""
URL configuration for SmartAccess project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.shortcuts import redirect
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import functions from modular apps
from students.views import (
    assign_card_request, remove_card, assign_card_page, profile_view
)


def home_redirect(request):
    return redirect('login')

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('', home_redirect, name='home_redirect'),
    
    # ============================
    # MODULAR APP URLS
    # ============================
    
    # Authentication URLs (modular)
    path('', include('authentication.urls')),
    
    # Student management URLs (modular)
    path('students/', include('students.urls')),
    
    # Teacher management URLs (modular)  
    path('teachers/', include('teachers.urls')),
    
    # Attendance management URLs (modular)
    path('attendance/', include('attendance.urls')),
    
    # Fines management URLs (modular)
    path('fines/', include('fines.urls')),
    
    # Events management URLs (modular)
    path('events/', include('events.urls')),
    
    # Library management URLs (modular)
    path('library/', include('library.urls')),
    
    # Transportation management URLs (modular)
    path('transportation/', include('transportation.urls')),
    
    # Dashboard URLs (modular)
    path('', include('dashboards.urls')),
    
    # ============================
    # LEGACY COMPATIBILITY URLS
    # Only essential functions for backward compatibility
    # ============================
    
    # NFC Card assignment URLs (legacy - essential functionality)
    path('assign-card/<int:student_id>/', assign_card_page, name='assign_card_page'),
    path('assign-card-request/<int:student_id>/', assign_card_request, name='assign_card_request'),
    path('remove-card/<int:student_id>/', remove_card, name='remove_card'),
    
    # Profile URL (legacy compatibility)
    path('profile/', profile_view, name='profile'),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
