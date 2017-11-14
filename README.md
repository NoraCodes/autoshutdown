# autoshutdown
A script to turn off servers.


## autoshutdown.py

`autoshutdown.py` asks for a list of server names, each on a new line, and an RSA private key.

Sample servers file:

```
# This is a comment
test.your.domain.net
192.168.0.1
```

You can also provide the argument "dry", which will do everything the regular script does except for actually running `shutdown -h now` on the servers once connected.

