#!/usr/bin/env python
"""
Test script to verify event registration functionality
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/shahzaibakhtar/Documents/Fyp/Website/SmartAccess')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartAccess.settings')
django.setup()

from django.contrib.auth.models import User
from students.models import Student
from events.models import Event, EventRegistration

def test_registration():
    """Test event registration functionality"""
    
    print("🧪 Testing Event Registration Functionality")
    print("=" * 50)
    
    # Get a test student and event
    student = Student.objects.first()
    event = Event.objects.first()
    
    if not student or not event:
        print("❌ Missing student or event data")
        return False
    
    print(f"👤 Student: {student.user.username}")
    print(f"🎪 Event: {event.title}")
    print(f"📅 Registration Status: {event.is_registration_open}")
    print(f"👥 Capacity: {event.registered_count}/{event.max_capacity}")
    
    # Check if already registered
    existing = EventRegistration.objects.filter(event=event, student=student).first()
    
    if existing:
        print(f"🔍 Existing Registration: {existing.status} (Date: {existing.registration_date})")
        
        if existing.status == 'cancelled':
            print("♻️  Previous registration was cancelled - can re-register")
        else:
            print("✅ Student is already registered for this event")
            return True
    else:
        print("🆕 No existing registration found")
        
        # Try to create a registration
        try:
            registration = EventRegistration.objects.create(
                event=event,
                student=student,
                status='confirmed'
            )
            print(f"✅ Successfully created registration: {registration.id}")
            print(f"📝 Status: {registration.status}")
            print(f"📅 Date: {registration.registration_date}")
            return True
            
        except Exception as e:
            print(f"❌ Registration failed: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = test_registration()
    if success:
        print("\n🎉 Event registration system is working!")
    else:
        print("\n💥 Registration system has issues")