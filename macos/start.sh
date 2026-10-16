#!/usr/bin/env bash
set -euo pipefail
umask 077

fail() { printf 'macOS: %s\n' "$*" >&2; exit 1; }

if [ -n "${SELKIES_BASIC_AUTH_PASSWORD_FILE:-}" ]; then
    export SELKIES_BASIC_AUTH_PASSWORD
    SELKIES_BASIC_AUTH_PASSWORD=$(cat "$SELKIES_BASIC_AUTH_PASSWORD_FILE")
fi
password=${SELKIES_BASIC_AUTH_PASSWORD:-}
[ -n "$password" ] && [ "$password" != mypasswd ] || fail 'Set SELKIES_BASIC_AUTH_PASSWORD_FILE or SELKIES_BASIC_AUTH_PASSWORD for browser access.'
export SELKIES_BASIC_AUTH_PASSWORD="$password"
unset password
[ -c /dev/kvm ] && [ -r /dev/kvm ] && [ -w /dev/kvm ] || fail 'Expose a working /dev/kvm from an AMD64 Linux host with virtualisation enabled.'
compgen -G '/dev/dri/renderD*' >/dev/null || fail 'Expose a Vulkan-capable host GPU through /dev/dri.'

# Match mapped device groups inside the container, including AMD guest-memory import.
for node in /dev/dri/renderD* /dev/dri/card* /dev/kvm /dev/udmabuf; do
    [ -c "$node" ] || continue
    device_group=$(stat -c %g "$node")
    if ! getent group "$device_group" >/dev/null; then
        groupadd --gid "$device_group" "gpu-$device_group"
    fi
    usermod --append --groups "$device_group" ubuntu
done
mkdir -p "$XDG_RUNTIME_DIR" "$REIMS_CTL_CONFIG_DIR" "$REIMS_CTL_DATA_DIR"
chown root:ubuntu /storage
chmod 750 /storage
chown ubuntu:ubuntu "$XDG_RUNTIME_DIR" "$REIMS_CTL_CONFIG_DIR" "$REIMS_CTL_DATA_DIR"
chmod 700 "$XDG_RUNTIME_DIR" "$REIMS_CTL_CONFIG_DIR" "$REIMS_CTL_DATA_DIR"
rm -f "$XDG_RUNTIME_DIR/container-env"

selkies_pid=
vm_pid=
# shellcheck disable=SC2329 # Invoked by the signal and exit traps below.
stop() {
    trap '' TERM INT
    if [ -n "$vm_pid" ]; then
        kill -TERM "$vm_pid" 2>/dev/null || true
        wait "$vm_pid" 2>/dev/null || true
        vm_pid=
    fi
    if [ -n "$selkies_pid" ]; then
        runuser -u ubuntu -- s6-svscanctl -t /etc/service 2>/dev/null || true
        wait "$selkies_pid" 2>/dev/null || true
        selkies_pid=
    fi
}
trap 'stop; exit 0' TERM INT
trap stop EXIT

runuser -u ubuntu -- /etc/container-entrypoint.sh &
selkies_pid=$!
for attempt in {1..120}; do
    if [ -s "$XDG_RUNTIME_DIR/container-env" ] \
        && runuser -u ubuntu -- pactl info >/dev/null 2>&1; then break; fi
    kill -0 "$selkies_pid" 2>/dev/null || fail 'Selkies exited during startup.'
    [ "$attempt" != 120 ] || fail 'Selkies did not become ready within 60 seconds.'
    sleep 0.5
done

runuser -u ubuntu -- /usr/local/lib/macos/run-vm.sh &
vm_pid=$!
set +e
wait -n "$vm_pid" "$selkies_pid"
result=$?
set -e
exit "$result"
