# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.13.0 AS uv
FROM python:3.15.0-slim-bookworm AS build

COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
WORKDIR /app
COPY --from=upstream / /app/
COPY uv.lock ./
RUN uv sync --extra dev --locked --no-editable \
    && uv run --extra dev --locked pytest -q \
    && uv sync --locked --no-dev --no-editable

FROM python:3.15.0-slim-bookworm AS runtime

ENV BETTERBENCH_HOME=/data \
    BETTERBENCH_NO_UPDATE_CHECK=1 \
    PATH=/app/.venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY --from=build /app/.venv /app/.venv
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update --error-on=any \
    && apt-get upgrade --no-install-recommends -y \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /usr/local/lib/python*/ensurepip /usr/local/lib/python*/site-packages/pip* \
    && rm -f /usr/local/bin/pip* \
    && useradd --create-home --uid 1000 betterbench \
    && mkdir /data && chown betterbench:betterbench /data

USER betterbench
WORKDIR /data
ENTRYPOINT ["betterbench"]
CMD ["--help"]
