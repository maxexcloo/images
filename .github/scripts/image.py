#!/usr/bin/env python3
"""Build active image recipes using pinned upstream contexts."""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def images():
    return sorted(path.parent.name for path in ROOT.glob("*/source.json"))


def run(*command):
    subprocess.run(command, check=True, cwd=ROOT)


def source(name):
    if name not in images():
        raise ValueError(f"Unknown image: {name}")
    data = json.loads((ROOT / name / "source.json").read_text())
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", data["repository"]):
        raise ValueError(f"Invalid upstream repository for {name}")
    if not re.fullmatch(r"[0-9a-f]{40}", data["revision"]):
        raise ValueError(f"Invalid pinned revision for {name}")
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
        ".gitignore",
        ".mise.toml",
        "AGENTS.md",
        "ARCHITECTURE.md",
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


def results_succeeded(prepare, build, publish, required, publishing):
    if (
        prepare != "success"
        or required not in {"true", "false"}
        or publishing not in {"true", "false"}
    ):
        return False
    expected_build = "success" if required == "true" else "skipped"
    expected_publish = (
        "success" if required == "true" and publishing == "true" else "skipped"
    )
    return build == expected_build and publish == expected_publish


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["build", "lock", "matrix", "verify"])
    parser.add_argument("image", default="all", nargs="?")
    parser.add_argument("--changed-from")
    parser.add_argument("--platform")
    parser.add_argument("--tag")
    args = parser.parse_args()
    if args.action == "verify":
        if not results_succeeded(
            *(
                os.environ.get(name, "")
                for name in (
                    "PREPARE_RESULT",
                    "BUILD_RESULT",
                    "PUBLISH_RESULT",
                    "BUILD_REQUIRED",
                    "PUBLISH_REQUIRED",
                )
            )
        ):
            raise SystemExit(
                "Required image preparation, build or publishing did not succeed"
            )
        return
    if args.action == "matrix":
        changed_files = None
        if args.changed_from and args.changed_from != "0" * 40:
            changed_files = subprocess.check_output(
                [
                    "git",
                    "diff",
                    "--name-only",
                    "--no-renames",
                    args.changed_from,
                    "HEAD",
                ],
                cwd=ROOT,
                text=True,
            ).splitlines()
        print(json.dumps(matrix(args.image, changed_files)))
        return
    selected = images() if args.image == "all" else [args.image]
    if args.tag and len(selected) != 1:
        parser.error("--tag requires a single image")
    platform = args.platform
    if args.action == "build" and platform is None:
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
        if args.action == "lock":
            if name != "betterbench":
                parser.error("Only BetterBench has a local dependency lockfile")
            with tempfile.TemporaryDirectory(prefix="images-source-") as temporary:
                subprocess.run(["git", "init", temporary], check=True)
                subprocess.run([
                    "git", "-C", temporary, "fetch", "--depth", "1",
                    f"https://github.com/{data['repository']}.git", data["revision"],
                ], check=True)
                subprocess.run([
                    "git", "-C", temporary, "checkout", "--detach", "FETCH_HEAD",
                ], check=True)
                shutil.copyfile(ROOT / name / "uv.lock", Path(temporary) / "uv.lock")
                run("uv", "lock", "--directory", temporary, "--python", sys.executable)
                shutil.copyfile(Path(temporary) / "uv.lock", ROOT / name / "uv.lock")
            continue
        tag = args.tag or f"images-{name}:test"
        if args.action == "build":
            command = [
                "docker", "buildx", "build",
                "--build-arg", f"UPSTREAM_REFERENCE={data['reference']}",
                "--build-arg", f"UPSTREAM_REVISION={data['revision']}",
                "--build-context",
                f"upstream=https://github.com/{data['repository']}.git#{data['revision']}",
                "--load",
            ]
            if args.platform:
                command.extend(["--platform", args.platform])
            command.extend(["--tag", tag, name])
            run(*command)


if __name__ == "__main__":
    main()
