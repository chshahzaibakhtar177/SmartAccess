#!/usr/bin/env python3
"""
NFC Scanner for Library Book Issuing - SmartAccess System
Raspberry Pi 5 + PN532 NFC Reader
Sends student card scans directly to Django for book issuing
"""

import time
import board
import busio
import requests
import json
from datetime import datetime
from adafruit_pn532.i2c import PN532_I2C
from adafruit_pn532.adafruit_pn532 import MIFARE_CMD_AUTH_A

# Configuration
DJANGO_SERVER = "http://172.20.10.4:8001"  # Django server IP (same as Entry.py)
API_ENDPOINT = f"{DJANGO_SERVER}/library/api/scan-card-for-issue/"
SCAN_COOLDOWN = 3  # seconds between scans of same card

# Create I2C connection
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    pn532 = PN532_I2C(i2c, debug=False)
    
    # Configure PN532 to communicate with MiFare cards
    pn532.SAM_configuration()
    print("=" * 60)
    print("📚 Library Book Issuing NFC Scanner")
    print("=" * 60)
    print("✅ NFC Reader initialized successfully!")
    print(f"🔗 Connected to Django server: {DJANGO_SERVER}")
    print(f"📡 API Endpoint: {API_ENDPOINT}")
    print("📱 Place student NFC card near the reader...")
    print("⌨️  Press Ctrl+C to exit")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Error initializing NFC reader: {e}")
    exit(1)

# Default key for MIFARE cards
key_a = b'\xFF\xFF\xFF\xFF\xFF\xFF'

last_uid = None
last_time = 0

def convert_uid_to_string(uid):
    """Convert UID bytes to hex string format"""
    return ''.join([f'{i:02x}' for i in uid])

def send_to_django(uid_hex):
    """Send NFC scan data to Django API for book issuing"""
    try:
        payload = {
            'card_id': uid_hex
        }
        
        print(f"\n📡 Sending card scan to Django: {uid_hex}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        response = requests.post(
            API_ENDPOINT, 
            json=payload, 
            timeout=5,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Student Found!")
                print(f"👤 Name: {data.get('student_name')}")
                print(f"🎓 Roll Number: {data.get('roll_number')}")
                print(f"📚 Active Borrows: {data.get('active_borrows')}/{data.get('borrowing_limit')}")
                print(f"🔖 NFC UID: {data.get('nfc_uid')}")
                print("✨ Student info sent to teacher's screen!")
                print("-" * 60)
                return True
            else:
                error = data.get('error', 'Unknown error')
                print(f"❌ Error: {error}")
                print("-" * 60)
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            print("-" * 60)
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Cannot reach Django server")
        print(f"   Make sure Django is running at {DJANGO_SERVER}")
        print("-" * 60)
        return False
    except requests.exceptions.Timeout:
        print("❌ Request Timeout: Django server not responding")
        print("-" * 60)
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        print("-" * 60)
        return False

def main():
    """Main scanning loop"""
    global last_uid, last_time
    
    while True:
        try:
            # Read NFC card
            uid = pn532.read_passive_target(timeout=0.5)
            
            if uid is not None:
                uid_hex = convert_uid_to_string(uid)
                current_time = time.time()
                
                # Check if this is a duplicate scan (same card within cooldown period)
                if uid_hex == last_uid and (current_time - last_time) < SCAN_COOLDOWN:
                    time.sleep(0.5)
                    continue
                
                # New card or cooldown expired
                print(f"\n🔍 Card Detected!")
                print(f"   UID: {uid_hex}")
                print(f"   Raw: {[hex(i) for i in uid]}")
                
                # Try to authenticate (optional)
                if pn532.mifare_classic_authenticate_block(uid, 4, MIFARE_CMD_AUTH_A, key_a):
                    print("   🔓 Card authenticated")
                else:
                    print("   🔒 Card read without authentication")
                
                # Send to Django
                if send_to_django(uid_hex):
                    last_uid = uid_hex
                    last_time = current_time
                    print("⏳ Waiting for next scan...")
                else:
                    print("⚠️  Scan failed. You can try again.")
                    last_uid = None  # Allow immediate retry on failure
                    
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down Library NFC Scanner...")
            print("Goodbye!")
            break
            
        except Exception as e:
            print(f"❌ Scanner Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Fatal Error: {e}")
        print("Scanner stopped!")
