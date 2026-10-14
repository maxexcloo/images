#!/bin/sh
set -eu

image=$1
docker run --cap-drop=ALL --network=none --read-only --rm \
  --security-opt=no-new-privileges "$image" --version
container=$(docker run --cap-drop=ALL --detach --network=none --read-only \
  --security-opt=no-new-privileges --tmpfs /tmp "$image")
trap 'docker rm --force "$container" > /dev/null' EXIT HUP INT TERM
attempt=0
until docker exec "$container" curl --fail --silent http://localhost:8080/settings > /dev/null; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 30 ]; then
    docker logs "$container"
    exit 1
  fi
  sleep 1
done
