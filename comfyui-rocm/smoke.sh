#!/bin/sh
set -eu

engine=${CONTAINER_ENGINE:-docker}
image=$1
revision=$2
actual=$("$engine" run --entrypoint git --network=none --read-only --rm \
  "$image" -C /default-comfyui-bundle/ComfyUI rev-parse HEAD)
test "$actual" = "$revision"
"$engine" run --entrypoint /usr/bin/python3.13 --network=none --read-only --rm \
  --tmpfs /tmp "$image" -c 'import torch, peft, rotary_embedding_torch; assert torch.version.hip; print("ROCm runtime imports passed.")'
