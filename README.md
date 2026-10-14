# Images

Pinned upstream applications packaged for personal infrastructure. Active builds publish
Atvloadly, BetterBench, ComfyUI ROCm, Gatus/Tailscale and Redlib under `ghcr.io/maxexcloo`.
ComfyUI ROCm supports AMD64; other active recipes support AMD64 and ARM64.

## Images

| Image | Upstream | Runtime |
| --- | --- | --- |
| Atvloadly | [bitxeno/atvloadly](https://github.com/bitxeno/atvloadly) | Root service on localhost port 5533; mount persistent data at `/data`; host networking for LAN discovery |
| BetterBench | [GGZ14/BetterBench](https://github.com/GGZ14/BetterBench) | Non-root CLI; mount writable results at `/data` |
| ComfyUI ROCm | [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) | AMD64 ROCm runtime; AI owns GPU allocation, models and persisted state |
| Gatus/Tailscale | [twin/gatus](https://github.com/twin/gatus) | Reusable binaries; Flylab adds generated monitoring configuration and startup |
| Redlib | [Nachtalb/redlib](https://github.com/Nachtalb/redlib) | Non-root HTTP service on port 8080 |

Each directory owns its Dockerfile, smoke test and pinned `source.json`.
BetterBench also owns its Python dependency lockfile. Application source is fetched
as a named BuildKit context at the exact configured commit.

Caddy and Gatus recipes remain as legacy files. Their workflows are disabled;
this repository does not build or publish them.

## Development

Docker with Buildx is required. Install the pinned tools and verify the host architecture.
Local checks explicitly skip recipes that do not support that architecture:

```sh
mise install
mise run check
```

Build or test one image:

```sh
mise exec -- python scripts/image.py check atvloadly
mise exec -- python scripts/image.py check betterbench
mise exec -- python scripts/image.py check gatus-tailscale
mise exec -- python scripts/image.py check redlib
```

Atvloadly includes pairing completion and discovery refresh patches, plus pinned
security fixes for Go dependencies and updates to runtime OS packages. Browser
and Go regression tests run during its build. Its runtime smoke test checks the UI,
Avahi and D-Bus without LAN access. Deployment requires host networking and
`seccomp=unconfined` for the upstream signing tools.

BetterBench runs upstream tests during its image build. Smoke tests verify its
CLI, packaged corpus and writable results directory. Redlib smoke tests verify
its CLI version and the health-check executable without contacting Reddit. HTTP readiness
requires successful Reddit OAuth and belongs to live deployment verification.

ComfyUI smoke tests verify its source revision and ROCm runtime imports on native AMD64.
Verify GPU compatibility on Bento before changing its image pin; its saved core, models
and separate Normal/NSFW state remain owned by AI. The Gatus/Tailscale smoke test starts
Gatus with an isolated local endpoint and checks the Tailscale executable.

## Publishing

Pull requests build, test and scan each recipe’s configured architectures without publishing.
Pushes and manual runs on `main` publish verified architecture images, then assemble
multi-architecture manifests. Manual runs accept an `image` recipe name, or `all`.
Tags include `latest`, `sha-<build-commit>` and
`source-<upstream-commit>`. Pin deployed images by digest.

The repository needs Write access under each existing GHCR package's
**Settings → Manage Actions Access**. Publishing uses `GITHUB_TOKEN`.
The package names stay unchanged when moving from the application forks.

Renovate proposes source and build dependency updates for manual review. When
BetterBench's dependency metadata changes, refresh its lockfile against the
new pinned source before merging:

```sh
mise exec -- python scripts/image.py lock betterbench
```

## Licence

Build infrastructure uses AGPL-3.0; application sources retain their upstream
licences: Apache-2.0 for BetterBench and Gatus, BSD-3-Clause for Tailscale,
GPL-3.0 for ComfyUI, and AGPL-3.0-only for Atvloadly and Redlib.
