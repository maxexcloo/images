ARG UPSTREAM_REFERENCE
FROM golang:1.26.9-bookworm AS source
ARG UPSTREAM_REFERENCE
WORKDIR /source
COPY --from=upstream / /source
COPY patches/ /tmp/patches/
RUN git apply /tmp/patches/*.patch

FROM node:24.15.0-bookworm-slim AS frontend
WORKDIR /source/web/static
COPY --from=source /source /source
RUN --mount=type=cache,target=/root/.npm npm ci && npm test && npm run build

FROM source AS backend
WORKDIR /source
COPY --from=frontend /source/web/static/dist web/static/dist
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    go test ./internal/manager ./internal/service \
    && go build -ldflags="-extldflags=-static -linkmode=external -X github.com/bitxeno/atvloadly/internal/app/build.Version=${UPSTREAM_REFERENCE} -X github.com/bitxeno/atvloadly/internal/app/build.Mode=production" -o /atvloadly -tags netgo,osusergo .

FROM bitxeno/atvloadly:${UPSTREAM_REFERENCE}
ENV SERVICE_PORT=5533
LABEL org.opencontainers.image.source="https://github.com/maxexcloo/images"
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
