#!/usr/bin/env bash
# Manual check inside the running VM container; Recovery must also be inspected.
set -euo pipefail

kill -0 "$(cat "$REIMS_CTL_DATA_DIR/vms/mac/qemu.pid")"
python3 - <<'PY'
import asyncio
import base64
import json
import os
import ssl
import urllib.error
import urllib.request

import aiohttp

context = ssl._create_unverified_context()
url = 'https://127.0.0.1:8080/'
try:
    urllib.request.urlopen(url, context=context)
except urllib.error.HTTPError as error:
    assert error.code == 401, error.code
else:
    raise AssertionError('Browser admitted an unauthenticated request')
password = (open(os.environ['SELKIES_BASIC_AUTH_PASSWORD_FILE']).read().strip()
            if os.environ.get('SELKIES_BASIC_AUTH_PASSWORD_FILE')
            else os.environ['SELKIES_BASIC_AUTH_PASSWORD'])
token = base64.b64encode(('ubuntu:' + password).encode()).decode()
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

with urllib.request.urlopen(urllib.request.Request(url + 'api/screenshot', headers=headers), context=context) as response:
    data = response.read()
    assert data.startswith(b'\x89PNG')
    open('/tmp/macos-recovery.png', 'wb').write(data)
print('Screenshot: /tmp/macos-recovery.png; inspect it and interact with Recovery to complete the gate.')
PY
