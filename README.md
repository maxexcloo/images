# Images

Container images for my own infrastructure, built from pinned upstream
applications and published under `ghcr.io/maxexcloo`.

## Images

| Image       | Upstream                                                                                    | Runtime                                                                                                                               |
| ----------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Atvloadly   | [bitxeno/atvloadly](https://github.com/bitxeno/atvloadly)                                   | Root service on port 5533, localhost unless `LISTEN_ADDR` is set; mount persistent data at `/data`; host networking for LAN discovery |
| BetterBench | [GGZ14/BetterBench](https://github.com/GGZ14/BetterBench)                                   | Non-root CLI; mount writable results at `/data`                                                                                       |
| macOS       | [steelbrain/reims-vgpu](https://github.com/steelbrain/reims-vgpu)                           | AMD64 KVM VM with native Reims graphics and Selkies HTTPS streaming on port 8080; persist `/storage`                                  |
| TRCC        | [Lexonight1/thermalright-trcc-linux](https://github.com/Lexonight1/thermalright-trcc-linux) | Headless cooler daemon; mount writable `/data`, host `/sys` read-only and `/dev/bus/usb` with device access                           |

Atvloadly also needs `seccomp=unconfined` for the upstream signing tools.
TRCC stores its configuration at `/data/.trcc/trcc.json`.

The [macOS guide](macos/README.md) covers Linux and TrueNAS setup.

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

## Publishing

Pushes to `main` publish changed recipes. To rebuild manually, run the
[Container workflow](.github/workflows/container.yaml) on `main` with `image` set
to a recipe name or `all`.

Tags include `latest`, `sha-<build-commit>` and, for recipes that set an
upstream release, `<release>-<workflow-run-number>` (for example `v1.2.3-42`).
Only `latest` moves. Pin deployed images by release or `sha-` tag.

The repository needs Write access under **Settings → Manage Actions Access** for
each existing GHCR package. Publishing uses `GITHUB_TOKEN`.
