# Image Build Architecture

## Source Ownership

Active image directories contain packaging and verification files. `source.json`
records the upstream repository, reference and immutable commit. Builds receive
that revision as a named `upstream` context; application code is not copied into
this repository. Updatecli previews revision updates locally for manual review.

Atvloadly packages upstream v0.6.2 with local pairing completion and discovery
refresh patches and a pinned Go dependency security patch. Runtime OS packages
receive available security updates. Browser and Go regression tests run in the build; its runtime
includes Avahi and D-Bus. Kubernetes deployment remains owned by kubelab.

BetterBench uses the upstream application and a local frozen Python lockfile.
Redlib uses the upstream revision underlying the deployed native ARM
image.

ComfyUI ROCm preserves AI’s pinned ROCm base, ComfyUI revision and additional
dependencies. AI consumes the published digest and retains all runtime configuration.
Gatus/Tailscale packages the upstream binaries; Flylab retains its credential-consuming
startup script and generated monitoring files in a thin deployment image.

## Verification & Publishing

Build orchestration lives in `.github/scripts/`.
A shared workflow discovers active recipes from their source files. Each recipe
builds on its configured native architectures; ComfyUI ROCm is AMD64 only. Manual runs can select one recipe;
pushes and pull requests verify all active recipes. BetterBench runs upstream tests inside
the build stage; each image then passes a vulnerability scan. Only verified builds
on `main` publish architecture tags.

A dependent publishing job assembles the configured architecture digests for each image
into `latest`, build-commit and source-commit manifests. Existing package names
are retained. Provenance and SBOMs accompany published images.

Local Mise checks run the same recipes on the host architecture.
Remote CI establishes both architecture support and registry publishing.
