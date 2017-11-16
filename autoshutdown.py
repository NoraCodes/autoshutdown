#! ./bin/python

"""
autoshutdown.py server_list rsa_private_key [dry]

Logs into every server specified in server_list using rsa_private_key
    and executes "shutdown -h now" as root.
"""

from sys import argv
from time import sleep
import socket
import subprocess
import datetime

import paramiko
from click import confirm


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


if len(argv) < 3:
    print("Usage: autoshutdown.py server_list rsa_private_key [dry]")
    exit(1)

DRY = False
if len(argv) > 3 and argv[3].lower() == "dry":
    DRY = True

SERVER_LIST_FILENAME = argv[1]
RSA_PRIVATE_KEY = argv[2]

SERVERS = []
with open(SERVER_LIST_FILENAME) as f:
    SERVERS = [line.strip() for line in f
               if line[0] != '#' and len(line.strip()) > 0]

UP_SERVERS = []
for server in SERVERS:
    if check_ping(server):
        print(server + " is up.")
        UP_SERVERS += [server]
    else:
        print(server + " appears down (did not respond to ping).")

if not UP_SERVERS:
    print("No specified servers are up. Exiting.")
    exit(0)

print("Servers to be powered off:")
for server in UP_SERVERS:
    print("\t" + server)

if DRY:
    confirm("Continue contacting off these servers? Dry run.", abort=True)
else:
    confirm("Continue shutting off these servers?", abort=True)

# Load and init the key
PRIVKEY = paramiko.RSAKey.from_private_key_file(RSA_PRIVATE_KEY)

TOUCHED_SERVERS = []
for server in UP_SERVERS:
    with paramiko.SSHClient() as client:
        # Don't break for input on new hosts
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print("Connecting to " + server)
        try:
            client.connect(
                hostname=server,
                username="root",
                pkey=PRIVKEY,
                timeout=10)
        except paramiko.PasswordRequiredException as error:
            print("Password required exception connecting to " + server +
                  " " + str(error))
            continue
        except paramiko.AuthenticationException as error:
            print("Authentication exception connecting to " + server + " "
                  + str(error))
            continue
        except socket.gaierror as error:
            print("Name " + server + " does not resolve: "
                  + error.strerror)
            continue
        except socket.timeout as error:
            print("Connection to " + server + " timed out.")
            continue
        # Run our payload, if any
        if not DRY:
            client.exec_command("shutdown -h now")
        TOUCHED_SERVERS += [server]

if not TOUCHED_SERVERS:
    print("Unable to connect to any servers. Nothing was done.")
    exit(1)

STILL_UP = TOUCHED_SERVERS
while STILL_UP:
    print("Waiting for shutdown of " + str(len(STILL_UP)) + " servers")
    sleep(5)

    for server in TOUCHED_SERVERS:
        if check_ping(server):
            dt = str(datetime.datetime.now())
            print("\t" + server + " is still up at " + dt)
        else:
            dt = str(datetime.datetime.now())
            print("\t" + server + " went down at " + dt)
            STILL_UP.remove(server)

print("The following servers were shut down by this invocation:")
for server in TOUCHED_SERVERS:
    print("\t" + server)
print("Success!")
