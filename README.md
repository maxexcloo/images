# Images

Container images for my own infrastructure, built from pinned upstream
applications. The active builds are Atvloadly, BetterBench, ComfyUI Radiance,
Gatus/Tailscale, macOS and Redlib, published under `ghcr.io/maxexcloo`.
ComfyUI Radiance and macOS are AMD64 only; the others support AMD64
and ARM64.

## Images

| Image            | Upstream                                                          | Runtime                                                                                                                                                              |
| ---------------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Atvloadly        | [bitxeno/atvloadly](https://github.com/bitxeno/atvloadly)         | Root service on localhost port 5533; mount persistent data at `/data`; host networking for LAN discovery                                                             |
| BetterBench      | [GGZ14/BetterBench](https://github.com/GGZ14/BetterBench)         | Non-root CLI; mount writable results at `/data`                                                                                                                      |
| ComfyUI Radiance | [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI)         | Complete ComfyUI worker with [Radiance](https://codeberg.org/StillDeadcode/radiance), pinned extensions and the matching Studio node; mount models and runtime state |
| Gatus/Tailscale  | [twin/gatus](https://github.com/twin/gatus)                       | Reusable binaries; deployments add monitoring configuration and startup                                                                                              |
| macOS            | [steelbrain/reims-vgpu](https://github.com/steelbrain/reims-vgpu) | AMD64 KVM VM with native Reims graphics and Selkies HTTPS streaming on port 8080; persist `/storage`                                                                 |
| Redlib           | [polak14/redlib](https://github.com/polak14/redlib)               | Non-root Reddit frontend on port 8080; built from source for AMD64 and ARM64                                                                                         |

Each recipe has a Dockerfile and a `source.json` naming the upstream repository.
Recipes built from an upstream release or source set its reference once, and
recipes that fetch source also pin its commit. Builds get these as
`UPSTREAM_REPOSITORY`, `UPSTREAM_REFERENCE` and `UPSTREAM_REVISION`, and the
reference picks the matching upstream image tags. Recipes reuse upstream images
where they exist and only fetch source when they have to. This repository holds
the packaging, runtime support and local `patches/`. The generic builder in
`.github/scripts/` finds recipes from their `source.json`. Credentials,
configuration and persistent data belong in the deployment repositories.

## Development

Install the [shared Mise configuration](https://github.com/maxexcloo/dotfiles#shared-tools--tasks)
before running local Mise tasks.

Install the tools and check repository configuration:

```sh
mise install
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
Gatus/Tailscale combines binaries from upstream images, and deployments add the
startup and monitoring configuration. Redlib builds the pinned fork from source
and runs its offline Rust tests during the build; deployments supply its configuration.

The [macOS recipe](macos/README.md) includes a Compose example for Linux and
TrueNAS Docker Apps. It needs host KVM and GPU access, downloads macOS at runtime
and keeps installation state outside the image. Both build stages share one
versioned Selkies base pin. Reims' native window renders into Selkies' GPU-backed
desktop, so the host doesn't need a desktop or streaming service.

## Publishing

Pull requests build changed recipes on their configured architectures without
publishing. Only changes inside a recipe's build context select that image. Shared
pipeline and metadata changes run configuration and unit checks without selecting
unrelated images. Use a manual run to rebuild selected images or every recipe
after a shared pipeline change. Required checks always report.

Publishing runs on the same branch run one at a time. Outdated manual runs on
`main` skip their builds, and manual runs of the current revision can rebuild
selected images. Outdated push runs fail before building so they can't move the
last successful publication forward. If that baseline has been lost from
rewritten history, every recipe is rebuilt. Runtime changes and manual runs on
`main` publish verified per-architecture images, then assemble multi-architecture
manifests. Manual runs take an `image` recipe name or `all`.

Tags include `latest`, `sha-<build-commit>`, the upstream release reference
(for example `v5.37.0`) for recipes that set one, and `source-<upstream-commit>`
for recipes that fetch source. Recipes without a reference combine their exact
base tags instead, final base first, for example `v0.41.0-radiance1.8.1`, and
Renovate's `loose` versioning orders them. Release tags move when a packaging
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

```sh
mise run dependencies:check
mise run dependencies:update
```

The shared image/video worker (`comfyui-radiance`) builds from its local recipe
context. Its core release and commit are owned by `comfyui-radiance/source.json`;
the reference supplies the published version tag and ComfyUI version label.
The current v0.42.0 reference pins a feature commit with native Fibo 2 support,
not the v0.42.0 release tag. Renovate release updates for ComfyUI are held because
the existing stable releases lack those nodes and the Fibo 2 encoder type. The
worker maintainer should remove the hold after pinning a stable release with
that support and verifying both generation and editing on Bento.
Worker extensions are pinned in `comfyui-radiance/sources.json`; its
CPU tests run with `mise run test:worker`. Local nodes share `custom_nodes/`,
and all worker tests live in `tests/` within the recipe; tests are excluded from
the Docker build context. The image includes its pinned Studio
node, Radiance runtime, custom nodes and Python dependencies. Deployment hosts
provide models, scratch mounts and environment settings.

The local extensions are `cliproxy` and `radiance`. LoRA loading uses the upstream
ComfyUI and rgthree nodes. ComfyUI caches the last LoRA per loader instance;
rgthree's Power LoRA Loader creates fresh instances and may reread weights.

CLIProxyAPI discovers advertised Grok image and video models from `/v1/models`,
cached for one minute. Set `CLIPROXYAPI_URL` and `CLIPROXYAPI_KEY` in the deployment.
Optional `CLIPROXYAPI_IMAGE_MODEL` and `CLIPROXYAPI_VIDEO_MODEL` select defaults;
otherwise the first advertised model of each kind is selected alphabetically.
Defaults must be advertised by that provider. Known request formats and limits
remain explicit because discovery does not publish their complete schemas. New
advertised variants use the standard endpoint format and provider resolution
defaults; an explicit resolution is passed through for the provider to validate.
Refresh the node's model list after provider changes. Discovery failure leaves
an empty selector and generation reports the provider error.

Cancelling a CLIProxyAPI job stops local waiting and discards late responses.
The provider may still finish or bill a submitted job; cancellation never
resubmits it. The unused seed control is removed, while saved API workflows may
still send it. Radiance workers share a single loopback endpoint definition.

[AI Control](https://github.com/maxexcloo/ai-control) owns its Docker image and
publishing workflow in its app repository. It continues to publish
`ghcr.io/maxexcloo/ai-control` independently of this repository.
