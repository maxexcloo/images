FROM alpine
RUN apk update && apk add ca-certificates ip6tables iptables && rm -rf /var/cache/apk/*
RUN mkdir -p /app /var/cache/tailscale /var/lib/tailscale /var/run/tailscale
COPY --from=tailscale/tailscale /usr/local/bin/tailscale /usr/local/bin/tailscale
COPY --from=tailscale/tailscale /usr/local/bin/tailscaled /usr/local/bin/tailscaled
COPY --from=twinproduction/gatus /gatus /app/gatus
COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh
ENTRYPOINT ["/app/run.sh"]
EXPOSE 8080
