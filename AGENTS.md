# Project Guidance

## Build Ownership

- Active recipes have a `source.json`, which owns architecture overrides.
- Keep recipe-specific patches and patch helpers in that recipe's `patches/` directory.
- Prefer suitable upstream container images over custom builds. Keep local recipes and changes to the minimum needed for working deployments.
- Use upstream dependencies when the image works. Add local patches or dependency overrides only to fix demonstrated functional issues, not solely to address vulnerability scan findings.
- Keep existing GHCR package names.
- Keep `renovate.json5` managers generic: they discover every recipe's `source.json` pins.

## Verification

Run `mise run fmt` before committing and `mise run check` after recipe, configuration or workflow changes. Run `mise run build` after recipe changes to verify supported recipes on the host architecture, including their build-time tests. Verify macOS deployments as described in [`macos/README.md`](macos/README.md#verification).
