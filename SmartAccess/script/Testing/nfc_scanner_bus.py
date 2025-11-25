#!/usr/bin/env python3
"""
NFC Scanner for Bus Transportation - Raspberry Pi
Tracks student boarding and alighting from buses using NFC cards
"""

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import requests
import time
import json
from datetime import datetime
import logging
from pathlib import Path

# ============ CONFIGURATION ============
API_BASE_URL = "http://172.20.10.4:8001"  # Django server IP (same as Entry.py)
API_ENDPOINT = "/api/transportation/scan/"
API_KEY = "your-secret-api-key"  # Add authentication if needed

# GPIO Configuration
BUZZER_PIN = 18
LED_GREEN = 23
LED_RED = 24
LED_BLUE = 25

# File paths
LOG_FILE = Path("/home/pi/bus_scanner/logs/scan_log.txt")
OFFLINE_QUEUE = Path("/home/pi/bus_scanner/offline_queue.json")

# Create directories
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
OFFLINE_QUEUE.parent.mkdir(parents=True, exist_ok=True)

# ============ LOGGING SETUP ============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============ GPIO SETUP ============
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Setup output pins
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(LED_GREEN, GPIO.OUT)
GPIO.setup(LED_RED, GPIO.OUT)
GPIO.setup(LED_BLUE, GPIO.OUT)

# Initialize all LEDs off
GPIO.output(LED_GREEN, GPIO.LOW)
GPIO.output(LED_RED, GPIO.LOW)
GPIO.output(LED_BLUE, GPIO.LOW)

# Initialize NFC Reader
reader = SimpleMFRC522()

# ============ HELPER FUNCTIONS ============

def beep(duration=0.1, times=1):
    """Sound buzzer"""
    for _ in range(times):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        if times > 1:
            time.sleep(0.1)

def led_on(color):
    """Turn on specific LED color"""
    GPIO.output(LED_GREEN, GPIO.LOW)
    GPIO.output(LED_RED, GPIO.LOW)
    GPIO.output(LED_BLUE, GPIO.LOW)
    
    if color == 'green':
        GPIO.output(LED_GREEN, GPIO.HIGH)
    elif color == 'red':
        GPIO.output(LED_RED, GPIO.HIGH)
    elif color == 'blue':
        GPIO.output(LED_BLUE, GPIO.HIGH)

def led_off():
    """Turn off all LEDs"""
    GPIO.output(LED_GREEN, GPIO.LOW)
    GPIO.output(LED_RED, GPIO.LOW)
    GPIO.output(LED_BLUE, GPIO.LOW)

def led_blink(color, times=3, duration=0.2):
    """Blink LED"""
    for _ in range(times):
        led_on(color)
        time.sleep(duration)
        led_off()
        time.sleep(duration)

def save_offline_scan(scan_data):
    """Save scan data when offline"""
    try:
        offline_scans = []
        if OFFLINE_QUEUE.exists():
            with open(OFFLINE_QUEUE, 'r') as f:
                offline_scans = json.load(f)
        
        scan_data['queued_at'] = datetime.now().isoformat()
        offline_scans.append(scan_data)
        
        with open(OFFLINE_QUEUE, 'w') as f:
            json.dump(offline_scans, f, indent=2)
        
        logger.info(f"Saved scan to offline queue. Total queued: {len(offline_scans)}")
        return True
    except Exception as e:
        logger.error(f"Error saving offline scan: {e}")
        return False

def sync_offline_scans():
    """Send queued offline scans to server"""
    if not OFFLINE_QUEUE.exists():
        return
    
    try:
        with open(OFFLINE_QUEUE, 'r') as f:
            offline_scans = json.load(f)
        
        if not offline_scans:
            return
        
        logger.info(f"Syncing {len(offline_scans)} offline scans...")
        synced_count = 0
        remaining_scans = []
        
        for scan_data in offline_scans:
            try:
                response = requests.post(
                    f"{API_BASE_URL}{API_ENDPOINT}",
                    json=scan_data,
                    timeout=15  # Increased timeout for email sending
                )
                
                if response.status_code == 200:
                    synced_count += 1
                    logger.info(f"Synced offline scan: {scan_data['nfc_uid']}")
                else:
                    remaining_scans.append(scan_data)
            except:
                remaining_scans.append(scan_data)
        
        # Update queue with failed syncs
        with open(OFFLINE_QUEUE, 'w') as f:
            json.dump(remaining_scans, f, indent=2)
        
        logger.info(f"Synced {synced_count} scans. {len(remaining_scans)} remaining.")
        
    except Exception as e:
        logger.error(f"Error syncing offline scans: {e}")

def send_scan_to_server(nfc_uid, action='board'):
    """Send scan data to server - backend determines bus from student assignment"""
    scan_data = {
        'nfc_uid': nfc_uid,
        'action': action,
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}{API_ENDPOINT}",
            json=scan_data,
            headers={'Authorization': f'Bearer {API_KEY}'},
            timeout=15  # Increased timeout for email sending
        )
        
        if response.status_code == 200:
            result = response.json()
            return True, result
        else:
            logger.warning(f"Server returned status {response.status_code}")
            save_offline_scan(scan_data)
            return False, {"message": "Saved offline - will sync later"}
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {e}")
        save_offline_scan(scan_data)
        return False, {"message": "No connection - saved offline"}

def display_result(success, message, student_name=None):
    """Display scan result with LEDs and buzzer"""
    if success:
        # Success feedback
        led_on('green')
        beep(0.1, 1)
        print(f"\n✓ SUCCESS: {student_name or 'Student'}")
        print(f"  {message}")
        time.sleep(2)
        led_off()
    else:
        # Error feedback
        led_on('red')
        beep(0.1, 3)
        print(f"\n✗ ERROR: {message}")
        time.sleep(2)
        led_off()

def determine_action(nfc_uid):
    """
    Determine if student is boarding or alighting
    This is a simple implementation - could be enhanced with state tracking
    """
    # For now, we'll track the last action in a local file
    state_file = Path("/home/pi/bus_scanner/student_states.json")
    
    try:
        if state_file.exists():
            with open(state_file, 'r') as f:
                states = json.load(f)
        else:
            states = {}
        
        # If student was onboard (boarded), they're now alighting
        # If student was not onboard, they're boarding
        if states.get(nfc_uid) == 'boarded':
            action = 'alight'
            states[nfc_uid] = 'alighted'
        else:
            action = 'board'
            states[nfc_uid] = 'boarded'
        
        with open(state_file, 'w') as f:
            json.dump(states, f)
        
        return action
        
    except Exception as e:
        logger.error(f"Error determining action: {e}")
        return 'board'  # Default to boarding

# ============ MAIN SCANNER LOOP ============

def main():
    """Main scanning loop"""
    logger.info("=" * 60)
    logger.info("Bus Transportation NFC Scanner Started")
    logger.info(f"Server: {API_BASE_URL}")
    logger.info("=" * 60)
    
    print("\n" + "=" * 60)
    print("🚌 BUS TRANSPORTATION SCANNER")
    print("=" * 60)
    print("Ready to scan NFC cards...")
    print("Hold card near reader to board/alight")
    print("Press Ctrl+C to exit\n")
    
    # Indicate system ready
    led_blink('blue', 2, 0.3)
    beep(0.05, 2)
    
    last_sync_time = time.time()
    SYNC_INTERVAL = 300  # Sync every 5 minutes
    
    last_scanned_uid = None
    last_scan_time = 0
    SCAN_COOLDOWN = 3  # Prevent duplicate scans within 3 seconds
    
    try:
        while True:
            try:
                # Sync offline scans periodically
                if time.time() - last_sync_time > SYNC_INTERVAL:
                    sync_offline_scans()
                    last_sync_time = time.time()
                
                # Show waiting status
                led_on('blue')
                
                # Read NFC card
                logger.info("Waiting for card scan...")
                id, text = reader.read()
                nfc_uid = str(id)
                
                led_off()
                
                # Prevent duplicate scans
                current_time = time.time()
                if nfc_uid == last_scanned_uid and (current_time - last_scan_time) < SCAN_COOLDOWN:
                    logger.info(f"Duplicate scan ignored: {nfc_uid}")
                    continue
                
                last_scanned_uid = nfc_uid
                last_scan_time = current_time
                
                logger.info(f"Card scanned - UID: {nfc_uid}")
                print(f"\n📱 Card Detected: {nfc_uid}")
                
                # Determine action (board or alight)
                action = determine_action(nfc_uid)
                action_text = "BOARDING" if action == 'board' else "ALIGHTING"
                print(f"   Action: {action_text}")
                
                # Send to server
                print("   Processing...")
                success, result = send_scan_to_server(nfc_uid, action)
                
                # Display result
                if success:
                    student_name = result.get('student_name', 'Student')
                    roll_number = result.get('roll_number', '')
                    bus_number = result.get('bus_number', '')
                    route_name = result.get('route_name', '')
                    
                    message = f"{action_text} recorded\\n  {student_name} ({roll_number})"
                    if bus_number:
                        message += f"\\n  Bus: {bus_number}"
                    if route_name:
                        message += f"\\n  Route: {route_name}"
                    
                    display_result(True, message, student_name)
                else:
                    error_msg = result.get('message', 'Scan failed')
                    display_result(False, error_msg)
                
                # Short delay before next scan
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in scan loop: {e}")
                led_on('red')
                beep(0.05, 2)
                time.sleep(1)
                led_off()
                
    except KeyboardInterrupt:
        print("\n\nShutting down scanner...")
        logger.info("Scanner shutdown requested")
        
        # Final sync attempt
        print("Syncing offline scans...")
        sync_offline_scans()
        
    finally:
        # Cleanup
        led_off()
        GPIO.cleanup()
        logger.info("Scanner stopped - GPIO cleaned up")
        print("Scanner stopped. Goodbye!")

# ============ RUN SCANNER ============

if __name__ == "__main__":
    main()
