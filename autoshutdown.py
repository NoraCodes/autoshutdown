#! ./bin/python
import paramiko
from click import confirm
from sys import argv
from time import sleep
import socket
import subprocess
import datetime

def checkPing(hostname):
    try:
        subprocess.check_call(
                ["/bin/ping", "-c1", "-w2", hostname], 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
        );
    except subprocess.CalledProcessError as e:
        return False;
    return True

if len(argv) < 3:
    print("Usage: autoshutdown.py server_list rsa_private_key [dry]");
    exit(1)

dry = False
if len(argv) > 3 and argv[3] == "dry":
    dry = True

serverListFilename = argv[1]
rsaPrivateKey = argv[2]

servers = []
with open(serverListFilename) as f:
    servers = [line.strip() for line in f 
            if line[0] != '#' and len(line.strip()) > 0]

upServers = []
for server in servers:
    if checkPing(server):
        print(server + " is up.")
        upServers += [server]
    else:
        print(server + " appears down (did not respond to ping).")

print("Servers to be powered off:")
for server in upServers:
    print("\t" + server)

if dry:
    print("DRY RUN")
confirm("Continue shutting off these servers?", abort=True);

# Load and init the key
privkey = paramiko.RSAKey.from_private_key_file(rsaPrivateKey)


touchedServers = []
for server in upServers:
    with paramiko.SSHClient() as client:
        # Don't break for input on new hosts
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print("Connecting to " + server)
        try:
            client.connect(
                    hostname=server,
                    username="root",
                    pkey=privkey,
                    timeout=10)
        except paramiko.AuthenticationException as error:
            print("Auth. exception connecting to " + server + " "\
                    + str(error))
            continue;
        except paramiko.PasswordRequiredException as error:
            print("Auth. exception connecting to " + server + \
                    " " + str(error))
            continue;
        except socket.gaierror as error:
            print("Name " + server + " does not resolve: " \
                    + error.strerror)
            continue;
        except socket.timeout as error:
            print("Connection to " + server + " timed out.")
            continue;
        if not dry:
            client.exec_command("shutdown -h now")
        touchedServers += [server]

if len(touchedServers) == 0:
    print("Touched 0 servers! Nothing was done.")
    exit(1)

stillUp = touchedServers
while len(stillUp) > 0:
    print("Waiting for shutdown of " + str(len(stillUp)) + " servers");
    sleep(5)

    for server in touchedServers:
        if checkPing(server):
            dt = str(datetime.datetime.now())
            print("\t" + server + " is still up at " + dt)
        else:
            dt = str(datetime.datetime.now())
            print("\t" + server + " went down at " + dt)
            stillUp.remove(server)

print("The following servers were shut down by this invocation:")
for server in touchedServers:
    print("\t" + server)
print("Success!")

