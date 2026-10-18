# syntax=docker/dockerfile:1
FROM golang:1.26.9-bookworm@sha256:d9c68c2c51161e12fd77e4c6320687c9cd86e1af1e3ad6e6cd63ff970641453c AS source
ARG UPSTREAM_REFERENCE
WORKDIR /source
COPY --from=upstream / /source
COPY patches/ /tmp/patches/
RUN git apply /tmp/patches/*.patch

FROM node:24.15.0-bookworm-slim@sha256:4e6b70dd6cbfc88c8157ba19aa3d9f9cce6ba4703576d55459e45efcbc9c5f5d AS frontend
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
