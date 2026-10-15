#!/usr/bin/env bash
# Sourced after Dockur config.sh, before it launches QEMU.

# The viewer talks over a private socket; VNC is never a network service.
# shellcheck disable=SC2034 # Consumed by Dockur's buildArguments function.
DISPLAY_OPTS="-display none ${REIMS_OPTS:-$VGA_ARG} -vnc unix:/run/shm/macos-vnc.sock"
# The release's ALSA backend reaches Selkies' PipeWire-Pulse through its ALSA plugin.
# shellcheck disable=SC2034 # Consumed by Dockur's buildArguments function.
AUDIO_OPTS="-audiodev alsa,id=snd,out.dev=pulse -device usb-audio,audiodev=snd"
buildArguments
