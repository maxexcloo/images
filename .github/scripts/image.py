#!/usr/bin/env python3
"""Build active image recipes using pinned upstream contexts."""

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def images():
    return sorted(path.parent.name for path in ROOT.glob("*/source.json"))


def source(name):
    if name not in images():
        raise ValueError(f"Unknown image: {name}")
    data = json.loads((ROOT / name / "source.json").read_text())
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", data["repository"]):
        raise ValueError(f"Invalid upstream repository for {name}")
    if "reference" in data or "revision" in data:
        if (
            not isinstance(data.get("reference"), str)
            or not data["reference"]
            or not re.fullmatch(r"[0-9a-f]{40}", data.get("revision", ""))
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
    metadata = {
        ".github/scripts/updates.py",
        ".gitignore",
        ".mise.toml",
        "AGENTS.md",
        "LICENSE",
        "README.md",
    }
    for path in changed_files:
        name = path.split("/", 1)[0]
        if name in names:
            selected.add(name)
        elif path not in metadata and not path.startswith((".updatecli.d/", "docs/")):
            return set(names)
    return selected


def matrix(image="all", changed_files=None):
    # Validate every recipe even when only metadata changed.
    catalogue = {name: dict(image=name, **source(name)) for name in images()}
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
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", "HEAD", revision], cwd=ROOT
    ).returncode == 0:
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
    parser.add_argument("--platform")
    parser.add_argument("--tag")
    args = parser.parse_args()
    if args.action == "matrix":
        changed_files = changes_since(args.changed_from)
        print(json.dumps(matrix(args.image, changed_files)))
        return
    selected = images() if args.image == "all" else [args.image]
    if args.tag and len(selected) != 1:
        parser.error("--tag requires a single image")
    platform = args.platform
    if platform is None:
        platform = subprocess.check_output([
            "docker", "info", "--format", "{{.OSType}}/{{.Architecture}}",
        ], text=True).strip()
        platform = platform.replace("/aarch64", "/arm64").replace("/x86_64", "/amd64")
    for name in selected:
        data = source(name)
        if platform and platform.split("/")[1] not in data["architectures"]:
            if args.image == "all" and not args.platform:
                print(f"Skipping {name}: {platform} is outside its configured architectures.")
                continue
            raise ValueError(f"{name} does not support {platform}")
        tag = args.tag or f"images-{name}:test"
        command = ["docker", "buildx", "build"]
        if "revision" in data:
            command.extend([
                "--build-arg", f"UPSTREAM_REFERENCE={data['reference']}",
                "--build-arg", f"UPSTREAM_REVISION={data['revision']}",
                "--build-context",
                f"upstream=https://github.com/{data['repository']}.git#{data['revision']}",
            ])
        command.append("--load")
        if args.platform:
            command.extend(["--platform", args.platform])
        command.extend(["--tag", tag, name])
        subprocess.run(command, check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
