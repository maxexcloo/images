# syntax=docker/dockerfile:1
ARG STUDIO_IMAGE=ghcr.io/maxexcloo/studio:0.38.0
FROM ${STUDIO_IMAGE} AS studio
FROM docker.io/stilldeadcode/radiance:1.10.0 AS radiance
FROM docker.io/yanwk/comfyui-boot:rocm-20261019

ARG STUDIO_IMAGE
ARG UPSTREAM_REFERENCE
ENV PIP_USER=false
COPY --from=radiance /opt/radiance /opt/radiance
COPY --from=radiance /lib64/ld-linux-x86-64.so.2 /opt/radiance/runtime/ld-linux-x86-64.so.2
COPY --from=radiance /usr/lib/x86_64-linux-gnu /opt/radiance/runtime/lib
RUN python3 -c 'import pathlib, sysconfig; pathlib.Path(sysconfig.get_path("stdlib"), "EXTERNALLY-MANAGED").unlink(missing_ok=True)' \
    && PIP_USER=false python3 -m pip install --no-cache-dir fsspec==2026.9.0 peft==0.21.2 rotary_embedding_torch==0.9.1 \
    && rm -rf /root/ComfyUI
COPY --from=upstream / /root/ComfyUI/
COPY worker_image.py /opt/ai/worker_image.py
COPY sources.json /opt/ai/sources.json
RUN rm -rf /root/ComfyUI/custom_nodes \
    && python3 /opt/ai/worker_image.py /opt/ai/sources.json /root/ComfyUI
COPY custom_nodes/ /root/ComfyUI/custom_nodes/
COPY --from=studio /app/comfyui/studio_worker /root/ComfyUI/custom_nodes/studio_worker
COPY patch_minimax.py /opt/ai/patch_minimax.py
COPY entrypoint.sh /opt/ai/comfyui-entrypoint.sh
COPY gpu-lease.sh /opt/ai/gpu-lease.sh
RUN python3 /opt/ai/patch_minimax.py /root/ComfyUI \
    && python3 -c 'import importlib.util; p="/root/ComfyUI/custom_nodes/ai_lora_cache/validate.py"; s=importlib.util.spec_from_file_location("guard",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); m.validate("/root/ComfyUI")' \
    && python3 -m compileall -q /root/ComfyUI/custom_nodes/ai_radiance /root/ComfyUI/custom_nodes/studio_worker
LABEL io.excloo.comfyui.version="$UPSTREAM_REFERENCE"
LABEL io.excloo.studio.image="$STUDIO_IMAGE"
WORKDIR /root/ComfyUI
EXPOSE 8188
ENTRYPOINT ["/bin/sh", "/opt/ai/gpu-lease.sh"]
CMD ["bash", "/opt/ai/comfyui-entrypoint.sh"]
