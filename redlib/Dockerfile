# syntax=docker/dockerfile:1
FROM rust:1.99.1-slim-trixie AS build
RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential cmake git libclang-dev perl pkg-config \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /source
COPY --from=upstream / /source/
# Upstream integration tests contact Reddit and depend on its current access policy.
RUN cargo test --release --locked --lib -- \
        --skip client::tests --skip oauth::tests --skip subreddit::tests \
        --skip user::tests --skip test_fetching \
    && cargo build --release --locked --bin redlib

FROM debian:13-slim
RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates libgcc-s1 libstdc++6 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --no-create-home --uid 1000 redlib
COPY --from=build /source/target/release/redlib /usr/local/bin/redlib
USER redlib
EXPOSE 8080
CMD ["redlib"]
