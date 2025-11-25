#!/usr/bin/env python3
"""
NFC Scanner Script for Library Book Issuing
Scans student NFC cards and sends data to the server for teacher book issuing
"""

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import requests
import time
import json
from datetime import datetime

# Configuration
SERVER_URL = "http://192.168.1.100:8000"  # Replace with your server IP
API_ENDPOINT = f"{SERVER_URL}/library/api/receive-nfc-scan/"

# LED and Buzzer Configuration
LED_GREEN = 17  # Success LED
LED_RED = 27    # Error LED
BUZZER = 22     # Buzzer pin

# Initialize
reader = SimpleMFRC522()
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Setup GPIO pins
GPIO.setup(LED_GREEN, GPIO.OUT)
GPIO.setup(LED_RED, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)

# Turn off all indicators initially
GPIO.output(LED_GREEN, GPIO.LOW)
GPIO.output(LED_RED, GPIO.LOW)
GPIO.output(BUZZER, GPIO.LOW)


def beep(duration=0.1, times=1):
    """Make a beep sound"""
    for _ in range(times):
        GPIO.output(BUZZER, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(BUZZER, GPIO.LOW)
        if times > 1:
            time.sleep(0.1)


def led_success():
    """Show success LED"""
    GPIO.output(LED_GREEN, GPIO.HIGH)
    GPIO.output(LED_RED, GPIO.LOW)
    beep(0.1, 1)
    time.sleep(1)
    GPIO.output(LED_GREEN, GPIO.LOW)


def led_error():
    """Show error LED"""
    GPIO.output(LED_RED, GPIO.HIGH)
    GPIO.output(LED_GREEN, GPIO.LOW)
    beep(0.1, 3)
    time.sleep(1)
    GPIO.output(LED_RED, GPIO.LOW)


def send_nfc_data(nfc_uid):
    """Send NFC UID to the server"""
    try:
        payload = {
            'nfc_uid': nfc_uid,
            'timestamp': datetime.now().isoformat(),
            'scanner_location': 'Library Desk'
        }
        
        print(f"Sending NFC data to server: {nfc_uid}")
        
        response = requests.post(
            API_ENDPOINT,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✓ NFC scan sent successfully: {nfc_uid}")
                led_success()
                return True
            else:
                print(f"✗ Server error: {data.get('error', 'Unknown error')}")
                led_error()
                return False
        else:
            print(f"✗ HTTP Error: {response.status_code}")
            led_error()
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Connection error: Cannot reach server")
        led_error()
        return False
    except requests.exceptions.Timeout:
        print("✗ Request timeout")
        led_error()
        return False
    except Exception as e:
        print(f"✗ Error sending data: {e}")
        led_error()
        return False


def main():
    """Main scanning loop"""
    print("=" * 50)
    print("NFC Scanner for Library Book Issuing")
    print("=" * 50)
    print(f"Server: {SERVER_URL}")
    print("Place student NFC card near reader...")
    print("Press Ctrl+C to exit")
    print("=" * 50)
    
    last_scan_uid = None
    last_scan_time = 0
    SCAN_COOLDOWN = 3  # Seconds between same card scans
    
    try:
        while True:
            try:
                # Read NFC card
                uid, text = reader.read()
                nfc_uid = str(uid)
                current_time = time.time()
                
                # Prevent duplicate scans of same card within cooldown period
                if nfc_uid == last_scan_uid and (current_time - last_scan_time) < SCAN_COOLDOWN:
                    time.sleep(0.5)
                    continue
                
                # New card detected
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Card detected!")
                print(f"NFC UID: {nfc_uid}")
                
                # Send to server
                if send_nfc_data(nfc_uid):
                    last_scan_uid = nfc_uid
                    last_scan_time = current_time
                    print("Waiting for next card...")
                else:
                    print("Failed to send data. Please try again.")
                
            except Exception as e:
                print(f"Error reading card: {e}")
                led_error()
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\nShutting down NFC scanner...")
    
    finally:
        # Cleanup
        GPIO.output(LED_GREEN, GPIO.LOW)
        GPIO.output(LED_RED, GPIO.LOW)
        GPIO.output(BUZZER, GPIO.LOW)
        GPIO.cleanup()
        print("NFC scanner stopped.")


if __name__ == "__main__":
    main()
