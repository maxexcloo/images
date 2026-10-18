# Images

Pinned upstream applications packaged for personal infrastructure. Active builds publish
Atvloadly, BetterBench, ComfyUI ROCm, Gatus/Tailscale and macOS under `ghcr.io/maxexcloo`.
ComfyUI ROCm and macOS support AMD64; other active recipes support AMD64 and ARM64.

## Images

| Image           | Upstream                                                          | Runtime                                                                                                  |
| --------------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Atvloadly       | [bitxeno/atvloadly](https://github.com/bitxeno/atvloadly)         | Root service on localhost port 5533; mount persistent data at `/data`; host networking for LAN discovery |
| BetterBench     | [GGZ14/BetterBench](https://github.com/GGZ14/BetterBench)         | Non-root CLI; mount writable results at `/data`                                                          |
| ComfyUI ROCm    | [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI)         | AMD64 ROCm runtime; deployments own GPU allocation, models and persisted state                           |
| Gatus/Tailscale | [twin/gatus](https://github.com/twin/gatus)                       | Reusable binaries; deployments add monitoring configuration and startup                                  |
| macOS           | [steelbrain/reims-vgpu](https://github.com/steelbrain/reims-vgpu) | AMD64 KVM VM with native Reims graphics and Selkies HTTPS streaming on port 8080; persist `/storage`     |

Each recipe owns a Dockerfile and `source.json` with the upstream repository.
Recipes built from an upstream release or source specify its reference once; recipes
that fetch source also pin its commit. Builds receive the reference as
`UPSTREAM_REFERENCE`, which selects matching upstream image tags.
Recipes reuse upstream images where available
and fetch source only when needed. This repository keeps packaging, runtime
support and local `patches/`.
The generic builder in `.github/scripts/` discovers recipes from `source.json`.
Deployment repositories own credentials, configuration and persistent data.

## Development

Install the [shared Mise configuration](https://github.com/maxexcloo/dotfiles#shared-tools--tasks)
before running local Mise tasks.

Install the tools and check repository configuration:

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

ComfyUI uses the upstream ROCm base and its Python installation.
Verify ComfyUI GPU compatibility on the target ROCm host before deploying a new
image; its base tag floats. Its saved core, models and state remain owned by the deployment.
Gatus/Tailscale combines binaries from upstream images; deployments supply
startup and monitoring configuration.

The [macOS recipe](macos/README.md) includes a Compose example for Linux and
TrueNAS Docker Apps. It requires host KVM and GPU access, downloads macOS at
runtime and keeps installation state outside the image. Reims' native window
renders into Selkies' GPU-backed desktop; no host desktop or streaming service is
required.

## Publishing

Pull requests build changed recipes on their configured architectures without publishing.
Shared pipeline changes rebuild all recipes; metadata-only changes validate configuration
and skip image builds. Required checks always report.
Publishing runs on the same branch are serialised. Outdated manual runs on `main`
skip builds; manual runs of its current revision can rebuild selected images.
Outdated push runs fail before building so they cannot advance the successful
publication baseline.
Runtime changes and manual runs on `main` publish verified architecture images, then assemble
multi-architecture manifests. Manual runs accept an `image` recipe name, or `all`.
Tags include `latest`, `sha-<build-commit>`, the upstream release reference
(for example `v5.37.0`) for recipes that specify one, and
`source-<upstream-commit>` for recipes that fetch source. Release tags move when
packaging changes rebuild the same upstream release. Revision labels record the
packaging commit; recipes that fetch source record their upstream reference as the
image version. Published images include provenance and SBOMs.
Pin deployed images by release or `sha-` tag.

The repository needs Write access under each existing GHCR package's
**Settings → Manage Actions Access**. Publishing uses `GITHUB_TOKEN`.

## Dependencies

Preview updates, then apply reviewed changes. `--labels` selects one group:
`group:actions`, `group:docker`, `group:git` or `group:python`.

```sh
mise run dependencies:check
mise run dependencies:update --labels group:docker
```
