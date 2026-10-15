#!/usr/bin/env bash
set -euo pipefail

[ ! -f /run/shm/qemu.end ]
if [ -s /run/shm/qemu.pid ]; then
    kill -0 "$(cat /run/shm/qemu.pid)"
    [ -S /run/shm/macos-vnc.sock ]
fi
scheme=https
[ "${SELKIES_ENABLE_HTTPS:-true}" != false ] || scheme=http
curl --fail --insecure --max-time 3 --silent "$scheme://127.0.0.1:${SELKIES_PORT:-8080}/api/health" >/dev/null
