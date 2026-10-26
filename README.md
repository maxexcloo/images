# Images

Container images for my own infrastructure, built from pinned upstream
applications. The active builds are Atvloadly, BetterBench, ComfyUI Radiance,
Gatus/Tailscale, macOS and Maya ROCm, published under `ghcr.io/maxexcloo`.
ComfyUI Radiance, macOS and Maya ROCm are AMD64 only; the others support AMD64
and ARM64.

## Images

| Image            | Upstream                                                          | Runtime                                                                                                                                                              |
| ---------------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Atvloadly        | [bitxeno/atvloadly](https://github.com/bitxeno/atvloadly)         | Root service on localhost port 5533; mount persistent data at `/data`; host networking for LAN discovery                                                             |
| BetterBench      | [GGZ14/BetterBench](https://github.com/GGZ14/BetterBench)         | Non-root CLI; mount writable results at `/data`                                                                                                                      |
| ComfyUI Radiance | [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI)         | Complete ComfyUI worker with [Radiance](https://codeberg.org/StillDeadcode/radiance), pinned extensions and the matching Studio node; mount models and runtime state |
| Gatus/Tailscale  | [twin/gatus](https://github.com/twin/gatus)                       | Reusable binaries; deployments add monitoring configuration and startup                                                                                              |
| macOS            | [steelbrain/reims-vgpu](https://github.com/steelbrain/reims-vgpu) | AMD64 KVM VM with native Reims graphics and Selkies HTTPS streaming on port 8080; persist `/storage`                                                                 |
| Maya ROCm        | [mw00/project-maya](https://github.com/mw00/project-maya)         | Maya's GLM-5.3-Flash engine and server for R9700 (`gfx1201`); deployments supply the server config, models, packs and runtime state                                  |

Each recipe has a Dockerfile and a `source.json` naming the upstream repository.
Recipes built from an upstream release or source set its reference once, and
recipes that fetch source also pin its commit. Builds get these as
`UPSTREAM_REPOSITORY`, `UPSTREAM_REFERENCE` and `UPSTREAM_REVISION`, and the
reference picks the matching upstream image tags. Recipes reuse upstream images
where they exist and only fetch source when they have to. This repository holds
the packaging, runtime support and local `patches/`. The generic builder in
`.github/scripts/` finds recipes from their `source.json`, where
`architectures` limits the build platforms and `"cache": false` keeps images
too large for the GitHub Actions cache from exporting to it. Credentials,
configuration and persistent data belong in the deployment repositories.

## Development

Install the [shared Mise configuration](https://github.com/maxexcloo/dotfiles#shared-tools--tasks)
before running local Mise tasks.

Check repository configuration:

```sh
mise run check
```

Build the active images with Docker and Buildx. Recipes that don't support the
host architecture are skipped:

```sh
mise run build
```

Build one image by recipe name:

```sh
mise exec -- python .github/scripts/image.py build atvloadly
```

Atvloadly includes patches for pairing completion and discovery refresh.
Application dependencies follow upstream, and local patches and overrides fix
functional problems that have actually shown up. Upstream browser and Go tests run during the build.
Deploying it needs host networking and `seccomp=unconfined` for the upstream
signing tools.

BetterBench has no upstream container image, so its minimal recipe installs the
upstream application and runs its tests. Dependency versions can change between
builds of the same source.

ComfyUI uses a dated upstream ROCm base and its Python installation. Check GPU
compatibility on the target ROCm host before deploying a new base version. The
pinned core, extensions and Python dependencies are packaged in ComfyUI Radiance;
deployments supply models and persistent state. Radiance has its own runtime
libraries inside the same worker image.
Maya ROCm builds Maya's HIP engine for the R9700 on AMD's ROCm development
image, with the Python packages and llama.cpp pin from Maya's own installer, so
dependency versions can change between builds of the same source. Maya's
shipped GLM hipBLASLt table matches an older hipBLASLt, so the recipe adds one
tuned on Bento for the base image's version. Retune it with the bundled
`build-hip/tune_hipblaslt` after a ROCm update. Verify it on Bento.
Gatus/Tailscale combines binaries from upstream images, and deployments add the
startup and monitoring configuration.

The [macOS recipe](macos/README.md) includes a Compose example for Linux and
TrueNAS Docker Apps. It needs host KVM and GPU access, downloads macOS at runtime
and keeps installation state outside the image. Both build stages share one
versioned Selkies base pin. Reims' native window renders into Selkies' GPU-backed
desktop, so the host doesn't need a desktop or streaming service.

## Publishing

Pull requests build changed recipes on their configured architectures without
publishing. Only changes inside a recipe's build context select that image;
shared pipeline and metadata changes run the checks alone. Checks and builds run
in parallel, and publishing waits for both. Required checks always report.

Pushes to `main` rebuild every recipe changed since the last successful push
run, so cancelled runs don't skip publication, and a delayed run never
overwrites a newer one. Without that baseline, every recipe is rebuilt. Manual
runs take an `image` recipe name or `all` and rebuild it on the current
revision. Verified per-architecture images are then assembled into
multi-architecture manifests.

Tags include `latest`, `sha-<build-commit>`, the upstream release reference
(for example `v5.37.0`) for recipes that set one, and `source-<upstream-commit>`
for recipes that fetch source. Release tags move when a packaging
change rebuilds the same upstream release. Revision labels record the packaging
commit, and recipes that fetch source record their upstream reference as the
image version. Published images include provenance and SBOMs. Pin deployed images
by release or `sha-` tag.

The repository needs Write access under **Settings → Manage Actions Access** for
each existing GHCR package. Publishing uses `GITHUB_TOKEN`.

## Dependencies

Renovate (`renovate.json5`) opens pull requests for actions, base images, Python
packages pinned in Dockerfiles and each `source.json` upstream. Release references
move to the latest GitHub release and its commit, and branch references follow
the branch's latest commit.

The shared image/video worker (`comfyui-radiance`) builds from its local recipe
context. Its core release and commit are owned by `comfyui-radiance/source.json`;
the reference supplies the published version tag and ComfyUI version label.
The current v0.42.0 reference pins a feature commit with native Fibo 2 support,
not the v0.42.0 release tag. Renovate release updates for ComfyUI are held because
the existing stable releases lack those nodes and the Fibo 2 encoder type. The
worker maintainer should remove the hold after pinning a stable release with
that support and verifying both generation and editing on Bento.
Worker extensions are pinned in `comfyui-radiance/sources.json`. Studio owns
the Studio worker, CLIProxyAPI and Radiance nodes in its `comfyui/` directory,
and the image copies them from the pinned Studio release, with the Radiance
runtime and Python dependencies. Deployment hosts provide models, scratch
mounts, environment settings and the GPU lease entrypoint.
