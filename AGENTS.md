# Project Guidance

## Build Ownership

- Active recipes have a `source.json`.
- Pin upstream source revisions. Keep application source in its upstream repository.
- Prefer suitable upstream container images over custom builds. Keep local recipes and changes to the minimum needed for working deployments.
- Use upstream dependencies when the image works. Add local patches or dependency overrides only to fix demonstrated functional issues, not solely to address vulnerability scan findings.
- Build each recipe’s configured architectures on native runners; the default is AMD64 and ARM64. ComfyUI ROCm is AMD64 only. Run build-time tests where provided and scan each image before publishing.
- Keep existing GHCR package names. Publish only from `main`; pull requests only build and scan.
- Keep source updates manual through local Updatecli review.
- Prefer native Updatecli autodiscovery; use shared discovery only for unsupported recipe metadata. Name Updatecli policies and groups by the tool or ecosystem they manage.

## Documentation

Keep build behaviour and architecture documented concisely in `README.md`.

## Verification

Run `mise run fmt` before committing and `mise run check` after recipe, configuration or workflow changes. Remote CI verifies both architectures and publishing; local checks verify supported recipes on the host architecture only. Verify ComfyUI ROCm on Bento; ARM64 local checks explicitly skip it.
