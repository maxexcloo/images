# syntax=docker/dockerfile:1
FROM docker.io/stilldeadcode/radiance:1.9.0 AS radiance
FROM ghcr.io/maxexcloo/comfyui-rocm:v0.41.0

COPY --from=radiance /opt/radiance /opt/radiance
# Keep Radiance's ROCm and libc separate from the Python/Comfy runtime.
COPY --from=radiance /lib64/ld-linux-x86-64.so.2 /opt/radiance/runtime/ld-linux-x86-64.so.2
COPY --from=radiance /usr/lib/x86_64-linux-gnu /opt/radiance/runtime/lib
