# Project Guidance

## Build Ownership

- Active recipes have a `source.json`, which owns architecture overrides.
- Pin fetched source by revision. Keep application source in its upstream repository.
- Prefer suitable upstream container images over custom builds. Keep local recipes and changes to the minimum needed for working deployments.
- Use upstream dependencies when the image works. Add local patches or dependency overrides only to fix demonstrated functional issues, not solely to address vulnerability scan findings.
- Run build-time tests where provided.
- Keep existing GHCR package names.
- Keep `renovate.json5` managers generic: they discover every recipe's `source.json` pins and Dockerfile Python pins.

## Documentation

Keep build behaviour and architecture documented concisely in `README.md`.

## Verification

Run `mise run fmt` before committing and `mise run check` after recipe, configuration or workflow changes. Local checks validate configuration and build selection without building images. Run `mise run build` after recipe changes to verify supported recipes on the host architecture. Remote CI verifies configured architectures and publishing. Verify ComfyUI ROCm on Bento; ARM64 local builds explicitly skip it. Verify macOS deployments as described in [`macos/README.md`](macos/README.md#verification).
