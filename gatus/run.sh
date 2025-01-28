#!/bin/sh
export GATUS_CONFIG_PATH=/app/config.yaml
tailscaled --socket /var/run/tailscale/tailscaled.sock --state /var/lib/tailscale/tailscaled.state &
tailscale up --authkey ${TAILSCALE_TAILNET_KEY} --hostname ${FLY_APP_NAME}-${FLY_MACHINE_ID}
(while tailscale status; do sleep 30; done; kill 1) &
exec /app/gatus
