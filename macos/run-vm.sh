#!/usr/bin/env bash
set -euo pipefail

# Use the display and audio environment selected by Selkies for its desktop.
# shellcheck source=/dev/null
. "$XDG_RUNTIME_DIR/container-env"
export PATH="/usr/lib/reims/bin:$PATH"
manager=
started=
# shellcheck disable=SC2329 # Invoked by the signal and exit traps below.
stop() {
    trap '' TERM INT
    if [ -n "$started" ]; then
        reims-ctl stop --timeout 110 mac || true
        started=
    fi
    [ -z "$manager" ] || kill "$manager" 2>/dev/null || true
}
trap 'stop; exit 0' TERM INT
trap stop EXIT

if [ "${SELKIES_WAYLAND:-false}" != true ]; then
    until xdpyinfo >/dev/null 2>&1; do sleep 0.5; done
    openbox --sm-disable &
    manager=$!
fi
if [ ! -s "$REIMS_CTL_DATA_DIR/vms/mac/vm.toml" ]; then
    reims-ctl create --borderless --cpus "$CPU_CORES" --disk-size "$DISK_SIZE" \
        --logs --macos "$VERSION" --memory "$RAM_SIZE" --resolution 1920x1080 mac
fi
reims-ctl set --audio-backend pipewire --borderless --cpus "$CPU_CORES" \
    --extra-args '-global ICH9-LPC.disable_s3=1 -global ICH9-LPC.disable_s4=1' \
    --logs --memory "$RAM_SIZE" --stop-timeout 110 mac
reims-ctl start mac
started=1
pid=$(cat "$REIMS_CTL_DATA_DIR/vms/mac/qemu.pid")
while kill -0 "$pid" 2>/dev/null; do sleep 1; done
printf 'macOS: QEMU exited; check the VM logs in /storage/reims/vms/mac/logs.\n' >&2
exit 1
