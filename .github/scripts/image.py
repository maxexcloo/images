"""Build active image recipes using pinned upstream contexts."""

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = re.compile(r"v?\d+\.\d+\.\d+(?:[-+].*)?")


def images():
    return sorted(path.parent.name for path in ROOT.glob("*/source.json"))


def source(name):
    if name not in images():
        raise ValueError(f"Unknown image: {name}")
    data = json.loads((ROOT / name / "source.json").read_text())
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", data["repository"]):
        raise ValueError(f"Invalid upstream repository for {name}")
    # A release reference alone selects upstream image tags; a revision also fetches source.
    reference = data.get("reference", "")
    if ("reference" in data or "revision" in data) and not (
        isinstance(reference, str)
        and reference
        and (
            re.fullmatch(r"[0-9a-f]{40}", str(data["revision"]))
            if "revision" in data
            else RELEASE.fullmatch(reference)
        )
    ):
        raise ValueError(f"Invalid pinned source for {name}")
    architectures = data.setdefault("architectures", ["amd64", "arm64"])
    if (
        not isinstance(architectures, list)
        or not architectures
        or len(architectures) != len(set(architectures))
        or any(value not in {"amd64", "arm64"} for value in architectures)
    ):
        raise ValueError(f"Invalid architectures for {name}")
    return data


def affected_images(names, changed_files):
    selected = set()
    # Changes outside image build contexts validate configuration without rebuilding.
    metadata_names = {".gitignore", "AGENTS.md", "LICENSE", "README.md", "compose.yaml"}
    metadata_paths = {
        ".github/scripts/updates.py",
        ".mise.toml",
        "macos/verify-stream.sh",
    }
    for path in changed_files:
        name = path.split("/", 1)[0]
        if (
            path in metadata_paths
            or Path(path).name in metadata_names
            or path.startswith((".github/scripts/test_", ".updatecli.d/"))
        ):
            continue
        if name in names:
            selected.add(name)
        else:
            return set(names)
    return selected


def matrix(image="all", changed_files=None):
    # Validate every recipe even when only metadata changed.
    catalogue = {name: dict(image=name, **source(name)) for name in images()}
    for recipe in catalogue.values():
        reference = recipe.get("reference", "")
        recipe["version"] = reference if RELEASE.fullmatch(reference) else ""
    if image != "all" and image not in catalogue:
        raise ValueError(f"Unknown image: {image}")
    selected = set(catalogue) if image == "all" else {image}
    if changed_files is not None:
        selected &= affected_images(catalogue, changed_files)
    recipes = [catalogue[name] for name in sorted(selected)]
    return {
        "required": bool(recipes),
        "include": recipes,
        "build": [
            {"architecture": architecture, "recipe": recipe}
            for recipe in recipes
            for architecture in recipe["architectures"]
        ],
    }


def changes_since(revision):
    if not revision or revision == "0" * 40:
        return None
    # A delayed run must not overwrite a newer successful publication.
    if (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", "HEAD", revision],
            check=False,
            cwd=ROOT,
        ).returncode
        == 0
    ):
        return []
    return subprocess.check_output(
        ["git", "diff", "--name-only", "--no-renames", revision, "HEAD"],
        cwd=ROOT,
        text=True,
    ).splitlines()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["build", "matrix"])
    parser.add_argument("image", default="all", nargs="?")
    parser.add_argument("--changed-from")
    args = parser.parse_args()
    if args.action == "matrix":
        changed_files = changes_since(args.changed_from)
        print(json.dumps(matrix(args.image, changed_files)))
        return
    selected = images() if args.image == "all" else [args.image]
    platform = subprocess.check_output(
        ["docker", "info", "--format", "{{.OSType}}/{{.Architecture}}"], text=True
    ).strip()
    platform = platform.replace("/aarch64", "/arm64").replace("/x86_64", "/amd64")
    for name in selected:
        data = source(name)
        if platform.split("/")[1] not in data["architectures"]:
            if args.image == "all":
                print(
                    f"Skipping {name}: {platform} is outside its configured architectures."
                )
                continue
            raise ValueError(f"{name} does not support {platform}")
        command = [
            "docker",
            "buildx",
            "build",
            "--build-arg",
            f"UPSTREAM_REPOSITORY={data['repository']}",
        ]
        if "reference" in data:
            command.extend(["--build-arg", f"UPSTREAM_REFERENCE={data['reference']}"])
        if "revision" in data:
            command.extend(
                [
                    "--build-arg",
                    f"UPSTREAM_REVISION={data['revision']}",
                    "--build-context",
                    f"upstream=https://github.com/{data['repository']}.git#{data['revision']}",
                ]
            )
        command.extend(["--load", "--tag", f"images-{name}:test", name])
        subprocess.run(command, check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
