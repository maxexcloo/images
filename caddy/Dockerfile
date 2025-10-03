FROM caddy:builder AS builder
RUN xcaddy build \
    --with github.com/caddy-dns/acmedns \
    --with github.com/lucaslorentz/caddy-docker-proxy/v2 \
    --with github.com/tailscale/caddy-tailscale
FROM caddy
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
CMD ["caddy", "docker-proxy"]
