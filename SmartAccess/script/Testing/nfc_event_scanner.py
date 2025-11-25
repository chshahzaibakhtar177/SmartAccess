#!/usr/bin/env python3
"""
NFC Event Scanner for SmartAccess
Automatically detects active events and marks students present
"""

import board
import busio
from adafruit_pn532.i2c import PN532_I2C
import requests
import time
from datetime import datetime

# Configuration
DJANGO_SERVER = "http://172.20.10.4:8001"  # Django server IP (same as Entry.py)
SCAN_COOLDOWN = 3  # Seconds between scans of same card

# Initialize I2C and PN532
i2c = busio.I2C(board.SCL, board.SDA)
pn532 = PN532_I2C(i2c, debug=False)

# Configure PN532
pn532.SAM_configuration()

print("=" * 60)
print("NFC Event Attendance Scanner - SmartAccess")
print("=" * 60)
print(f"Server: {DJANGO_SERVER}")
print("Waiting for NFC cards...")
print("Press Ctrl+C to exit")
print("=" * 60)

last_uid = None
last_scan_time = 0

def convert_uid_to_string(uid):
    """Convert UID bytes to hex string"""
    return ''.join([format(i, '02x') for i in uid])

def mark_attendance(card_id):
    """Send card scan to Django backend"""
    url = f"{DJANGO_SERVER}/events/api/nfc-attendance/"
    
    payload = {
        'card_id': card_id,
        'scan_time': datetime.now().isoformat()
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        data = response.json()
        
        if response.status_code == 200 and data.get('success'):
            print("\n" + "="*60)
            print("✓ ATTENDANCE MARKED")
            print("-"*60)
            print(f"Student: {data.get('student_name')}")
            print(f"Roll No: {data.get('roll_number')}")
            print(f"Event: {data.get('event_title')}")
            print(f"Time: {data.get('attendance_time')}")
            print("="*60)
            return True
        else:
            print("\n" + "="*60)
            print("✗ ATTENDANCE FAILED")
            print("-"*60)
            print(f"Error: {data.get('error', 'Unknown error')}")
            print("="*60)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Connection Error: {e}")
        return False

# Main scanning loop
while True:
    try:
        # Check for card
        uid = pn532.read_passive_target(timeout=0.5)
        
        if uid is not None:
            card_id = convert_uid_to_string(uid)
            current_time = time.time()
            
            # Check cooldown
            if card_id == last_uid and (current_time - last_scan_time) < SCAN_COOLDOWN:
                continue
            
            # Update last scan
            last_uid = card_id
            last_scan_time = current_time
            
            # Mark attendance
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Card detected: {card_id}")
            mark_attendance(card_id)
            
        time.sleep(0.1)
        
    except KeyboardInterrupt:
        print("\n\nScanner stopped by user")
        break
    except Exception as e:
        print(f"\n✗ Error: {e}")
        time.sleep(1)
