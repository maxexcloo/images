#!/bin/sh
set -eu

image=$1
docker run --cap-drop=ALL --network=none --read-only --rm \
  --security-opt=no-new-privileges "$image" --version
docker run --cap-drop=ALL --entrypoint curl --network=none --read-only --rm \
  --security-opt=no-new-privileges "$image" --version
