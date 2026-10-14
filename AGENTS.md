# Project Guidance

## Build Ownership

- Active recipes have a `source.json`.
- Pin upstream source revisions. Keep application source in its upstream repository.
- Preserve upstream licences and include application licence metadata in published images.
- Build each recipe’s configured architectures on native runners; the default is AMD64 and ARM64. ComfyUI ROCm is AMD64 only. Test and scan each image before publishing.
- Keep existing GHCR package names. Publish only from `main`; pull requests only build and test.
- Keep source updates manual through local Updatecli review.

## Documentation

Update `README.md` and `ARCHITECTURE.md` when changing build behaviour. The existing architecture document is a project exception to the root Markdown convention.

## Verification

Run `mise run fmt` before committing and `mise run check` after recipe, configuration or workflow changes. Remote CI verifies both architectures and publishing; local checks verify supported recipes on the host architecture only. Verify ComfyUI ROCm on Bento; ARM64 local checks explicitly skip it.
