# syntax=docker/dockerfile:1
# check=skip=InvalidDefaultArgInFrom
ARG UPSTREAM_REFERENCE
FROM caddy:${UPSTREAM_REFERENCE}-builder AS builder
ARG UPSTREAM_REFERENCE
# renovate: datasource=go depName=github.com/caddy-dns/cloudflare
ARG CLOUDFLARE_VERSION=v0.2.4
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    xcaddy build "v${UPSTREAM_REFERENCE}" --with "github.com/caddy-dns/cloudflare@${CLOUDFLARE_VERSION}"

FROM caddy:${UPSTREAM_REFERENCE}-alpine
ARG UPSTREAM_REFERENCE
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
RUN caddy version | grep -F "v${UPSTREAM_REFERENCE} " \
    && caddy list-modules | grep -Fx dns.providers.cloudflare
