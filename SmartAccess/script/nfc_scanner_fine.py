#!/usr/bin/env python3
"""
NFC Scanner for Fine Management System
Raspberry Pi Flask Server - Dedicated for scanning student cards when adding fines
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for Django frontend

# Initialize NFC Reader
reader = SimpleMFRC522()

# LED/Buzzer GPIO Pins (optional for feedback)
LED_GREEN = 17  # Success indicator
LED_RED = 27    # Error indicator
BUZZER = 22     # Audio feedback

# Setup GPIO (optional)
try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_GREEN, GPIO.OUT)
    GPIO.setup(LED_RED, GPIO.OUT)
    GPIO.setup(BUZZER, GPIO.OUT)
    GPIO.output(LED_GREEN, GPIO.LOW)
    GPIO.output(LED_RED, GPIO.LOW)
    GPIO.output(BUZZER, GPIO.LOW)
    print("✓ GPIO initialized for LED/Buzzer feedback")
except Exception as e:
    print(f"⚠ GPIO initialization failed (running without LED/Buzzer): {e}")

def beep(duration=0.1):
    """Short beep sound"""
    try:
        GPIO.output(BUZZER, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(BUZZER, GPIO.LOW)
    except:
        pass

def led_success():
    """Green LED flash for success"""
    try:
        GPIO.output(LED_GREEN, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(LED_GREEN, GPIO.LOW)
    except:
        pass

def led_error():
    """Red LED flash for error"""
    try:
        GPIO.output(LED_RED, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(LED_RED, GPIO.LOW)
    except:
        pass


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
        print(f"🎯 Scan Request Received: {action}")
        print(f"{'='*50}")
        print("📢 Please place student's NFC card on the scanner...")
        print("⏱️  Timeout: 30 seconds")
        
        # Single beep to indicate ready
        beep(0.1)
        
        # Wait for card scan with timeout
        timeout = 30  # 30 seconds
        start_time = time.time()
        card_id = None
        
        while (time.time() - start_time) < timeout:
            try:
                # Try to read card (non-blocking with short timeout)
                print(".", end="", flush=True)
                id, text = reader.read_no_block()
                
                if id:
                    card_id = str(id)
                    print(f"\n✓ Card Detected!")
                    print(f"📇 Card ID: {card_id}")
                    
                    # Success feedback
                    beep(0.1)
                    time.sleep(0.1)
                    beep(0.1)
                    led_success()
                    
                    return jsonify({
                        'success': True,
                        'card_id': card_id,
                        'message': 'Card scanned successfully',
                        'timestamp': time.time()
                    })
                
                time.sleep(0.5)  # Check every 0.5 seconds
                
            except Exception as read_error:
                # Ignore read errors and keep trying
                time.sleep(0.5)
                continue
        
        # Timeout reached
        print(f"\n✗ Timeout: No card detected within {timeout} seconds")
        led_error()
        beep(0.3)
        
        return jsonify({
            'success': False,
            'error': f'No card detected within {timeout} seconds. Please try again.',
            'timeout': True
        }), 408  # 408 Request Timeout
        
    except Exception as e:
        print(f"\n✗ Error during scan: {str(e)}")
        led_error()
        beep(0.5)
        
        return jsonify({
            'success': False,
            'error': f'Scanner error: {str(e)}'
        }), 500


@app.route('/test-scan', methods=['GET'])
def test_scan():
    """
    Manual test endpoint to scan a card
    Access via browser: http://PI_IP:5000/test-scan
    """
    try:
        print("\n" + "="*50)
        print("🧪 TEST MODE - Manual Card Scan")
        print("="*50)
        print("📢 Place card on scanner (10 second timeout)...")
        
        beep(0.1)
        
        timeout = 10
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            try:
                id, text = reader.read_no_block()
                
                if id:
                    card_id = str(id)
                    print(f"\n✓ Card Read Successfully!")
                    print(f"📇 Card ID: {card_id}")
                    print(f"📄 Text: {text}")
                    
                    beep(0.1)
                    time.sleep(0.1)
                    beep(0.1)
                    led_success()
                    
                    return jsonify({
                        'success': True,
                        'card_id': card_id,
                        'card_text': text,
                        'message': 'Test scan successful'
                    })
                
                time.sleep(0.3)
                
            except:
                time.sleep(0.3)
                continue
        
        print("\n✗ Timeout: No card detected")
        led_error()
        
        return jsonify({
            'success': False,
            'error': 'No card detected within 10 seconds'
        }), 408
        
    except Exception as e:
        print(f"\n✗ Test scan error: {str(e)}")
        led_error()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Safely shutdown the scanner service"""
    try:
        print("\n🛑 Shutdown request received")
        GPIO.cleanup()
        print("✓ GPIO cleaned up")
        
        return jsonify({
            'success': True,
            'message': 'Scanner service shutting down'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


if __name__ == '__main__':
    try:
        print("\n" + "="*60)
        print("🚀 NFC Scanner for Fine Management System")
        print("="*60)
        print("📡 Starting Flask server...")
        print("🌐 Accessible at: http://<PI_IP>:5000")
        print("⚙️  Endpoints:")
        print("   - GET  /status           - Check scanner status")
        print("   - POST /scan-for-student - Scan card for fine")
        print("   - GET  /test-scan        - Manual test scan")
        print("   - POST /shutdown         - Shutdown service")
        print("="*60)
        print("✓ Scanner ready! Waiting for requests...\n")
        
        # Run Flask server
        # Use 0.0.0.0 to make it accessible from other devices on network
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Keyboard interrupt detected")
        print("🧹 Cleaning up GPIO...")
        GPIO.cleanup()
        print("✓ Shutdown complete")
        
    except Exception as e:
        print(f"\n✗ Fatal error: {str(e)}")
        GPIO.cleanup()
