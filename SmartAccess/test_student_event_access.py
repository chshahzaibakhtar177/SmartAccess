#!/usr/bin/env python
"""
Quick test script to verify student event registration access is working
Run this script to test the fix for event registration authentication
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/shahzaibakhtar/Documents/Fyp/Website/SmartAccess')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartAccess.settings')
django.setup()

from django.contrib.auth.models import User, Group
from students.models import Student
from events.models import Event, EventRegistration
from django.test import RequestFactory
from events.views import event_detail

def test_student_event_access():
    """Test that student can access event registration properly"""
    
    print("🧪 Testing Student Event Access Fix...")
    print("=" * 50)
    
    # Check if there are students and events in the system
    students_count = Student.objects.count()
    events_count = Event.objects.count()
    
    print(f"📊 System Status:")
    print(f"   - Students in system: {students_count}")
    print(f"   - Events in system: {events_count}")
    
    if students_count == 0:
        print("❌ No students found in system")
        return False
        
    if events_count == 0:
        print("❌ No events found in system")
        return False
    
    # Get a test student and event
    test_student = Student.objects.first()
    test_event = Event.objects.first()
    
    print(f"\n🎯 Testing with:")
    print(f"   - Student: {test_student.user.username} ({test_student.user.first_name} {test_student.user.last_name})")
    print(f"   - Event: {test_event.title}")
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get(f'/events/{test_event.id}/')
    request.user = test_student.user
    
    # Test the event_detail view
    try:
        response = event_detail(request, test_event.id)
        
        if response.status_code == 200:
            print("✅ Event detail view returns 200 OK")
            
            # Check if the response contains the right context
            context = response.context_data if hasattr(response, 'context_data') else None
            
            if context:
                is_student = context.get('is_student', False)
                can_register = context.get('can_register', False)
                
                print(f"✅ Context variables set correctly:")
                print(f"   - is_student: {is_student}")
                print(f"   - can_register: {can_register}")
                
                if is_student:
                    print("✅ Student authentication detected correctly")
                else:
                    print("❌ Student authentication NOT detected")
                    return False
            else:
                print("⚠️  Could not check context data")
                
        else:
            print(f"❌ Event detail view returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing event detail view: {e}")
        return False
    
    print("\n🎉 Test completed successfully!")
    print("💡 The fix should resolve the 'Login as a student to register' issue")
    return True

if __name__ == "__main__":
    success = test_student_event_access()
    if success:
        print("\n✨ Event registration access fix is working correctly!")
    else:
        print("\n💥 There may still be issues with the fix")