# syntax=docker/dockerfile:1
ARG UPSTREAM_REFERENCE
FROM ghcr.io/twin/gatus:${UPSTREAM_REFERENCE} AS gatus
FROM docker.io/tailscale/tailscale:v1.102.5 AS tailscale
FROM alpine:3.24.2 AS runtime

RUN apk add --no-cache ca-certificates iptables ip6tables \
    && apk upgrade --no-cache \
    && mkdir -p /var/cache/tailscale /var/lib/tailscale /var/run/tailscale
WORKDIR /app
COPY --from=gatus /gatus gatus
COPY --from=tailscale /usr/local/bin/tailscaled tailscaled
COPY --from=tailscale /usr/local/bin/tailscale tailscale
COPY --from=upstream /LICENSE /usr/share/licenses/gatus/LICENSE
COPY licenses/tailscale/LICENSE /usr/share/licenses/tailscale/LICENSE
ENV GATUS_CONFIG_PATH=/app/config
EXPOSE 8080
ENTRYPOINT ["/app/gatus"]
