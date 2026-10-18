# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.13.1@sha256:4a1f3666816dafadd20ceb71eac9a7d56d7ef30279f7d64048519ab901ada336 AS uv
FROM python:3.15.0-slim-trixie@sha256:2da676046630d7bf14c6764ae1143dc7fa0377a53f94bf5a642f0b214aca5bce AS build

COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
WORKDIR /app
COPY --from=upstream / /app/
RUN uv sync --extra dev --no-editable \
    && .venv/bin/pytest -q \
    && uv sync --locked --no-dev --no-editable

FROM python:3.15.0-slim-trixie@sha256:2da676046630d7bf14c6764ae1143dc7fa0377a53f94bf5a642f0b214aca5bce AS runtime

ENV BETTERBENCH_HOME=/data \
    BETTERBENCH_NO_UPDATE_CHECK=1 \
    PATH=/app/.venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY --from=build /app/.venv /app/.venv
RUN useradd --no-create-home --uid 1000 betterbench \
    && mkdir /data && chown betterbench:betterbench /data

USER betterbench
WORKDIR /data
ENTRYPOINT ["betterbench"]
CMD ["--help"]
