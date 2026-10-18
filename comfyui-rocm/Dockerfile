# syntax=docker/dockerfile:1
FROM docker.io/yanwk/comfyui-boot:rocm

ARG UPSTREAM_REFERENCE
ARG UPSTREAM_REVISION

# Preserve the base image’s support for system pip installs.
RUN python3 -c 'import pathlib, sysconfig; pathlib.Path(sysconfig.get_path("stdlib"), "EXTERNALLY-MANAGED").unlink(missing_ok=True)'

RUN git -C /default-comfyui-bundle/ComfyUI fetch --depth 1 origin "$UPSTREAM_REVISION" \
    && git -C /default-comfyui-bundle/ComfyUI checkout --detach "$UPSTREAM_REVISION" \
    && PIP_USER=false python3 -m pip install --no-cache-dir --requirement /default-comfyui-bundle/ComfyUI/requirements.txt

# The ROCm torch build remains owned by the base image.
RUN PIP_USER=false python3 -m pip install --no-cache-dir fsspec==2026.9.0 peft==0.21.2 rotary_embedding_torch==0.9.1
LABEL io.excloo.comfyui.version="$UPSTREAM_REFERENCE"
