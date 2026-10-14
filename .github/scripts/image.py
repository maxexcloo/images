#!/usr/bin/env python3
"""Build active image recipes using pinned upstream contexts."""

import argparse
import json
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["build", "lock", "matrix"])
    parser.add_argument("image", default="all", nargs="?")
    parser.add_argument("--platform")
    parser.add_argument("--tag")
    args = parser.parse_args()
    selected = images() if args.image == "all" else [args.image]
    if args.tag and len(selected) != 1:
        parser.error("--tag requires a single image")
    if args.action == "matrix":
        recipes = [dict(image=name, **source(name)) for name in selected]
        print(json.dumps({
            "include": recipes,
            "build": [
                {"architecture": architecture, "recipe": recipe}
                for recipe in recipes
                for architecture in recipe["architectures"]
            ],
        }))
        return
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
