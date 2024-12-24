#!/bin/sh
tailscaled --socket /var/run/tailscale/tailscaled.sock --state /var/lib/tailscale/tailscaled.state &
tailscale up --authkey ${TAILSCALE_TAILNET_KEY} --hostname ${FLY_APP_NAME}-${FLY_MACHINE_ID}
GATUS_CONFIG_PATH=/app/config.yaml /app/gatus
