# syntax=docker/dockerfile:1
# check=skip=InvalidDefaultArgInFrom
ARG UPSTREAM_REFERENCE
FROM docker.io/twinproduction/gatus:${UPSTREAM_REFERENCE} AS gatus
FROM docker.io/tailscale/tailscale:v1.104.2 AS tailscale

FROM alpine:3.24 AS runtime
RUN apk add --no-cache ca-certificates iptables ip6tables \
    && mkdir -p /var/cache/tailscale /var/lib/tailscale /var/run/tailscale
WORKDIR /app
COPY --from=gatus /gatus gatus
COPY --from=tailscale /usr/local/bin/tailscaled tailscaled
COPY --from=tailscale /usr/local/bin/tailscale tailscale
ENV GATUS_CONFIG_PATH=/app/config
EXPOSE 8080
ENTRYPOINT ["/app/gatus"]
