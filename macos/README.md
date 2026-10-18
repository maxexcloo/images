# macOS

AMD64 macOS VM with upstream Reims graphics, a native Vulkan-backed window and
Selkies browser streaming. QEMU renders directly into Selkies' GPU-backed desktop;
there is no VNC server or separate viewer. USB audio uses QEMU's native PipeWire
backend.

## Run

Images build and publish on GitHub. Use the Compose example with a published GHCR
image, preferably pinned by digest. Create a browser password file, then start:

```sh
cd macos
(umask 077; openssl rand -base64 32 > browser-password)
docker compose up -d
```

Open <https://localhost:8080> and sign in as `ubuntu` with that password. For remote
access, set `MACOS_LISTEN_ADDRESS` to the host's configured private address.
HTTPS provides the browser secure context used by WebCodecs. Selkies uses a
self-signed certificate by default; a reverse proxy can provide a trusted
certificate and use `SELKIES_ENABLE_HTTPS=false` on its private upstream.

`reims-ctl` creates the VM, downloads macOS Recovery from Apple and supplies its
OpenCore and firmware through upstream `reims-util`. The default is macOS 26,
four vCPUs, 4 GiB RAM and a 64 GiB virtual disk. `CPU_CORES`, `RAM_SIZE` and
`DISK_SIZE` configure those values; `VERSION` chooses the Recovery version when
creating a VM. Disk size and version do not recreate an existing VM.

Persistent state lives in `/storage/config` and `/storage/reims`. Download
progress appears in the container log; guest and graphics logs live under
`/storage/reims/vms/mac/logs`. Do not print whole QEMU command logs when sharing
credentials or machine identity could be included.

Container health requires a live QEMU process and Selkies' health endpoint.
Initial Recovery downloads can exceed the health check's startup grace period;
the container becomes healthy after the VM starts. Display readiness has a bounded
wait and fails startup if X remains unavailable.

## Host & TrueNAS

Use AMD64 Linux with working KVM, AVX2, a supported Vulkan GPU and enough memory
for the VM, graphics and streaming. Map `/dev/kvm` and `/dev/dri`; AMD GPUs also
need `/dev/udmabuf` for guest-memory import. The launcher grants the container user
its mapped device groups. It does not change host drivers, modules or sysctls.
Reims' host kernel and `vm.max_map_count` requirements still apply.

macOS requires monotonic guest time. On hosts with an unstable TSC, an early
`Non-monotonic time` panic can be avoided with `CPU_CORES=1` and a Compose
`cpuset` limited to the sibling threads of one physical core, at the cost of CPU
throughput.

Linux-based TrueNAS Docker Apps can use the Compose example through
**Apps → Install Via YAML**. Bind a writable dataset to `/storage`, mount the
browser password as a secret, and bind port 8080 to the NAS's private address.
Keep the two-minute stop grace period: upstream `reims-ctl` requests guest
shutdown before powering off. User-mode networking needs neither `/dev/net/tun`
nor `NET_ADMIN`.

## Display & Performance

The pinned upstream installer builds Reims, its matching QEMU and `reims-ctl`;
its toolchain, QEMU revision and helper dependencies remain upstream-owned.
Reims' own borderless SDL window presents through Vulkan into Selkies' desktop.
Selkies selects the mapped GPU for rendering and encoding; a supported codec and
driver are required for hardware encoding. This removes the VNC encode, transport
and decode hop. Actual frame-copy behaviour, codec selection and latency must be
verified on the deployment GPU; this is not a promise of zero-copy streaming.

Input goes directly to the native window. PipeWire carries guest audio into the
stream. WebSocket streaming uses the single HTTPS port, without TURN. Microphone,
camera and guest clipboard integration are not configured.

## Verification

The completion gate is a visible, usable macOS Recovery desktop on the target
host, with the native Reims window and Selkies stream running. A healthy
container, an encoded frame or an Apple boot logo alone does not pass it. Open
Recovery's utilities and check keyboard and pointer input before declaring the
deployment ready. Installing macOS is a separate action.

GitHub builds on native AMD64 and checks the packaged executables and libraries.
Keep runtime verification manual. From the repository root, run against the live
container:

```sh
docker exec -i CONTAINER bash < macos/verify-stream.sh
docker cp CONTAINER:/tmp/macos-recovery.png /tmp/macos-recovery.png
```

The script checks the live QEMU PID, authentication on the configured backend
scheme and port, and an H.264 frame, then saves a screenshot for inspection. With
a reverse proxy, also verify HTTPS and streaming through its external URL. Then
use the browser to verify Recovery's utilities and input. These checks do not
establish installed macOS Metal
correctness or streaming performance.
