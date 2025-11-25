#!/usr/bin/env python3
"""
NFC Scanner for Fine Management System
Raspberry Pi Flask Server - Dedicated for scanning student cards when adding fines
Uses PN532 NFC Reader (I2C) - Same as scan_card.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import board
import busio
from adafruit_pn532.i2c import PN532_I2C
from adafruit_pn532.adafruit_pn532 import MIFARE_CMD_AUTH_A

app = Flask(__name__)
CORS(app)  # Enable CORS for Django frontend

# Initialize PN532 NFC Reader (I2C)
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    pn532 = PN532_I2C(i2c, debug=False)
    pn532.SAM_configuration()
    print("✅ PN532 NFC Reader initialized successfully!")
except Exception as e:
    print(f"❌ Error initializing PN532 NFC reader: {e}")
    exit(1)

# Default key for MIFARE cards
key_a = b'\xFF\xFF\xFF\xFF\xFF\xFF'

def convert_uid_to_string(uid):
    """Convert UID bytes to hex string format"""
    return ''.join([f'{i:02x}' for i in uid])


@app.route('/status', methods=['GET'])
def status():
    """Check if the scanner is online and ready"""
    return jsonify({
        'success': True,
        'status': 'online',
        'service': 'NFC Scanner for Fine Management',
        'message': 'Scanner is ready to scan student cards'
    })


@app.route('/scan-for-student', methods=['POST'])
def scan_for_student():
    """
    Scan NFC card to get student information for adding a fine
    Used when teacher clicks "Scan Card" button in fine management
    
    Request from Django frontend:
    POST /scan-for-student
    {
        "action": "scan_for_fine"
    }
    
    Response:
    {
        "success": true,
        "card_id": "123456789",
        "message": "Card scanned successfully"
    }
    """
    try:
        data = request.get_json() or {}
        action = data.get('action', 'scan_for_fine')
        
        print(f"\n{'='*50}")
        print(f"💰 Fine Scan Request: {action}")
        print(f"{'='*50}")
        print("📢 Please place student's NFC card on the scanner...")
        print("⏱️  Timeout: 30 seconds")
        
        # Wait for card scan with timeout using PN532
        timeout = 30  # 30 seconds
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            # Read card with 0.5 second timeout per attempt
            uid = pn532.read_passive_target(timeout=0.5)
            
            if uid is not None:
                card_id = convert_uid_to_string(uid)
                print("\n✅ Card Detected!")
                print(f"📇 Card ID: {card_id}")
                print(f"🔖 Raw UID: {[hex(i) for i in uid]}")
                
                # Try to authenticate (optional - for verification)
                if pn532.mifare_classic_authenticate_block(uid, 4, MIFARE_CMD_AUTH_A, key_a):
                    print("🔓 Card authentication successful!")
                else:
                    print("🔒 Using card without authentication")
                
                return jsonify({
                    'success': True,
                    'card_id': card_id,
                    'message': 'Card scanned successfully',
                    'timestamp': time.time()
                })
        
        # Timeout reached
        print(f"\n⏰ Timeout: No card detected within {timeout} seconds")
        
        return jsonify({
            'success': False,
            'error': f'No card detected within {timeout} seconds. Please try again.',
            'timeout': True
        }), 408  # 408 Request Timeout
        
    except Exception as e:
        print(f"\n❌ Error during scan: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': f'Scanner error: {str(e)}'
        }), 500


@app.route('/test', methods=['GET'])
def test():
    """Test endpoint to verify connectivity"""
    return jsonify({
        'success': True,
        'message': 'Fine Management NFC Scanner is online and ready',
        'service': 'Fine Management Scanner (PN532)',
        'timestamp': time.time()
    })


if __name__ == '__main__':
    try:
        print("=" * 60)
        print("💰 Fine Management NFC Scanner Server (PN532)")
        print("=" * 60)
        print("✅ PN532 NFC Reader initialized")
        print("🌐 Starting Flask server on http://0.0.0.0:5000")
        print("📡 Endpoints:")
        print("   POST /scan-for-student - Scan student card for adding fines")
        print("   GET /status - Check scanner status")
        print("   GET /test - Test connection")
        print("⌨️  Press Ctrl+C to stop")
        print("=" * 60)
        
        # Run Flask server
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down scanner...")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")

