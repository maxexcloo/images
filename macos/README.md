# macOS

An AMD64 macOS VM with Reims graphics, streamed to the browser with Selkies.

## Run

Run a published GHCR image, ideally pinned by its `sha-` tag. Create a browser
password file, then start it:

```sh
cd macos
(umask 077; openssl rand -base64 32 > browser-password)
docker run --detach --name macos --restart unless-stopped \
  --shm-size 2g --stop-timeout 120 \
  --device /dev/dri --device /dev/kvm --device /dev/udmabuf \
  --env SELKIES_BASIC_AUTH_PASSWORD_FILE=/run/secrets/browser-password \
  --publish 127.0.0.1:8080:8080 \
  --volume "$PWD/browser-password:/run/secrets/browser-password:ro" \
  --volume macos:/storage \
  ghcr.io/maxexcloo/macos:latest
```

Open <https://localhost:8080> and sign in as `ubuntu` with that password. For remote
access, publish the port on the host's configured private address instead of
`127.0.0.1`.
HTTPS gives the browser the secure context WebCodecs needs. Selkies uses a
self-signed certificate by default. A reverse proxy can provide a trusted
certificate and set `SELKIES_ENABLE_HTTPS=false` on its private upstream.

On first start, the container creates the VM and downloads macOS Recovery from
Apple. Set `CPU_CORES`, `RAM_SIZE` and `DISK_SIZE` to choose VM resources;
`VERSION` picks the Recovery version. Changing the disk size or version doesn't
recreate an existing VM.

Persistent state lives in `/storage/config` and `/storage/reims`. Download
progress shows in the container log, and guest and graphics logs are under
`/storage/reims/vms/mac/logs`. Don't share whole QEMU command logs, since they can
include credentials or machine identity.

The first Recovery download can outlast the health check's startup grace period;
the container turns healthy once the VM starts.

## Host & TrueNAS

Use AMD64 Linux with working KVM, AVX2, a supported Vulkan GPU and enough memory
for the VM, graphics and streaming. Map `/dev/kvm` and `/dev/dri`. AMD GPUs also
need `/dev/udmabuf` for guest memory import. Configure host drivers, modules and
sysctls separately; Reims' host kernel and `vm.max_map_count` requirements still
apply.

macOS needs monotonic guest time. On hosts with an unstable TSC, you can avoid an
early `Non-monotonic time` panic with `CPU_CORES=1` and `--cpuset-cpus` limited
to the sibling threads of one physical core. It costs CPU throughput.

On Linux-based TrueNAS, install it as a custom Docker App with the same devices,
shared memory and environment. Bind a writable dataset to `/storage`, mount the
browser password file read-only at `/run/secrets/browser-password` and bind port
8080 to the NAS's private address.
Keep the two-minute stop grace period, because upstream `reims-ctl` asks the guest
to shut down before powering off. User-mode networking doesn't need
`/dev/net/tun` or `NET_ADMIN`.

## Display & Performance

Hardware encoding needs a supported codec and driver. Check streaming performance
on the deployment GPU; zero-copy streaming isn't guaranteed.

Input goes straight to the native window, and PipeWire carries guest audio into
the stream. WebSocket streaming uses the single HTTPS port without TURN.
Microphone, camera and guest clipboard integration aren't set up.

## Verification

A deployment is done when the macOS Recovery desktop is visible and usable on
the target host, with the native Reims window and Selkies stream running. A
healthy container, an encoded frame or an Apple boot logo on its own isn't
enough. Open Recovery's utilities and check keyboard and pointer input before
calling it ready. Installing macOS is a separate step.

From the repository root, run this against the live container:

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
