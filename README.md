# autoshutdown
A script to turn off servers.

Requires Python >= 3.4. Assumes a virtualenv with all packages in `requirements.txt` installed.


## autoshutdown.py

`autoshutdown.py` asks for a list of POSIX SSH server names, each on a new line, and an RSA private key.

Sample servers file:

```
# This is a comment
test.your.domain.net
192.168.0.1
```

You can also provide the argument "dry", which will do everything the regular script does except for actually running `shutdown -h now` on the servers once connected. You should always try this first:

```
./autoshutdown.py servers.txt ~/.ssh/id_rsa dry
```

## autoshutdown_windows.py

`autoshutdown_windows.py` asks for a list of Windows SMB RPC server names, each on a new line, with username and password, encrypted with encdec.

Sample file:

```
# This is a comment
test.your.domain.net admin lmaoThisis_a_bad_Password
192.168.0.6 leo userpassword45565
```

Then, encrypt this file with `encdec`:

```
./encdec.py enc servers.txt
```

Finally, run the script (try dry mode first):

```
./autoshutdown_windows.py servers.txt dry
```

