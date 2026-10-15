#!/usr/bin/env bash
# Manual check in an ephemeral container; uses TCG without macOS or host devices.
set -euo pipefail
umask 077

if /usr/local/bin/start-macos > /tmp/preflight.log 2>&1; then
    echo 'Launcher accepted a missing browser password' >&2
    exit 1
fi
grep -q 'browser access' /tmp/preflight.log
export SELKIES_BASIC_AUTH_PASSWORD
SELKIES_BASIC_AUTH_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
if /usr/local/bin/start-macos > /tmp/preflight.log 2>&1; then
    echo 'Launcher accepted a missing KVM device' >&2
    exit 1
fi
grep -q /dev/kvm /tmp/preflight.log
echo 'Missing credential & KVM startup checks: passed'

export DISPLAY=:20
export SELKIES_BASIC_AUTH_USER=ubuntu
mkdir -p "$XDG_RUNTIME_DIR"
chown ubuntu:ubuntu "$XDG_RUNTIME_DIR"
runuser -u ubuntu -- /etc/container-entrypoint.sh > /tmp/selkies.log 2>&1 &
session_pid=$!
qemu_pid=
cleanup() {
    if [ -n "$qemu_pid" ]; then
        kill "$qemu_pid" 2>/dev/null || true
        wait "$qemu_pid" 2>/dev/null || true
    fi
    runuser -u ubuntu -- s6-svscanctl -t /etc/service 2>/dev/null || true
    wait "$session_pid" 2>/dev/null || true
}
trap cleanup EXIT

for attempt in {1..120}; do
    if curl --fail --insecure --silent https://127.0.0.1:8080/api/health >/dev/null \
        && runuser -u ubuntu -- pactl info >/dev/null 2>&1; then break; fi
    [ "$attempt" != 120 ] || { tail -60 /tmp/selkies.log; exit 1; }
    sleep 0.5
done

qemu-system-x86_64 -accel tcg -display none -m 64 -machine q35 -nodefaults \
    -S -vga std -vnc unix:/run/shm/macos-vnc.sock \
    -audiodev alsa,id=snd,out.dev=pulse -device qemu-xhci -device usb-audio,audiodev=snd \
    > /tmp/qemu.log 2>&1 &
qemu_pid=$!
for attempt in {1..60}; do
    if [ -S /run/shm/macos-vnc.sock ]; then break; fi
    kill -0 "$qemu_pid" 2>/dev/null || { cat /tmp/qemu.log; exit 1; }
    sleep 0.5
done
chown ubuntu:ubuntu /run/shm/macos-vnc.sock
chmod 600 /run/shm/macos-vnc.sock
for attempt in {1..60}; do
    if runuser -u ubuntu -- xwininfo -root -tree | grep -q QEMU; then break; fi
    [ "$attempt" != 60 ] || { tail -40 /tmp/selkies.log; cat /tmp/qemu.log; exit 1; }
    sleep 0.5
done
kill -0 "$qemu_pid"
echo 'Private QEMU console, fullscreen viewer & ALSA backend: passed'

# Credentials stay inside this process, never in command arguments or output.
python3 - <<'PY'
import asyncio
import base64
import json
import math
import os
import ssl
import struct
import urllib.error
import urllib.request
import wave

import aiohttp

context = ssl._create_unverified_context()
url = 'https://127.0.0.1:8080/'
try:
    urllib.request.urlopen(url, context=context)
except urllib.error.HTTPError as error:
    assert error.code == 401, error.code
else:
    raise AssertionError('Browser admitted an unauthenticated request')
token = base64.b64encode(('ubuntu:' + os.environ['SELKIES_BASIC_AUTH_PASSWORD']).encode()).decode()
headers = {'Authorization': 'Basic ' + token}
with urllib.request.urlopen(urllib.request.Request(url, headers=headers), context=context) as response:
    assert response.status == 200
    assert b'<html' in response.read().lower()
print('HTTPS browser authentication: passed')

async def check_stream():
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.ws_connect(url + 'api/websockets', ssl=False) as client:
            await client.receive(timeout=10)
            await client.send_str('SETTINGS,' + json.dumps({
                'displayId': 'primary', 'initialClientWidth': 1280,
                'initialClientHeight': 720, 'manual_resolution': False,
                'framerate': 15, 'encoder': 'h264enc', 'video_crf': 25,
                'video_bitrate': 4000, 'audio_bitrate': 128000,
                'scaling_dpi': 96, 'displayPosition': 'right',
            }))
            async with asyncio.timeout(30):
                async for message in client:
                    if message.type == aiohttp.WSMsgType.BINARY:
                        data = message.data
                        if len(data) > 4 and data[0] == 0x04:
                            print('Authenticated WebSocket H.264 video frame: passed')
                            return
            raise AssertionError('No H.264 video frame received')

asyncio.run(check_stream())
with wave.open('/tmp/tone.wav', 'wb') as tone:
    tone.setparams((2, 2, 48000, 0, 'NONE', 'not compressed'))
    tone.writeframes(b''.join(struct.pack('<hh', *(2 * [int(12000 * math.sin(2 * math.pi * 440 * i / 48000))])) for i in range(96000)))
PY

timeout 5 runuser -u ubuntu -- parec --device=@DEFAULT_MONITOR@ --format=s16le --rate=48000 --channels=2 > /tmp/monitor.pcm &
capture_pid=$!
sleep 0.5
aplay --device=pulse --quiet /tmp/tone.wav
wait "$capture_pid" || [ "$?" = 124 ]
python3 - <<'PY'
from array import array

samples = array('h')
samples.frombytes(open('/tmp/monitor.pcm', 'rb').read())
assert any(abs(value) > 1000 for value in samples), 'ALSA playback did not reach the streaming audio monitor'
print('ALSA to PipeWire-Pulse audio capture: passed')
PY
