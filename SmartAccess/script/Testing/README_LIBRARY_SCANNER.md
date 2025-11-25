# Library Book Issuing NFC Scanner

## Script: `nfc_library_issue.py`

### Purpose
Scans student NFC cards and sends the data directly to Django for the teacher book issuing page.

### How It Works
1. Raspberry Pi continuously scans for NFC cards
2. When student places card on reader:
   - Card UID is read
   - Sent to Django API: `/library/api/scan-card-for-issue/`
   - Django looks up student by NFC UID
   - Returns student info (name, roll number, active borrows)
3. Teacher's browser displays student information automatically
4. Teacher can then select book to issue

### Setup

#### 1. Update Django Server IP
Edit line 18 in `nfc_library_issue.py`:
```python
DJANGO_SERVER = "http://172.20.10.4:8001"  # Change to your Django server IP
```

#### 2. Run on Raspberry Pi
```bash
cd /home/pi/SmartAccess/script/Testing
python3 nfc_library_issue.py
```

### Output Example
```
============================================================
📚 Library Book Issuing NFC Scanner
============================================================
✅ NFC Reader initialized successfully!
🔗 Connected to Django server: http://172.20.10.4:8001
📡 API Endpoint: http://172.20.10.4:8001/library/api/scan-card-for-issue/
📱 Place student NFC card near the reader...
⌨️  Press Ctrl+C to exit
============================================================

🔍 Card Detected!
   UID: 2ae44685
   Raw: ['0x2a', '0xe4', '0x46', '0x85']
   🔓 Card authenticated

📡 Sending card scan to Django: 2ae44685
⏰ Time: 2025-11-24 14:30:45
✅ Student Found!
👤 Name: Shahzaib Akhtar
🎓 Roll Number: SP22-BCS-197
📚 Active Borrows: 1/10
🔖 NFC UID: 2ae44685
✨ Student info sent to teacher's screen!
------------------------------------------------------------
⏳ Waiting for next scan...
```

### Features
- ✅ Direct communication with Django (no polling)
- ✅ Automatic cooldown (3 seconds between same card scans)
- ✅ Detailed student information display
- ✅ Shows active borrows and limit
- ✅ Error handling for network issues
- ✅ Clean console output with timestamps

### Troubleshooting

**Card not detected:**
- Check NFC reader connection
- Verify card is MIFARE compatible
- Try different card placement

**Connection error:**
- Verify Django server IP address
- Check Django is running: `python manage.py runserver 0.0.0.0:8001`
- Test network: `ping 172.20.10.4`

**Student not found:**
- Verify student has NFC UID assigned in database
- Check NFC UID matches in database
- Run in Django: `Student.objects.filter(nfc_uid='2ae44685')`

### Stop Scanner
Press `Ctrl+C` to stop the scanner gracefully.

### Comparison with Other Scanners

| Scanner | Purpose | Endpoint |
|---------|---------|----------|
| `Entry.py` | Attendance tracking | `/attendance/api/nfc-scan/` |
| `nfc_scanner_fine.py` | Fine management | `/fines/scan-card-for-fine/` |
| `nfc_library_issue.py` | Book issuing | `/library/api/scan-card-for-issue/` |
| `scan_card.py` | Card assignment | `/students/scan-for-assignment/` |

All scripts use the same hardware, just different API endpoints! 🎉
