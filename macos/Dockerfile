# syntax=docker/dockerfile:1
FROM ghcr.io/selkies-project/selkies/base:latest-debiantrixie AS build
USER 0
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG UPSTREAM_REVISION
ENV CARGO_BUILD_JOBS=2 \
    CARGO_INSTALL_ROOT=/out/usr/lib/reims \
    CARGO_PROFILE_RELEASE_DEBUG=0 \
    DEBIAN_FRONTEND=noninteractive
RUN apt-get update -o APT::Update::Error-Mode=any \
    && apt-get install --no-install-recommends -y \
        binutils bison build-essential bzip2 ca-certificates clang cmake curl flex git \
        libasound2-dev libdbus-1-dev libdecor-0-dev libdrm-dev libegl-dev libfdt-dev \
        libgbm-dev libgl-dev libglib2.0-dev libpipewire-0.3-dev libpixman-1-dev \
        libpulse-dev libslirp-dev libudev-dev libvulkan1 libwayland-bin libwayland-dev \
        libx11-dev libxcursor-dev libxext-dev libxfixes-dev libxi-dev libxkbcommon-dev \
        libxrandr-dev libxss-dev libxtst-dev lld ninja-build pkg-config python3 \
        python3-venv zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
RUN <<'BUILD'
set -euo pipefail
git init /src/reims
git -C /src/reims remote add origin https://github.com/steelbrain/reims-vgpu.git
git -C /src/reims fetch --depth=1 origin "$UPSTREAM_REVISION"
git -C /src/reims checkout --detach FETCH_HEAD
bash /src/reims/scripts/install-ctl.sh --yes
cp -a "$HOME/.local/share/reims-ctl/qemu/current/." /out/usr/lib/reims/qemu
mkdir -p /out/usr/share/licenses/reims
cp /src/reims/LICENSE /out/usr/share/licenses/reims/LICENSE
cp -a /src/reims/LICENSES /out/usr/share/licenses/reims/
cp /src/reims/vendor/qemu/COPYING /out/usr/share/licenses/reims/QEMU-COPYING
cp /src/reims/vendor/qemu/COPYING.LIB /out/usr/share/licenses/reims/QEMU-COPYING.LIB
/out/usr/lib/reims/bin/reims-ctl --version
/out/usr/lib/reims/bin/reims-util --version
/out/usr/lib/reims/qemu/bin/qemu-system-x86_64 -device help | grep -F apple-gfx-pci
rm -rf /src/reims "$HOME/.cache/reims-ctl" "$HOME/.cargo" "$HOME/.rustup" \
    "$HOME/.local/share/reims-ctl" "$HOME/.config/reims-ctl"
BUILD
# Resolve canonical paths: this distribution records merged-/usr library paths.
RUN ldd /out/usr/lib/reims/bin/reims-* /out/usr/lib/reims/qemu/bin/qemu-* \
    | awk '/=> \// { print $3 }' | xargs realpath | sort -u \
    | xargs dpkg-query --search | cut -d: -f1 | sort -u > /out/runtime-packages

FROM ghcr.io/selkies-project/selkies/base:latest-debiantrixie
USER 0
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV DEBIAN_FRONTEND=noninteractive
COPY --from=build /out/runtime-packages /tmp/runtime-packages
RUN apt-get update -o APT::Update::Error-Mode=any \
    && apt-get install --no-install-recommends -y $(cat /tmp/runtime-packages) \
        libdecor-0-0 libwayland-client0 libx11-6 libxcursor1 libxext6 libxfixes3 \
        libxi6 libxkbcommon0 libxrandr2 libxss1 libxtst6 openbox procps tini vulkan-tools \
    && rm -rf /var/lib/apt/lists/* /tmp/runtime-packages
COPY --from=build /out/usr/ /usr/
COPY --chmod=755 start.sh /usr/local/bin/start-macos
COPY --chmod=755 health.sh run-vm.sh /usr/local/lib/macos/
RUN /usr/lib/reims/bin/reims-ctl --version \
    && /usr/lib/reims/bin/reims-util --version \
    && /usr/lib/reims/qemu/bin/qemu-system-x86_64 -device apple-gfx-pci,help >/dev/null \
    && ! ldd /usr/lib/reims/bin/reims-* /usr/lib/reims/qemu/bin/qemu-* | grep 'not found' \
    && bash -n /usr/local/bin/start-macos /usr/local/lib/macos/*.sh
ENV CPU_CORES=4 \
    DISK_SIZE=64G \
    RAM_SIZE=4G \
    REIMS_CTL_CONFIG_DIR=/storage/config \
    REIMS_CTL_DATA_DIR=/storage/reims \
    REIMS_CTL_QEMU=/usr/lib/reims/qemu/bin/qemu-system-x86_64 \
    SELKIES_ENABLE_BASIC_AUTH=true \
    SELKIES_ENABLE_DUAL_MODE=false \
    SELKIES_MODE=websockets \
    SELKIES_WAYLAND=false \
    VERSION=26
EXPOSE 8080
VOLUME /storage
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 CMD /usr/local/lib/macos/health.sh
ENTRYPOINT ["/usr/bin/tini", "-s", "--", "/usr/local/bin/start-macos"]
