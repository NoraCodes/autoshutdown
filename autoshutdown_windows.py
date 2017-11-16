#! ./bin/python

"""
autoshutdown_windows.py server_list [dry]

Logs into every server specified in server_list using rsa_private_key
    and executes "shutdown -h now" as root.
"""

from sys import argv
from time import sleep
import subprocess
import datetime
import hashlib
import base64

from click import confirm, prompt
import cryptography
from cryptography.fernet import Fernet


def check_ping(hostname):
    """
    Runs the system ping command, checking if given hostname appears up.
    """
    try:
        subprocess.check_call(
            ["/bin/ping", "-c1", "-w2", hostname],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError:
        return False
    return True


def shutdown_with_netrpc(hostname, username, password):
    """
    Runs net rpc shutdown to shut down the remote machine, returning True if successful, False otherwises
    """
    try:
        subprocess.check_call(
            ["/usr/bin/net", "rpc", "shutdown", "-I", hostname, "-U", username + "%" + password],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError:
        return False
    return True

def check_with_netrpc(hostname, username, password):
    """
    Runs net rpc test to test connection to the remote machine, returning True if successful, False otherwises
    """
    try:
        subprocess.check_call(
            ["/usr/bin/net", "rpc", "conf", "list", "-I", hostname, "-U", username + "%" + password],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError:
        return False
    return True

if len(argv) < 2:
    print("Usage: autoshutdown.py server_list [dry]")
    print("\tThe file should contain lines like hostname username password and be encrypted with encdec")
    exit(1)

DRY = False
if len(argv) > 2 and argv[2].lower() == "dry":
    DRY = True

SERVER_LIST_FILENAME = argv[1]

DATA_IN = b""
with open(SERVER_LIST_FILENAME, "rb") as f:
    DATA_IN = f.read()

# Acquire the key. The process is the same for both encryption and decryption
print("Enter your encryption password below. The value will be hidden.")
PASSWORD_STRING = prompt("Enter  passphrase", hide_input=True)
HASHER = hashlib.sha256()
HASHER.update(bytes(PASSWORD_STRING, "utf-8"))
KEY_BYTES = HASHER.digest()
KEY_B64 = base64.urlsafe_b64encode(KEY_BYTES)
F = Fernet(KEY_B64)
DEC_DATA = b""

try:
    DEC_DATA = F.decrypt(DATA_IN)
except cryptography.fernet.InvalidToken:
    print("Invalid signature. Either the file was tampered with \
           or you have entered the wrong password.")
    exit(1)

SERVERS = [] 
for line in DEC_DATA.splitlines():
    strline = str(line.strip(), "utf-8")
    if strline and strline[0] != '#':
        splitline = strline.split(" ")
        if len(splitline) != 3:
            print("WARN: Discarding garbage line '" + strline + "'")
        else:
            SERVERS += [splitline]

UP_SERVERS = []
for line in SERVERS:
    server = line[0]
    if check_ping(server):
        print(server + " is up.")
        UP_SERVERS += [line]
    else:
        print(server + " appears down (did not respond to ping).")

if not UP_SERVERS:
    print("No specified servers are up. Exiting.")
    exit(0)

print("Servers to be powered off:")
for line in UP_SERVERS:
    server = line[0]
    print("\t" + server)

if DRY:
    confirm("Continue contacting off these servers? Dry run.", abort=True)
else:
    confirm("Continue shutting off these servers?", abort=True)

TOUCHED_SERVERS = []
for line in UP_SERVERS:
    server = line[0]
    username = line[1]
    password = line[2]
    succ = False
    if not DRY:
        succ = shutdown_with_netrpc(server, username, password)
    else:
        succ = check_with_netrpc(server, username, password)
    if succ:
        TOUCHED_SERVERS += [line]
    else:
        print("WARN: Failed to connect to '" + server + "' with user '" + username + "'")

if not TOUCHED_SERVERS:
    print("Unable to connect to any servers. Nothing was done.")
    exit(1)

STILL_UP = TOUCHED_SERVERS
DELAY = 5
while STILL_UP:
    print("Waiting for shutdown of " + str(len(STILL_UP)) + " servers")
    sleep(DELAY)

    for line in TOUCHED_SERVERS:
        server = line[0]
        if check_ping(server):
            dt = str(datetime.datetime.now())
            print("\t" + server + " is still up within " + str(DELAY) + " seconds of " + dt)
        else:
            dt = str(datetime.datetime.now())
            print("\t" + server + " went down within " + str(DELAY) + " seconds of " + dt)
            STILL_UP.remove(server)

print("The following servers were shut down by this invocation:")
for server in TOUCHED_SERVERS:
    print("\t" + server)
print("Success!")
