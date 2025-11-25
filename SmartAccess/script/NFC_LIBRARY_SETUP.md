# NFC Scanner Setup for Library Book Issuing

## Overview
This script runs on Raspberry Pi to scan student NFC cards and send the data to the Django server for the teacher book issuing page.

## Hardware Requirements
- Raspberry Pi (any model with GPIO)
- MFRC522 NFC/RFID Reader
- LEDs (Green and Red)
- Buzzer
- Resistors (220Ω for LEDs, 100Ω for buzzer)
- Breadboard and jumper wires

## Wiring Diagram

### MFRC522 to Raspberry Pi
```
MFRC522 Pin  ->  Raspberry Pi Pin
SDA          ->  GPIO 8 (Pin 24)
SCK          ->  GPIO 11 (Pin 23)
MOSI         ->  GPIO 10 (Pin 19)
MISO         ->  GPIO 9 (Pin 21)
IRQ          ->  (Not connected)
GND          ->  Ground (Pin 6)
RST          ->  GPIO 25 (Pin 22)
3.3V         ->  3.3V (Pin 1)
```

### LEDs and Buzzer
```
Component       ->  Raspberry Pi Pin
Green LED (+)   ->  GPIO 17 (Pin 11) + 220Ω resistor
Red LED (+)     ->  GPIO 27 (Pin 13) + 220Ω resistor
Buzzer (+)      ->  GPIO 22 (Pin 15) + 100Ω resistor
All GND (-)     ->  Ground (Pin 14)
```

## Software Installation

### 1. Install Required Packages
```bash
sudo apt-get update
sudo apt-get install python3-dev python3-pip -y
pip3 install mfrc522 requests RPi.GPIO
```

### 2. Enable SPI Interface
```bash
sudo raspi-config
# Navigate to: Interface Options -> SPI -> Enable
# Reboot if prompted
```

### 3. Setup Script
```bash
# Copy the script to Raspberry Pi
scp script/nfc_scanner_library_issue.py pi@raspberrypi.local:~/

# Make it executable
chmod +x ~/nfc_scanner_library_issue.py

# Edit the SERVER_URL in the script
nano ~/nfc_scanner_library_issue.py
# Change: SERVER_URL = "http://192.168.1.100:8000"
# To your actual server IP address
```

## Usage

### Run Manually
```bash
cd ~
python3 nfc_scanner_library_issue.py
```

### Run as Service (Auto-start on boot)
Create a systemd service:

```bash
sudo nano /etc/systemd/system/nfc-library-scanner.service
```

Add the following content:
```ini
[Unit]
Description=NFC Scanner for Library Book Issuing
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/nfc_scanner_library_issue.py
WorkingDirectory=/home/pi
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable nfc-library-scanner.service
sudo systemctl start nfc-library-scanner.service
```

Check status:
```bash
sudo systemctl status nfc-library-scanner.service
```

View logs:
```bash
sudo journalctl -u nfc-library-scanner.service -f
```

## How It Works

1. **NFC Scanning**: The script continuously listens for NFC cards
2. **Data Transmission**: When a card is detected, it sends the NFC UID to the server
3. **Visual Feedback**:
   - **Green LED + 1 beep**: Card scanned and sent successfully
   - **Red LED + 3 beeps**: Error (connection failed, card not recognized, etc.)
4. **Cooldown**: 3-second cooldown prevents duplicate scans of the same card

## Integration with Django

The script sends POST requests to: `/library/api/receive-nfc-scan/`

The teacher's browser polls: `/library/api/get-nfc-scan/` every second

When a card is scanned:
1. Raspberry Pi sends NFC UID to server
2. Server stores it temporarily
3. Teacher's browser retrieves it via polling
4. Student information auto-fills on the page

## Troubleshooting

### Card not detected
- Check SPI is enabled: `lsmod | grep spi`
- Verify wiring connections
- Test with: `python3 -c "from mfrc522 import SimpleMFRC522; reader = SimpleMFRC522(); print('Place card...'); print(reader.read())"`

### Connection errors
- Verify SERVER_URL is correct
- Check network connectivity: `ping <server_ip>`
- Ensure server is running: `curl http://<server_ip>:8000/`
- Check firewall: `sudo ufw status`

### Permission errors
- Run with sudo: `sudo python3 nfc_scanner_library_issue.py`
- Or add user to spi and gpio groups:
  ```bash
  sudo usermod -a -G spi,gpio pi
  sudo reboot
  ```

### LED/Buzzer not working
- Check GPIO pin numbers match in script
- Verify correct resistor values
- Test GPIO: `gpio readall`

## Configuration

Edit `nfc_scanner_library_issue.py` to change:

```python
# Server configuration
SERVER_URL = "http://192.168.1.100:8000"  # Your server IP

# GPIO pins
LED_GREEN = 17  # Green LED pin
LED_RED = 27    # Red LED pin
BUZZER = 22     # Buzzer pin

# Timing
SCAN_COOLDOWN = 3  # Seconds between same card scans
```

## Security Note

For production, consider:
- Using HTTPS instead of HTTP
- Adding authentication token to API requests
- Implementing rate limiting on server
- Using VPN or secure network for Raspberry Pi

## Support

For issues or questions:
- Check Django server logs: `python manage.py runserver`
- Check Raspberry Pi logs: `sudo journalctl -u nfc-library-scanner.service`
- Verify network connectivity between Pi and server
