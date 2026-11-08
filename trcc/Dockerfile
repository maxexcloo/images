# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.13 AS uv
FROM python:3.15.2-slim-trixie AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    QT_QPA_PLATFORM=offscreen
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        fonts-dejavu-core libdbus-1-3 libegl1 libfontconfig1 libfreetype6 libgl1 libglib2.0-0 libportaudio2 libudev1 libusb-1.0-0 libxkbcommon0 \
    && rm -rf /var/lib/apt/lists/*

FROM base AS build
COPY --from=uv /uv /usr/local/bin/uv
RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential libudev-dev libusb-1.0-0-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /source
COPY --from=upstream / /source/
RUN uv pip install --system '.[dev]' \
    && pytest -q -o addopts= tests/test_led_segment.py tests/test_led_send.py tests/test_led_settings_commands.py tests/test_settings_schema_migration.py \
    && uv venv /opt/venv \
    && uv pip install --python /opt/venv/bin/python .

FROM base AS runtime
ENV HOME=/data \
    PATH=/opt/venv/bin:$PATH
COPY --from=build /opt/venv /opt/venv
WORKDIR /data
ENTRYPOINT ["trcc"]
CMD ["daemon"]
