#!/usr/bin/env python3
"""
NFC Card Assignment Scanner for SmartAccess System
Raspberry Pi 5 + PN532 NFC Reader
Handles ONLY card assignment requests from Django
"""

import time
import board
import busio
import threading
from datetime import datetime
from flask import Flask, request, jsonify
from adafruit_pn532.i2c import PN532_I2C
from adafruit_pn532.adafruit_pn532 import MIFARE_CMD_AUTH_A

# Configuration
ASSIGNMENT_TIMEOUT = 30  # seconds to wait for card during assignment

# Global variables
assignment_mode = False
assignment_data = {}
assignment_result = {}

# Flask app for handling assignment requests
app = Flask(__name__)

# Initialize NFC Reader
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    pn532 = PN532_I2C(i2c, debug=False)
    pn532.SAM_configuration()
    print("✅ NFC Card Assignment Scanner initialized!")
    
except Exception as e:
    print(f"❌ Error initializing NFC reader: {e}")
    exit(1)

# Default key for MIFARE cards
key_a = b'\xFF\xFF\xFF\xFF\xFF\xFF'

def convert_uid_to_string(uid):
    """Convert UID bytes to hex string format"""
    return ''.join([f'{i:02x}' for i in uid])

def card_assignment_scanner():
    """Scan for cards during assignment mode only"""
    global assignment_mode, assignment_data, assignment_result
    
    print("🆔 Card Assignment Scanner ready...")
    
    while True:
        try:
            if assignment_mode:
                # Only scan when in assignment mode
                uid = pn532.read_passive_target(timeout=0.5)
                
                if uid is not None:
                    uid_hex = convert_uid_to_string(uid)
                    
                    print(f"🔍 Card detected for assignment: {uid_hex}")
                    print(f"� Raw UID: {[hex(i) for i in uid]}")
                    
                    # Try to authenticate (optional - for verification)
                    if pn532.mifare_classic_authenticate_block(uid, 4, MIFARE_CMD_AUTH_A, key_a):
                        print("🔓 Card authentication successful!")
                    else:
                        print("🔒 Using card without authentication")
                    
                    # Store result
                    assignment_result['success'] = True
                    assignment_result['card_id'] = uid_hex
                    assignment_result['timestamp'] = datetime.now().isoformat()
                    assignment_result['raw_uid'] = [hex(i) for i in uid]
                    
                    # Exit assignment mode
                    assignment_mode = False
                    print(f"✅ Card {uid_hex} ready for assignment to student {assignment_data.get('roll_number')}")
                    
                    # Brief delay before continuing
                    time.sleep(1)
            else:
                # When not in assignment mode, just wait
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n👋 Shutting down Card Assignment Scanner...")
            break
        except Exception as e:
            print(f"❌ Scanner error: {e}")
            time.sleep(1)

@app.route('/scan-for-assignment', methods=['POST'])
def scan_for_assignment():
    """Handle card assignment requests from Django"""
    global assignment_mode, assignment_data, assignment_result
    
    try:
        data = request.json
        roll_number = data.get('roll_number')
        action = data.get('action')
        
        if not roll_number or action != 'assign_card':
            return jsonify({'success': False, 'error': 'Invalid request data'})
        
        print(f"\n🎯 Card assignment requested for student: {roll_number}")
        print(f"⏰ Waiting {ASSIGNMENT_TIMEOUT} seconds for card placement...")
        
        # Reset assignment result
        assignment_result = {}
        assignment_data = data
        assignment_mode = True
        
        # Wait for card scan with timeout
        timeout_time = time.time() + ASSIGNMENT_TIMEOUT
        
        while time.time() < timeout_time:
            if assignment_result.get('success'):
                print(f"✅ Card assignment completed: {assignment_result['card_id']}")
                return jsonify(assignment_result)
            time.sleep(0.1)
        
        # Timeout occurred
        assignment_mode = False
        print(f"⏰ Assignment timeout for student {roll_number}")
        print("❌ No card detected within 30 seconds")
        
        return jsonify({
            'success': False, 
            'error': f'No card detected within {ASSIGNMENT_TIMEOUT} seconds'
        })
        
    except Exception as e:
        assignment_mode = False
        print(f"❌ Assignment error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/status', methods=['GET'])
def get_status():
    """Get scanner status"""
    return jsonify({
        'status': 'online',
        'scanner_type': 'card_assignment_only',
        'assignment_mode': assignment_mode,
        'current_student': assignment_data.get('roll_number') if assignment_mode else None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/test', methods=['GET'])
def test_connection():
    """Test endpoint to verify Pi is reachable"""
    return jsonify({
        'message': 'NFC Card Assignment Scanner is online',
        'status': 'ready',
        'timestamp': datetime.now().isoformat()
    })

def run_flask_server():
    """Run Flask server in a separate thread"""
    print("🌐 Starting Card Assignment Flask server on port 5000...")
    print("📡 Endpoints available:")
    print("   POST /scan-for-assignment - Handle card assignment")
    print("   GET /status - Check scanner status") 
    print("   GET /test - Test connection")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    print("🚀 Starting SmartAccess Card Assignment Scanner...")
    print("🆔 Purpose: Scan NFC cards for student assignment only")
    print("📡 Flask server will start on: http://0.0.0.0:5000")
    print("� Press Ctrl+C to stop")
    print("-" * 60)
    
    # Start Flask server in background thread
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    
    # Wait a moment for Flask to start
    time.sleep(2)
    
    # Start card assignment scanner loop
    try:
        card_assignment_scanner()
    except KeyboardInterrupt:
        print("\n👋 Card Assignment Scanner stopped!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
