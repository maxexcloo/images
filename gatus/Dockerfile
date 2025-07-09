FROM alpine
RUN apk update && apk add ca-certificates ip6tables iptables supervisor && rm -rf /var/cache/apk/*
RUN mkdir -p /app /var/cache/tailscale /var/lib/tailscale /var/run/tailscale
COPY --from=tailscale/tailscale /usr/local/bin/tailscale /usr/local/bin/tailscale
COPY --from=tailscale/tailscale /usr/local/bin/tailscaled /usr/local/bin/tailscaled
COPY --from=twinproduction/gatus /gatus /app/gatus
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
ENTRYPOINT ["/usr/bin/supervisord", "-c", "/app/supervisord.conf"]
EXPOSE 8080
