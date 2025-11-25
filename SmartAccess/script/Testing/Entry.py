#!/usr/bin/env python3
"""
NFC Scanner for SmartAccess System
Raspberry Pi 5 + PN532 NFC Reader
Communicates with Django backend via HTTP API
"""

import time
import board
import busio
import requests
import json
from digitalio import DigitalInOut
from adafruit_pn532.i2c import PN532_I2C
from adafruit_pn532.adafruit_pn532 import MIFARE_CMD_AUTH_A

# Configuration
DJANGO_SERVER = "http://172.20.10.4:8001"  # Replace with your Django server IP
API_ENDPOINT = f"{DJANGO_SERVER}/attendance/api/nfc-scan/"
SCAN_COOLDOWN = 1  # seconds between scans of same card

# Create I2C connection
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    pn532 = PN532_I2C(i2c, debug=False)
    
    # Configure PN532 to communicate with MiFare cards
    pn532.SAM_configuration()
    print("✅ NFC Reader initialized successfully!")
    print(f"🔗 Connected to Django server: {DJANGO_SERVER}")
    print("📱 Place your NFC card near the reader...")
    
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
    """Send NFC scan data to Django API"""
    try:
        payload = {
            'card_id': uid_hex
        }
        
        print(f"📡 Sending to Django: {payload}")
        
        response = requests.post(
            API_ENDPOINT, 
            json=payload, 
            timeout=15,  # Increased timeout for email sending
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ {data.get('message')}")
                print(f"👤 Student: {data.get('student_name')} ({data.get('roll_number')})")
                print(f"📊 Status: {data.get('status').upper()}")
                return True
            else:
                print(f"❌ Error: {data.get('error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Cannot reach Django server")
        return False
    except requests.exceptions.Timeout:
        print("❌ Timeout: Django server not responding")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    global last_uid, last_time
    
    while True:
        try:
            # Check if a card is available
            uid = pn532.read_passive_target(timeout=0.5)

            if uid is not None:
                # Prevent multiple reads in short time
                if uid == last_uid and (time.time() - last_time) < SCAN_COOLDOWN:
                    continue

                print("\n" + "="*50)
                print(f"🔍 Card detected! UID: {[hex(i) for i in uid]}")
                
                # Convert UID to string format
                uid_hex = convert_uid_to_string(uid)
                print(f"📇 UID (hex): {uid_hex}")

                # Try to authenticate and read block (optional - for debugging)
                if pn532.mifare_classic_authenticate_block(uid, 4, MIFARE_CMD_AUTH_A, key_a):
                    print("🔓 Authentication successful!")
                    try:
                        data = pn532.mifare_classic_read_block(4)
                        print(f"📄 Block 4 Data: {data}")
                    except Exception as e:
                        print(f"⚠️  Could not read block data: {e}")
                else:
                    print("ℹ️  Authentication not required (using UID for attendance)")

                # Send to Django
                success = send_to_django(uid_hex)
                
                if success:
                    print("🎉 Scan processed successfully!")
                else:
                    print("⚠️  Scan failed - check server connection")

                last_uid = uid
                last_time = time.time()
                print("="*50)
                
                # Delay after successful scan
                time.sleep(SCAN_COOLDOWN)
                
        except KeyboardInterrupt:
            print("\n👋 Shutting down NFC scanner...")
            break
        except Exception as e:
            print(f"❌ Unexpected error in main loop: {e}")
            #time.sleep(1)

if __name__ == "__main__":
    print("🚀 Starting SmartAccess NFC Scanner...")
    print("📡 Press Ctrl+C to stop")
    main()
