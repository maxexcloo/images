# syntax=docker/dockerfile:1
FROM golang:1.26.9-trixie@sha256:f06b7122f888680048afb247c4e5f49c0069eb6c4c1ccae0f3f4834527a8d22c AS source
ARG UPSTREAM_REFERENCE
WORKDIR /source
COPY --from=upstream / /source
COPY patches/ /tmp/patches/
RUN git apply /tmp/patches/*.patch

FROM node:24.15.0-trixie-slim@sha256:291be77873bc04731968cacf82f0fcef17cee8cf200c6b6951e2bcab41560eb7 AS frontend
WORKDIR /source/web/static
COPY --from=source /source /source
RUN --mount=type=cache,target=/root/.npm npm ci && npm test && npm run build

FROM source AS backend
WORKDIR /source
COPY --from=frontend /source/web/static/dist web/static/dist
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    go test ./internal/manager ./internal/service \
    && go build -ldflags="-extldflags=-static -linkmode=external -X github.com/bitxeno/atvloadly/internal/app/build.Version=${UPSTREAM_REFERENCE} -X github.com/bitxeno/atvloadly/internal/app/build.Mode=production" -o /atvloadly -tags netgo,osusergo .

FROM bitxeno/atvloadly:v0.6.2@sha256:777373b81714f79a7047ff6cd1a849ae7043566d689db699c4088bf62e7648e6
ENV SERVICE_PORT=5533
# The upstream image leaves /tmp unwritable by apt's unprivileged helper.
RUN chmod 1777 /tmp \
    && sed -i 's|http://|https://|g' /etc/apt/sources.list \
    && apt-get update -o APT::Update::Error-Mode=any \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
        avahi-daemon avahi-utils dbus \
    && rm -rf /var/lib/apt/lists/*
COPY config.yaml /keep/config.yaml
COPY --from=backend /atvloadly /usr/bin/atvloadly
COPY --chmod=755 start.sh /usr/local/bin/start-atvloadly
ENTRYPOINT ["/usr/local/bin/start-atvloadly"]
