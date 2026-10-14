# Image Build Architecture

## Source Ownership

Active image directories contain packaging and verification files. `source.json`
records the upstream repository, reference and immutable commit. Builds receive
that revision as a named `upstream` context; application code is not copied into
this repository. Renovate proposes revision updates for manual review.

BetterBench uses the upstream application and a local frozen Python lockfile.
Redlib initially uses the upstream revision underlying the deployed native ARM
image, preserving its application code while moving build ownership.

## Verification & Publishing

A shared workflow discovers active recipes from their source files. Each recipe
builds on native AMD64 and ARM64 runners. BetterBench runs upstream tests inside
the build stage; each image then passes an isolated runtime smoke test and a
vulnerability scan. Only verified builds on `main` publish architecture tags.

A dependent publishing job assembles the two architecture digests for each image
into `latest`, build-commit and source-commit manifests. Existing package names
are retained. Provenance, SBOMs and licence metadata accompany published images.

Local Mise checks run the same recipes and smoke tests on the host architecture.
Remote CI establishes both architecture support and registry publishing.

## Legacy Recipes

Caddy and Gatus files and disabled workflows are retained for historical context.
They are excluded from active recipe discovery and Renovate updates.
