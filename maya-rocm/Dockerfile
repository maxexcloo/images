# syntax=docker/dockerfile:1
FROM docker.io/rocm/dev-ubuntu-26.04:10.1.0-full

ENV PATH=/opt/maya/.venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends build-essential python3-venv \
    && rm -rf /var/lib/apt/lists/*
COPY --from=upstream / /opt/maya/
WORKDIR /opt/maya
# Maya's installer owns its Python packages and llama.cpp pin; its HIP setup needs a GPU, so run its steps directly.
RUN python3 -m venv .venv \
    && .venv/bin/python -c "import setup; setup.pip_install(setup.PY_PACKAGES, 'Maya'); setup.get_llama_cpp()" \
    && cmake -S . -B build-hip -G Ninja -DCMAKE_BUILD_TYPE=Release \
        -DSTRATA_ENABLE_HIP=ON -DSTRATA_ENABLE_CUDA=OFF -DSTRATA_PREFILL_MMQ=ON -DSTRATA_NATIVE_EXPERTS=ON \
        -DSTRATA_BUILD_TESTS=OFF -DCMAKE_HIP_ARCHITECTURES=gfx1201 \
        -DCMAKE_HIP_COMPILER=/opt/rocm/llvm/bin/clang++ -DCMAKE_PREFIX_PATH=/opt/rocm \
        -DSTRATA_GGML_DIR=/opt/maya/third_party/llama.cpp \
    && cmake --build build-hip --target maya tune_hipblaslt -j 4
COPY gfx1201-glm-hipblaslt-100401.txt tools/hip/
CMD ["python", "serve/server.py", "--help"]
