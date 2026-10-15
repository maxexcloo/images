# syntax=docker/dockerfile:1
FROM docker.io/twinproduction/gatus:v5.37.0@sha256:094eb186e55235db367e90e9d56140e5897b7044c41de23cde4cc18e6da1242e AS gatus
FROM docker.io/tailscale/tailscale:v1.104.1@sha256:87c55d6be56ad85b3d8bceca5f87f73de288c609131460dd1be1874c250cc41d AS tailscale

FROM alpine:3.24.2 AS runtime
RUN apk add --no-cache ca-certificates iptables ip6tables \
    && mkdir -p /var/cache/tailscale /var/lib/tailscale /var/run/tailscale
WORKDIR /app
COPY --from=gatus /gatus gatus
COPY --from=tailscale /usr/local/bin/tailscaled tailscaled
COPY --from=tailscale /usr/local/bin/tailscale tailscale
ENV GATUS_CONFIG_PATH=/app/config
EXPOSE 8080
ENTRYPOINT ["/app/gatus"]
