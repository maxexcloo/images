#!/bin/sh
set -eu

engine=${CONTAINER_ENGINE:-docker}
image=$1
configuration=$(mktemp)
container=
cleanup() {
  if [ -n "$container" ]; then
    "$engine" rm --force "$container" > /dev/null
  fi
  rm -f "$configuration"
}
trap cleanup EXIT HUP INT TERM
cat > "$configuration" <<'YAML'
endpoints:
  - name: Smoke Test
    url: http://127.0.0.1:8080/health
    interval: 1m
    conditions:
      - "[STATUS] == 200"
YAML
"$engine" run --cap-drop=ALL --entrypoint /app/tailscale --network=none --read-only --rm \
  --security-opt=no-new-privileges "$image" version
container=$("$engine" run --cap-drop=ALL --detach --network=none --read-only \
  --security-opt=no-new-privileges --volume "$configuration:/app/config/smoke.yaml:ro" "$image")
attempt=0
until "$engine" exec "$container" wget -q -O /dev/null http://127.0.0.1:8080/health; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 30 ]; then
    "$engine" logs "$container"
    exit 1
  fi
  sleep 1
done
