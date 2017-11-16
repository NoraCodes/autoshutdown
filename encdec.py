#!./bin/python

from sys import argv
import base64
import hashlib

import cryptography
from cryptography.fernet import Fernet
from click import prompt

USAGE = "Usage: \n\tencdec.py enc input output\n\tencdec.py dec input output"

if len(argv) != 4:
    print("Not enough arguments.")
    print(USAGE)
    exit(1)

if argv[1].lower() not in ["enc", "dec"]:
    print("Command " + argv[1] + " was not understood.")
    print(USAGE)
    exit(1)

COMMAND = argv[1].lower()
INPUT_FILENAME = argv[2]
OUTPUT_FILENAME = argv[3]

# Try to read from the file.
DATA_IN = b""
with open(INPUT_FILENAME, "rb") as f:
    DATA_IN = f.read()

# Acquire the key. The process is the same for both encryption and decryption
print("Enter your encryption password below. The value will be hidden.")
PASSWORD_STRING = prompt("Enter  passphrase", hide_input=True)
if COMMAND == "enc":
    PASSWORD_STRING_VERIF = prompt("Verify passphrase", hide_input=True)
    if (PASSWORD_STRING != PASSWORD_STRING_VERIF):
        print("Passphrases do not match!")
        exit(1)
HASHER = hashlib.sha256()
HASHER.update(bytes(PASSWORD_STRING, "utf-8"))
KEY_BYTES = HASHER.digest()
KEY_B64 = base64.urlsafe_b64encode(KEY_BYTES)

# Create a Fernet enc/dec with the key
F = Fernet(KEY_B64)

# Buffer for data to be written
DATA_OUT = b""

if COMMAND == "enc":
    DATA_OUT = F.encrypt(DATA_IN)
elif COMMAND == "dec":
    try:
        DATA_OUT = F.decrypt(DATA_IN)
    except cryptography.fernet.InvalidToken:
        print("Invalid signature. Either the file was tampered with or you have entered the wrong password.")
        exit(1)
else:
    raise TypeError("INVALID COMMAND " + COMMAND)

with open(OUTPUT_FILENAME, "wb") as f:
    f.write(DATA_OUT)

print("Completed successfully!")
