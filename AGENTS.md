# Project Guidance

## Build Ownership

- Active recipes have a `source.json`.
- Pin upstream images by digest. Recipes that fetch source also pin its revision; image-only recipes follow Docker updates without an independent Git pin. Keep application source in its upstream repository.
- Prefer suitable upstream container images over custom builds. Keep local recipes and changes to the minimum needed for working deployments.
- Use upstream dependencies when the image works. Add local patches or dependency overrides only to fix demonstrated functional issues, not solely to address vulnerability scan findings.
- Build each recipe’s configured architectures on native runners. `source.json` owns architecture overrides; the builder defaults to AMD64 and ARM64. Run build-time tests where provided.
- Keep existing GHCR package names. Publish only from `main`; pull requests only build.
- Keep source updates manual through local Updatecli review.
- Prefer native Updatecli autodiscovery; use shared discovery only for unsupported recipe metadata. Name Updatecli policies and groups by the tool or ecosystem they manage.

## Documentation

Keep build behaviour and architecture documented concisely in `README.md`.

## Verification

Run `mise run fmt` before committing and `mise run check` after recipe, configuration or workflow changes. Local checks validate configuration and build selection without building images. Run `mise run build` after recipe changes to verify supported recipes on the host architecture. Remote CI verifies both architectures and publishing. Verify ComfyUI ROCm on Bento; ARM64 local builds explicitly skip it.
