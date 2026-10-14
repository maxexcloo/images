# syntax=docker/dockerfile:1
FROM docker.io/yanwk/comfyui-boot:rocm@sha256:b9573d1176e636380fbb6a5af008e54324fb7b06fb642c58932a6340ed6307a9

ARG UPSTREAM_REFERENCE
ARG UPSTREAM_REVISION
RUN git -C /default-comfyui-bundle/ComfyUI fetch --depth 1 origin "$UPSTREAM_REVISION" \
    && git -C /default-comfyui-bundle/ComfyUI checkout --detach "$UPSTREAM_REVISION" \
    && PIP_USER=false python3 -m pip install --no-cache-dir --requirement /default-comfyui-bundle/ComfyUI/requirements.txt

# The ROCm torch build remains owned by the pinned base image.
RUN PIP_USER=false python3 -m pip install --no-cache-dir fsspec==2026.6.0 peft==0.21.2 rotary_embedding_torch==0.9.1
COPY --from=upstream /LICENSE /usr/share/licenses/comfyui/LICENSE
LABEL io.excloo.comfyui.version="$UPSTREAM_REFERENCE"
