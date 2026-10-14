#!/bin/sh
set -eu

image=$1
docker run --cap-drop=ALL --network=none --read-only --rm \
  --security-opt=no-new-privileges "$image" --version
docker run --cap-drop=ALL --entrypoint python --network=none --read-only --rm \
  --security-opt=no-new-privileges --tmpfs /data:uid=1000,gid=1000,mode=0700 \
  "$image" -c 'from betterbench.corpus import load_corpus; from betterbench.runs import betterbench_home; assert load_corpus(categories=["prose"]); (betterbench_home() / "smoke.txt").write_text("ok")'
