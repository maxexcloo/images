#!/bin/sh
set -eu

image=$1
container=$(docker run --detach --network=none \
  --security-opt=seccomp=unconfined "$image")
trap 'docker rm --force "$container" > /dev/null' EXIT HUP INT TERM
attempt=0
until docker exec "$container" curl --fail --silent http://localhost:5533/ > /dev/null; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 60 ]; then
    docker logs "$container"
    exit 1
  fi
  sleep 1
done
docker exec "$container" test -s /usr/share/licenses/atvloadly/LICENSE
docker exec "$container" sh -c 'test -s /run/avahi-daemon/pid && test -s /run/dbus/pid'
