# Raspberry Pi NFC Scanner Setup Guide

## Hardware Requirements
- Raspberry Pi (3/4/Zero)
- MFRC522 NFC Reader Module
- NFC Cards/Tags
- LED (Green & Red) + Resistors (220Ω)
- Buzzer (Active or Passive)
- Jumper Wires

## GPIO Pin Connections

### MFRC522 NFC Reader:
- SDA  → GPIO 8  (Pin 24)
- SCK  → GPIO 11 (Pin 23)
- MOSI → GPIO 10 (Pin 19)
- MISO → GPIO 9  (Pin 21)
- GND  → Ground
- RST  → GPIO 25 (Pin 22)
- 3.3V → 3.3V Power

### LEDs and Buzzer:
- Green LED → GPIO 17 (Pin 11) + Resistor → Ground
- Red LED   → GPIO 27 (Pin 13) + Resistor → Ground
- Buzzer    → GPIO 22 (Pin 15) → Ground

## Installation Steps

### 1. Enable SPI Interface
```bash
sudo raspi-config
# Navigate to: Interface Options → SPI → Enable
# Reboot: sudo reboot
```

### 2. Update System
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 3. Install Python Dependencies
```bash
# Install pip if not available
sudo apt-get install python3-pip -y

# Install system packages
sudo apt-get install python3-dev python3-rpi.gpio -y

# Install Python packages
cd /path/to/script/
pip3 install -r requirements_pi.txt
```

### 4. Test NFC Reader
```bash
# Test if SPI is enabled
lsmod | grep spi

# Should show: spi_bcm2835
```

## Running the Scripts

### For Fine Management:
```bash
# Navigate to script directory
cd /path/to/SmartAccess/script/

# Run the fine scanner
python3 nfc_scanner_fine.py

# Scanner will start on http://0.0.0.0:5000
```

### For Attendance (existing):
```bash
python3 enhanced_nfc_scanner_pi.py
```

## Auto-Start on Boot (Optional)

### Using systemd service:

1. Create service file:
```bash
sudo nano /etc/systemd/system/nfc-fine-scanner.service
```

2. Add content:
```ini
[Unit]
Description=NFC Scanner for Fine Management
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/SmartAccess/script
ExecStart=/usr/bin/python3 /home/pi/SmartAccess/script/nfc_scanner_fine.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable nfc-fine-scanner.service
sudo systemctl start nfc-fine-scanner.service
sudo systemctl status nfc-fine-scanner.service
```

## Accessing the Scanner

### From Django Server:
- Update `add_fine.html` with your Pi's IP:
```javascript
fetch('http://YOUR_PI_IP:5000/scan-for-student', ...)
```

### Testing Endpoints:
```bash
# Check status
curl http://localhost:5000/status

# Test manual scan
curl http://localhost:5000/test-scan

# Scan for fine
curl -X POST http://localhost:5000/scan-for-student
```

## Troubleshooting

### SPI Not Working:
```bash
# Check if SPI is enabled
ls -l /dev/spi*
# Should show: /dev/spidev0.0 and /dev/spidev0.1

# If not, enable in config
sudo nano /boot/config.txt
# Add: dtparam=spi=on
sudo reboot
```

### Permission Errors:
```bash
# Add user to GPIO group
sudo usermod -a -G gpio pi
sudo usermod -a -G spi pi

# Reboot
sudo reboot
```

### Can't Read Cards:
- Check wiring connections
- Verify 3.3V power (NOT 5V!)
- Test with simple read script
- Check card is MIFARE Classic/compatible

### Port Already in Use:
```bash
# Find process using port 5000
sudo lsof -i :5000

# Kill process
sudo kill -9 <PID>
```

## Different Scripts for Different Purposes

### nfc_scanner_fine.py:
- **Purpose**: Fine management only
- **Port**: 5000
- **Endpoint**: `/scan-for-student`
- **Use**: Teacher fining students by scanning cards

### enhanced_nfc_scanner_pi.py:
- **Purpose**: Attendance tracking
- **Port**: 5000
- **Endpoint**: `/nfc-scan`
- **Use**: Entry/exit logging

**Note**: Don't run both scripts simultaneously - they use the same port and NFC reader!

## Security Notes

1. **Change default credentials** if using authentication
2. **Use HTTPS** in production (nginx reverse proxy)
3. **Firewall rules** to restrict access
4. **Keep system updated**: `sudo apt-get update && sudo apt-get upgrade`

## Network Configuration

### Static IP (Recommended):
```bash
sudo nano /etc/dhcpcd.conf

# Add:
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

## LED/Buzzer Behavior

### Fine Scanner:
- **Green LED + 1 Beep**: Card read successfully
- **Red LED + 3 Beeps**: Error reading card
- **Red LED + 2 Beeps**: Timeout (no card scanned)

### Attendance Scanner:
- **Green LED + 1 Long Beep**: Entry logged
- **Green LED + 2 Short Beeps**: Exit logged
- **Red LED + 3 Beeps**: Error or unknown card

## Support

For issues:
1. Check `/var/log/syslog` for system errors
2. Review Flask console output
3. Test NFC reader with SimpleMFRC522 examples
4. Verify GPIO connections with multimeter
