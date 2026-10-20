# macOS

An AMD64 macOS VM with upstream Reims graphics in a native Vulkan window,
streamed to the browser with Selkies. QEMU renders straight into Selkies'
GPU-backed desktop, so there's no VNC server or separate viewer. USB audio uses
QEMU's native PipeWire backend.

## Run

Images are built and published on GitHub. Use the Compose example with a
published GHCR image, ideally pinned by its `sha-` tag. Create a browser password
file, then start it:

```sh
cd macos
(umask 077; openssl rand -base64 32 > browser-password)
docker compose up -d
```

Open <https://localhost:8080> and sign in as `ubuntu` with that password. For remote
access, set `MACOS_LISTEN_ADDRESS` to the host's configured private address.
HTTPS gives the browser the secure context WebCodecs needs. Selkies uses a
self-signed certificate by default. A reverse proxy can provide a trusted
certificate and set `SELKIES_ENABLE_HTTPS=false` on its private upstream.

`reims-ctl` creates the VM, downloads macOS Recovery from Apple and supplies
OpenCore and firmware through upstream `reims-util`. The defaults are macOS 26,
four vCPUs, 4 GiB RAM and a 64 GiB virtual disk. `CPU_CORES`, `RAM_SIZE` and
`DISK_SIZE` change those values, and `VERSION` picks the Recovery version when
creating a VM. Changing the disk size or version doesn't recreate an existing VM.

Persistent state lives in `/storage/config` and `/storage/reims`. Download
progress shows in the container log, and guest and graphics logs are under
`/storage/reims/vms/mac/logs`. Don't share whole QEMU command logs, since they can
include credentials or machine identity.

The container is healthy when QEMU is running and Selkies' health endpoint
responds. The first Recovery download can take longer than the health check's
startup grace period; the container turns healthy once the VM starts. Startup
waits a limited time for the display and fails if X still isn't available.

## Host & TrueNAS

Use AMD64 Linux with working KVM, AVX2, a supported Vulkan GPU and enough memory
for the VM, graphics and streaming. Map `/dev/kvm` and `/dev/dri`. AMD GPUs also
need `/dev/udmabuf` for guest memory import. The launcher adds the container user
to its mapped device groups but doesn't change host drivers, modules or sysctls.
Reims' host kernel and `vm.max_map_count` requirements still apply.

macOS needs monotonic guest time. On hosts with an unstable TSC, you can avoid an
early `Non-monotonic time` panic with `CPU_CORES=1` and a Compose `cpuset` limited
to the sibling threads of one physical core. It costs CPU throughput.

On Linux-based TrueNAS, Docker Apps can use the Compose example through
**Apps → Install Via YAML**. Bind a writable dataset to `/storage`, mount the
browser password as a secret and bind port 8080 to the NAS's private address.
Keep the two-minute stop grace period, because upstream `reims-ctl` asks the guest
to shut down before powering off. User-mode networking doesn't need
`/dev/net/tun` or `NET_ADMIN`.

## Display & Performance

The pinned upstream installer builds Reims, its matching QEMU and `reims-ctl`.
The toolchain, QEMU revision and helper dependencies are left to upstream. Reims'
borderless SDL window presents through Vulkan into Selkies' desktop. Selkies uses
the mapped GPU for rendering and encoding, and hardware encoding needs a
supported codec and driver. This skips the VNC encode, transport and decode step.
Frame copying, codec choice and latency still need checking on the deployment
GPU; zero-copy streaming isn't guaranteed.

Input goes straight to the native window, and PipeWire carries guest audio into
the stream. WebSocket streaming uses the single HTTPS port without TURN.
Microphone, camera and guest clipboard integration aren't set up.

## Verification

A deployment is done when the macOS Recovery desktop is visible and usable on
the target host, with the native Reims window and Selkies stream running. A
healthy container, an encoded frame or an Apple boot logo on its own isn't
enough. Open Recovery's utilities and check keyboard and pointer input before
calling it ready. Installing macOS is a separate step.

GitHub builds on native AMD64 and checks the packaged executables and libraries.
Runtime verification stays manual. From the repository root, run this against the
live container:

```sh
docker exec -i CONTAINER bash < macos/verify-stream.sh
docker cp CONTAINER:/tmp/macos-recovery.png /tmp/macos-recovery.png
```

The script checks the live QEMU PID, authentication on the configured backend
scheme and port, and an H.264 frame, then saves a screenshot to look at. Behind a
reverse proxy, also check HTTPS and streaming through its external URL. Then use
the browser to check Recovery's utilities and input. None of this proves Metal
works correctly in an installed macOS or says anything about streaming
performance.
