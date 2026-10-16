# Images

Pinned upstream applications packaged for personal infrastructure. Active builds publish
Atvloadly, BetterBench, ComfyUI ROCm, Gatus/Tailscale and macOS under `ghcr.io/maxexcloo`.
ComfyUI ROCm and macOS support AMD64; other active recipes support AMD64 and ARM64.

## Images

| Image           | Upstream                                                  | Runtime                                                                                                  |
| --------------- | --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Atvloadly       | [bitxeno/atvloadly](https://github.com/bitxeno/atvloadly) | Root service on localhost port 5533; mount persistent data at `/data`; host networking for LAN discovery |
| BetterBench     | [GGZ14/BetterBench](https://github.com/GGZ14/BetterBench) | Non-root CLI; mount writable results at `/data`                                                          |
| ComfyUI ROCm    | [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) | AMD64 ROCm runtime; AI owns GPU allocation, models and persisted state                                   |
| Gatus/Tailscale | [twin/gatus](https://github.com/twin/gatus)               | Reusable binaries; Flylab adds generated monitoring configuration and startup                            |
| macOS          | [steelbrain/reims-vgpu](https://github.com/steelbrain/reims-vgpu)         | AMD64 KVM VM with native Reims graphics and Selkies HTTPS streaming on port 8080; persist `/storage`                |

Each recipe owns a Dockerfile and `source.json` with the upstream repository.
Recipes that fetch source also specify its reference and pinned commit.
Recipes reuse pinned upstream images where available
and fetch source only when needed. This repository keeps packaging, runtime
support and local `patches/`.
The generic builder in `.github/scripts/` discovers recipes from `source.json`.
Deployment repositories own credentials, configuration and persistent data.

## Development

Install the [shared Mise configuration](https://github.com/maxexcloo/dotfiles#shared-tools--tasks)
before running local Mise tasks.

Install the pinned tools and check repository configuration:

```sh
mise install
mise run check
```

Build active images with Docker and Buildx. Builds skip recipes that do not support
the host architecture:

```sh
mise run build
```

Build one image by recipe name:

```sh
mise exec -- python .github/scripts/image.py build atvloadly
```

Atvloadly includes pairing completion and discovery refresh patches. Application
dependencies follow upstream; local patches and overrides address demonstrated
functional issues. Upstream browser and Go tests run during its build. Deployment
requires host networking and
`seccomp=unconfined` for the upstream signing tools.

BetterBench has no upstream container image, so its minimal recipe installs the
upstream application and runs upstream tests; dependency versions can change
between builds of the same source.

ComfyUI uses the pinned upstream ROCm base and its Python installation.
Verify ComfyUI GPU compatibility on Bento before changing its image pin; its saved
core, models and separate Normal/NSFW state remain owned by AI.
Gatus/Tailscale combines binaries from
pinned upstream images; Flylab supplies startup and monitoring configuration.

The [macOS recipe](macos/README.md) includes a Compose example for Linux and
TrueNAS Docker Apps. It requires host KVM and GPU access, downloads macOS at
runtime and keeps installation state outside the image. A private local viewer
connects QEMU to Selkies; no host desktop or streaming service is required.

## Publishing

Pull requests build changed recipes on their configured architectures without publishing.
Shared pipeline changes rebuild all recipes; metadata-only changes validate configuration
and skip image builds. Required checks always report.
Runtime changes and manual runs on `main` publish verified architecture images, then assemble
multi-architecture manifests. Manual runs accept an `image` recipe name, or `all`.
Tags include `latest`, `sha-<build-commit>` and
`source-<upstream-commit>` for recipes that fetch source. Image-only recipes use the
packaging commit for revision metadata. Published images include provenance and SBOMs.
Pin deployed images by digest. Local builds cover the host architecture; CI
verifies every configured architecture on native runners and handles publishing.

The repository needs Write access under each existing GHCR package's
**Settings → Manage Actions Access**. Publishing uses `GITHUB_TOKEN`.

Preview updates with `mise run dependencies:check`; apply reviewed changes with
`mise run dependencies:update`. The shared updater discovers configured Git pins from `source.json`
and inline Python `package==version` pins from Dockerfiles. Versioned sources follow releases; branch sources follow
their configured branch. Prefer native Updatecli crawlers where available; they
handle base images and Actions. Actions use the crawler’s standard version selection
without per-action exceptions, so reviewed updates may replace major aliases with
full release tags.
Gatus/Tailscale follows its Docker image pins only. macOS builds the pinned Reims
revision with its upstream installer; that revision owns its QEMU, firmware and
helper dependencies. Set `GITHUB_TOKEN` for authenticated GitHub lookups.

Update groups follow their ecosystems: `actions`, `docker`, `git`, `mise` and `python`.
