# syntax=docker/dockerfile:1.19

FROM qemux/qemu:7.50@sha256:e7f6fda52503a546fd649670ba46e4bc23dc6dcef275bc3fac48877fbbc430df AS runtime
ARG UPSTREAM_REVISION
COPY --from=upstream --chmod=755 /src /run/
COPY --from=upstream --chmod=755 /assets /assets/
ADD https://raw.githubusercontent.com/dockur/macos/${UPSTREAM_REVISION}/license.md /usr/share/doc/dockur-macos/LICENSE

# Keep the executable, GPU firmware and shader tool from one verified release.
ARG QEMU_VERSION=11.1.3
ADD --checksum=sha256:eda9d286368183f9abc192d6fb5f989eb754c81e78a93e5051d45c0085ad4aa5 --chmod=755 https://github.com/qemus/qemu-macos/releases/download/v${QEMU_VERSION}/qemu-system-x86_64 /usr/bin/qemu-system-x86_64
ADD --checksum=sha256:e3abd51894be2c488369ab42bd51d398f074389e5ed375e1b8c090cd4a09eded --chmod=755 https://github.com/qemus/qemu-macos/releases/download/v${QEMU_VERSION}/air-dis /usr/local/bin/air-dis
ADD --checksum=sha256:e9b61baddfddce60c7767d0b3687efebf21b41b6edddad844fcd411ed9481681 --chmod=644 https://github.com/qemus/qemu-macos/releases/download/v${QEMU_VERSION}/reims-vgpu-gop.rom /usr/share/qemu/reims-vgpu-gop.rom

ARG OPENCORE_VERSION=1.0.7
RUN <<EOF
set -eu
for build in RELEASE DEBUG; do
    flavour=$(printf '%s' "$build" | tr '[:upper:]' '[:lower:]')
    wget -q -O /tmp/opencore.zip "https://github.com/acidanthera/OpenCorePkg/releases/download/$OPENCORE_VERSION/OpenCore-$OPENCORE_VERSION-$build.zip"
    unzip -q /tmp/opencore.zip 'X64/EFI/*' -d /tmp/opencore
    mkdir -p "/opencore/$flavour"
    cp -a /tmp/opencore/X64/EFI "/opencore/$flavour/EFI"
    if [ "$build" = RELEASE ]; then
        unzip -p /tmp/opencore.zip Utilities/macserial/macserial.linux > /usr/local/bin/macserial
        chmod 755 /usr/local/bin/macserial
    fi
    rm -rf /tmp/opencore /tmp/opencore.zip
done
printf '%s\n' "$OPENCORE_VERSION" > /opencore/version
printf '%s\n' "$UPSTREAM_REVISION" > /etc/version
# Install the packages owning the executable's shared libraries in the final base.
ldd /usr/bin/qemu-system-x86_64 /usr/bin/qemu-img /usr/local/bin/air-dis \
    | awk '/=> \// { print $3 }' | sort -u \
    | xargs dpkg-query --search | cut -d: -f1 | grep -v '^qemu-render$' | sort -u > /runtime-packages
EOF

ADD --chmod=644 https://raw.githubusercontent.com/kholia/OSX-KVM/326053dd61f49375d5dfb28ee715d38b04b5cd8e/OVMF_CODE.fd /usr/share/OVMF/OVMF_CODE.fd
ADD --chmod=644 https://raw.githubusercontent.com/kholia/OSX-KVM/326053dd61f49375d5dfb28ee715d38b04b5cd8e/OVMF_VARS.fd /usr/share/OVMF/OVMF_VARS.fd
ADD --chmod=644 https://raw.githubusercontent.com/kholia/OSX-KVM/326053dd61f49375d5dfb28ee715d38b04b5cd8e/OVMF_VARS-1024x768.fd /usr/share/OVMF/OVMF_VARS-1024x768.fd
ADD --chmod=644 https://raw.githubusercontent.com/kholia/OSX-KVM/326053dd61f49375d5dfb28ee715d38b04b5cd8e/OVMF_VARS-1920x1080.fd /usr/share/OVMF/OVMF_VARS-1920x1080.fd
ADD https://github.com/Carnations-Botanica/VMHide/releases/download/2.0.0/VMHide-2.0.0-RELEASE.zip /vmh.zip
ADD https://github.com/LongQT-sea/OpenCore-ISO/releases/download/v0.7/LongQT-OpenCore-v0.7.iso /opencore.iso

FROM ghcr.io/selkies-project/selkies/base:latest-debiantrixie@sha256:4926b252eabd23dce9b9d52eedcc17588fff4b2c28c3930766516467028b06e7
USER 0
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV DEBIAN_FRONTEND=noninteractive
COPY --from=runtime /runtime-packages /tmp/runtime-packages
RUN apt-get update -o APT::Update::Error-Mode=any \
    && apt-get install --no-install-recommends -y $(cat /tmp/runtime-packages) \
        aria2 bc cpio curl dnsmasq-base fdisk file genisoimage gzip ipcalc iproute2 jq libasound2-plugins libgbm1 mtools \
        netcat-openbsd openbox p7zip-full procps pulseaudio-utils python3 spirv-tools tigervnc-viewer \
        tini unzip util-linux vulkan-tools wget xar xmlstarlet xxd xz-utils \
    && rm -rf /var/lib/apt/lists/* /tmp/runtime-packages

COPY --from=runtime /run/ /run/
COPY --from=runtime /assets/ /assets/
COPY --from=runtime /etc/version /etc/version
COPY --from=runtime /opencore/ /opencore/
COPY --from=runtime /opencore.iso /vmh.zip /
COPY --from=runtime /usr/bin/qemu-img /usr/bin/qemu-system-x86_64 /usr/bin/
COPY --from=runtime /usr/local/bin/air-dis /usr/local/bin/macserial /usr/local/bin/
COPY --from=runtime /usr/share/doc/dockur-macos/ /usr/share/doc/dockur-macos/
COPY --from=runtime /usr/share/doc/qemu-system-common/ /usr/share/doc/qemu-system-common/
COPY --from=runtime /usr/share/doc/qemu-system-x86/ /usr/share/doc/qemu-system-x86/
COPY --from=runtime /usr/share/doc/qemu-utils/ /usr/share/doc/qemu-utils/
COPY --from=runtime /usr/share/doc/seabios/ /usr/share/doc/seabios/
COPY --from=runtime /usr/share/OVMF/ /usr/share/OVMF/
COPY --from=runtime /usr/share/ovmf/ /usr/share/ovmf/
COPY --from=runtime /usr/share/qemu/ /usr/share/qemu/
COPY --from=runtime /usr/share/seabios/ /usr/share/seabios/
COPY --from=runtime /usr/lib/x86_64-linux-gnu/libspice-server.so.1.15.0 /usr/lib/x86_64-linux-gnu/libvirglrenderer.so.1.11.0 /usr/local/lib/
COPY --from=runtime /usr/share/doc/qemu-render/ /usr/share/doc/qemu-render/
COPY --from=runtime /var/www/ /var/www/

COPY --chmod=755 start.sh /usr/local/bin/start-macos
COPY --chmod=755 console.sh health.sh /usr/local/lib/macos/
COPY --chown=1000:1000 --chmod=755 services/ /etc/service/
COPY patches/ /tmp/patches/
RUN for patch_file in /tmp/patches/*.patch; do \
        patch --batch --directory=/ --fuzz=0 --strip=1 < "$patch_file" || exit 1; \
    done \
    && rm -rf /tmp/patches
RUN ldconfig \
    && mkdir -p /storage \
    && qemu-system-x86_64 -device reims-vgpu-pci,help >/dev/null \
    && LD_BIND_NOW=1 qemu-system-x86_64 --version \
    && command -v vncviewer \
    && command -v air-dis aria2c dnsmasq ipcalc mformat nc pactl sfdisk xar xmlstarlet xxd \
    && qemu-system-x86_64 -audio driver=help 2>&1 | grep -qx alsa \
    && ! ldd /usr/bin/qemu-system-x86_64 /usr/bin/qemu-img /usr/local/bin/air-dis | grep 'not found' \
    && bash -n /usr/local/bin/start-macos /usr/local/lib/macos/*.sh /etc/service/macos-console/run \
    && python3 -c 'import selkies, pixelflux, pcmflux'

ENV AUDIO=N \
    CPU_CORES=4 \
    DISK_SIZE=64G \
    GPU=Y \
    NETWORK=slirp \
    PASSWD="" \
    RAM_SIZE=4G \
    SELKIES_ENABLE_BASIC_AUTH=true \
    SELKIES_ENABLE_DUAL_MODE=false \
    SELKIES_MODE=websockets \
    SELKIES_WAYLAND=false \
    TIMEOUT=110 \
    VERSION=15 \
    WEB=N
LABEL org.opencontainers.image.source="https://github.com/maxexcloo/images"
EXPOSE 8080
VOLUME /storage
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 CMD /usr/local/lib/macos/health.sh
ENTRYPOINT ["/usr/bin/tini", "-s", "--", "/usr/local/bin/start-macos"]
