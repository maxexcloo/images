#!/bin/sh
echo "${CONFIG_0_CONTENT}" | base64 -d | gunzip > ${CONFIG_0_PATH}
export GATUS_CONFIG_PATH=${CONFIG_0_PATH}
tailscaled --socket /var/run/tailscale/tailscaled.sock --state /var/lib/tailscale/tailscaled.state &
tailscale up --authkey ${TAILSCALE_TAILNET_KEY} --hostname ${FLY_APP_NAME}-${FLY_MACHINE_ID}
/app/gatus
