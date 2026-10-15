# Images

Pinned upstream applications packaged for personal infrastructure. Active builds publish
Atvloadly, BetterBench, ComfyUI ROCm, Gatus/Tailscale and Redlib under `ghcr.io/maxexcloo`.
ComfyUI ROCm supports AMD64; other active recipes support AMD64 and ARM64.

## Images

| Image           | Upstream                                                  | Runtime                                                                                                  |
| --------------- | --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Atvloadly       | [bitxeno/atvloadly](https://github.com/bitxeno/atvloadly) | Root service on localhost port 5533; mount persistent data at `/data`; host networking for LAN discovery |
| BetterBench     | [GGZ14/BetterBench](https://github.com/GGZ14/BetterBench) | Non-root CLI; mount writable results at `/data`                                                          |
| ComfyUI ROCm    | [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) | AMD64 ROCm runtime; AI owns GPU allocation, models and persisted state                                   |
| Gatus/Tailscale | [twin/gatus](https://github.com/twin/gatus)               | Reusable binaries; Flylab adds generated monitoring configuration and startup                            |
| Redlib          | [Nachtalb/redlib](https://github.com/Nachtalb/redlib)     | Non-root HTTP service on port 8080                                                                       |

Each recipe directory owns its Dockerfile and pinned `source.json`. Shared build
orchestration lives in `.github/scripts/`.
BetterBench also owns its Python dependency lockfile. Application source is fetched
as a named BuildKit context at the exact configured commit.

## Development

Docker with Buildx is required. Install the pinned tools and verify the host architecture.
Local checks explicitly skip recipes that do not support that architecture:

```sh
mise install
mise run check
```

Validate repository configuration without building images:

```sh
mise run validate
```

Build one image:

```sh
mise exec -- python .github/scripts/image.py build atvloadly
mise exec -- python .github/scripts/image.py build betterbench
mise exec -- python .github/scripts/image.py build gatus-tailscale
mise exec -- python .github/scripts/image.py build redlib
```

Atvloadly includes pairing completion and discovery refresh patches, plus pinned
security fixes for Go dependencies and updates to runtime OS packages. Browser
and Go regression tests run during its build. Deployment requires host networking and
`seccomp=unconfined` for the upstream signing tools.

BetterBench runs upstream tests during its image build. Redlib HTTP readiness
requires successful Reddit OAuth and belongs to live deployment verification.

Verify ComfyUI GPU compatibility on Bento before changing its image pin; its saved
core, models and separate Normal/NSFW state remain owned by AI.

## Publishing

Pull requests provide source review. Image builds and scans run after merging.
Pushes and manual runs on `main` publish verified architecture images, then assemble
multi-architecture manifests. Manual runs accept an `image` recipe name, or `all`.
Tags include `latest`, `sha-<build-commit>` and
`source-<upstream-commit>`. Pin deployed images by digest.

The repository needs Write access under each existing GHCR package's
**Settings → Manage Actions Access**. Publishing uses `GITHUB_TOKEN`.
The package names stay unchanged when moving from the application forks.

Updatecli previews source and build dependency updates locally for manual review. When
BetterBench's dependency metadata changes, refresh its lockfile against the
new pinned source before merging:

```sh
mise exec -- python .github/scripts/image.py lock betterbench
```
