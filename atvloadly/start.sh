#!/bin/sh
set -eu
mkdir -p /run/avahi-daemon /run/dbus
rm -f /run/avahi-daemon/pid /run/dbus/pid
dbus-daemon --fork --system
avahi-daemon --daemonize --no-chroot
exec /entrypoint.sh "$@"
