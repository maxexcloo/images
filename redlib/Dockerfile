# syntax=docker/dockerfile:1
FROM rust:1.90.0-slim-bookworm AS certificates

FROM certificates AS build

RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update --error-on=any \
    && apt-get install --no-install-recommends -y build-essential cmake git libclang-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /redlib
COPY --from=upstream / /redlib/
ARG UPSTREAM_REVISION
ENV GIT_HASH=${UPSTREAM_REVISION}
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/usr/local/cargo/git \
    cargo build --bin redlib --locked --release

FROM ubuntu:24.04 AS runtime

COPY --from=certificates /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
RUN sed -i 's|http://|https://|g' /etc/apt/sources.list.d/ubuntu.sources \
    && apt-get update --error-on=any \
    && apt-get install --no-install-recommends -y ca-certificates curl libstdc++6 \
    && apt-get upgrade --no-install-recommends -y \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --no-create-home --uid 1000 redlib
COPY --from=build /redlib/target/release/redlib /usr/local/bin/redlib

USER redlib
EXPOSE 8080
HEALTHCHECK --interval=1m --timeout=3s CMD curl --fail --silent http://localhost:8080/settings > /dev/null || exit 1
ENTRYPOINT ["redlib"]
