#!/usr/bin/env bash
set -euo pipefail

pidfile="$REIMS_CTL_DATA_DIR/vms/mac/qemu.pid"
[ -s "$pidfile" ]
kill -0 "$(cat "$pidfile")"
scheme=https
[ "${SELKIES_ENABLE_HTTPS:-true}" != false ] || scheme=http
curl --fail --insecure --max-time 3 --silent "$scheme://127.0.0.1:${SELKIES_PORT:-8080}/api/health" >/dev/null
