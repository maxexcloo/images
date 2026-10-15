# macOS

AMD64 macOS VM runtime with Reims graphics and a Selkies browser console.
QEMU, its firmware, the viewer, audio services and streaming run in one container.
macOS downloads from Apple at runtime; installation and VM disks persist in
`/storage`. The image does not contain an installed copy of macOS.

## Run

Build the image from the repository root:

```sh
mise exec -- python .github/scripts/image.py build macos --tag images-macos:test
```

The build requires an AMD64 Docker builder. CI uses a native AMD64 runner.
To run the local build, replace the Compose example's `image` with
`images-macos:test`. The GHCR tag becomes available only after publishing from
`main`; pin deployed images by their published digest.

Create a browser password file without printing its value, then start the service:

```sh
cd macos
(umask 077; openssl rand -base64 32 > browser-password)
docker compose up -d
```

Open <https://localhost:8080> and sign in as `ubuntu`, using the password from
your password manager or the mounted file. Selkies generates a self-signed
certificate. For access from another machine, set `MACOS_LISTEN_ADDRESS` to the
host's configured private interface address before starting Compose. The example
listens on loopback by default. A reverse proxy can terminate TLS instead; set
`SELKIES_ENABLE_HTTPS=false` when the private upstream requires HTTP.

The browser shows the VM when QEMU starts. Follow the
[Dockur installation instructions](https://github.com/dockur/macos#how-do-i-use-it)
to format the virtual disk and install macOS. Download progress appears in
`docker compose logs --follow macos` before the VM console is available.

## Host Requirements

- AMD64 Linux, hardware virtualisation enabled, AVX2, and an accessible `/dev/kvm`.
- A supported host GPU driver and Vulkan-capable GPU exposed through `/dev/dri`.
  Selkies also needs a supported encoder for hardware video encoding; software
  encoding can work when the GPU cannot encode the selected codec.
- At least 4 GiB of guest RAM plus headroom for Linux, QEMU and streaming, and
  sufficient writable storage for the configured disk and installer.

No host packages, kernel modules, sysctls or device permissions are changed by the
image. `NETWORK=slirp` uses QEMU's user-mode networking and avoids requiring
`/dev/net/tun` or `NET_ADMIN`. Devices and
host kernel support still have to exist: container packaging cannot supply them.
If a selected Reims version or GPU needs `/dev/udmabuf`, load it through the host's
supported configuration and add that device mapping. Likewise, an insufficient
host `vm.max_map_count` needs a host setting; it cannot be configured privately
through Compose. See the
[Reims host guidance](https://github.com/steelbrain/reims-vgpu#x86-64-guest-on-linux-kvm).
Do not add these changes speculatively; verify the target host first.

The default is `GPU=Y`. Missing GPU access fails startup rather than silently
claiming acceleration. `GPU=N` permits a basic software-rendered guest for
troubleshooting, while KVM is still required by the launcher.

## TrueNAS

Linux-based TrueNAS 24.10 and later can deploy the Compose example through
**Apps → Install Via YAML**. Replace the named storage volume with a writable
dataset bind mount if desired. Configure the password as a mounted secret file
at an absolute dataset path, or supply `SELKIES_BASIC_AUTH_PASSWORD` through your
deployment's credential configuration and remove the example secret mapping.
Use the NAS's configured private address for `MACOS_LISTEN_ADDRESS`.

KVM and the GPU must be available to Docker Apps. A GPU isolated for exclusive
VM passthrough is not available as a normal host rendering device. TrueNAS CORE
cannot run this Linux image directly. Exact TrueNAS release and GPU compatibility
require a test on the target NAS.

## Console & Audio

QEMU exposes VNC only through `/run/shm/macos-vnc.sock` inside the container.
TigerVNC displays it fullscreen in Selkies' private X11 session, using raw local
frame updates. Selkies encodes that display for the browser. This is not a
zero-copy path: Reims and the local viewer can copy frames, and performance must
be measured on the target GPU. Browser resizing does not guarantee a matching
macOS display mode; choose the guest resolution in macOS display settings.

Guest USB audio goes through QEMU's ALSA backend and the PulseAudio plugin to
Selkies' PipeWire-Pulse service. Keyboard and pointer input return through the
viewer. Microphone, camera, gamepad and guest clipboard forwarding are not
configured. WebSocket streaming uses the single HTTPS port; WebRTC/TURN is not
required for the default setup.

Container shutdown sends Dockur's ACPI shutdown request and retains the console
and audio services until the VM exits. Keep the Compose example's two-minute
grace period; do not interrupt storage while a guest is running.

## Updates & Verification

`source.json` pins Dockur. The Dockerfile pins both base image digests and the
QEMU release's executable, Reims firmware and shader-tool checksums. Keep those
three release artefacts together when updating `QEMU_VERSION`. The functional
startup hook lives in `patches/console.patch`. `patches/vulkan.patch` keeps Dockur's
display selector out of the headless Vulkan probe; otherwise `DISPLAY=vnc`
causes GPU detection to fail. OpenCore, VMHide and OSX-KVM
firmware use fixed upstream versions or revisions. Updatecli previews Dockur
source and base-image updates locally for manual review.

Build-time probes verify the GPU device registration, dynamic dependencies and
audio backend. The manual streaming check uses an isolated TCG console to verify
HTTPS authentication, the fullscreen viewer, an encoded H.264 WebSocket frame
and ALSA-to-PipeWire audio capture. Run it against a local image:

```sh
docker run --entrypoint bash --init --rm --shm-size 1g \
  --volume "$PWD/macos/verify-stream.sh:/verify-stream.sh:ro" \
  images-macos:test /verify-stream.sh
```

Run it from the repository root on an AMD64 Docker host. Local ARM64 checks skip this
recipe. Emulated build and console tests do not establish macOS boot, Metal
correctness, hardware encoding performance or TrueNAS compatibility; those need
an AMD64 host with the intended GPU.
