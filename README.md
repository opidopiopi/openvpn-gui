# OpenVPN-GUI

A gui for OpenVPN using python and nicegui.


## The why

This gui connects to the management interface of a running openvpn instance.
The main purpose is to provide a user interface for unprivileged users.
As openvpn needs certain privileges to create network devices and routes,
a "normal" user cannot start openvpn instances.


## The how

By enabling the management interface it is possible to configure and
start an openvpn instance (e.g. using a systemd-unit) which this gui then connects to.

The client can toggle the connection and will answer interactive queries by the openvpn instance.


## Configuration

To enable connecting to the management interface you must specify the following options:
```
# specify how to connect to the management interface:
management <unix socket path> unix [password-file]
# or
management 127.0.0.1 <port> [password-file]
# make openvpn ask the gui for passwords:
management-query-passwords
```

If you want to use smartcards for authentication add:
```
pkcs11-id-management
pkcs11-pin-cache 60
```


# Build

To build and run just:
```
uv run openvpn-gui
```

To build a self contained executable use:
```
uv run --extra package nicegui-pack --onefile --name "openvpn-gui" src/openvpn_gui/main.py
```


# Shameless copies

`omi.py` is copied from https://gerrit.openvpn.net/c/openvpn/+/1859 with slight modifications
to fix the inconsistencies of `pkcs11-id-get` and some bugfixes.


# Copyright/Branding notice

This project is in no way affiliated to the company nor the open source project OpenVPN.

All colors an icons used can be found at https://openvpn.net/branding/. 
