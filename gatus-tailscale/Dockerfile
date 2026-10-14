# syntax=docker/dockerfile:1
FROM golang:1.27.2-alpine AS gatus
WORKDIR /source
COPY --from=upstream / /source
# Preserve the application release while applying fixes to its dependencies.
RUN go get golang.org/x/image@v0.45.0 golang.org/x/net@v0.60.0 google.golang.org/grpc@v1.83.2
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 go build -o /gatus .

FROM golang:1.27.2-alpine AS tailscale
ARG TAILSCALE_REFERENCE=v1.104.1
ARG TAILSCALE_REVISION=9a522a9786c97eb7910c01ccb7bd66557b04c910
WORKDIR /source
ADD https://github.com/tailscale/tailscale.git#${TAILSCALE_REVISION} /source
RUN go get golang.org/x/crypto@v0.57.0 golang.org/x/image@v0.45.0 golang.org/x/net@v0.60.0
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 go build -ldflags="-X tailscale.com/version.longStamp=${TAILSCALE_REFERENCE#v} -X tailscale.com/version.shortStamp=${TAILSCALE_REFERENCE#v} -X tailscale.com/version.gitCommitStamp=${TAILSCALE_REVISION}" -o /tailscale ./cmd/tailscale \
    && CGO_ENABLED=0 go build -ldflags="-X tailscale.com/version.longStamp=${TAILSCALE_REFERENCE#v} -X tailscale.com/version.shortStamp=${TAILSCALE_REFERENCE#v} -X tailscale.com/version.gitCommitStamp=${TAILSCALE_REVISION}" -o /tailscaled ./cmd/tailscaled

FROM alpine:3.24.2 AS runtime
RUN apk add --no-cache ca-certificates iptables ip6tables \
    && apk upgrade --no-cache \
    && mkdir -p /var/cache/tailscale /var/lib/tailscale /var/run/tailscale
WORKDIR /app
COPY --from=gatus /gatus gatus
COPY --from=tailscale /tailscaled tailscaled
COPY --from=tailscale /tailscale tailscale
ENV GATUS_CONFIG_PATH=/app/config
EXPOSE 8080
ENTRYPOINT ["/app/gatus"]
