import time
import board
import busio
from digitalio import DigitalInOut
from adafruit_pn532.i2c import PN532_I2C
from adafruit_pn532.adafruit_pn532 import MIFARE_CMD_AUTH_A

# Create I2C connection
i2c = busio.I2C(board.SCL, board.SDA)
pn532 = PN532_I2C(i2c, debug=False)

# Configure PN532 to communicate with MiFare cards
pn532.SAM_configuration()

print("Place your NFC card near the reader...")

# Default key for MIFARE cards
key_a = b'\xFF\xFF\xFF\xFF\xFF\xFF'

last_uid = None
last_time = 0

while True:
    # Check if a card is available
    uid = pn532.read_passive_target(timeout=0.5)

    if uid is not None:
        # Prevent multiple reads in <2 sec
        if uid == last_uid and (time.time() - last_time) < 2:
            continue

        print("Card detected! UID:", [hex(i) for i in uid])

        # Try to authenticate block 4
        if pn532.mifare_classic_authenticate_block(uid, 4, MIFARE_CMD_AUTH_A, key_a):
            print("Authentication successful for block 4!")
            data = pn532.mifare_classic_read_block(4)
            print("Block 4 Data:", data)
        else:
            print("Authentication failed!")

        last_uid = uid
        last_time = time.time()

        # Delay after successful scan
        time.sleep(2)
