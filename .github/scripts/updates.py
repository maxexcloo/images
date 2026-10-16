"""Discover recipe Updatecli manifests."""

import argparse
import json
import re
import shlex
import subprocess
from pathlib import Path

from image import ROOT, images, source


def pin_target(path, key, sourceid):
    return {
        "kind": "json",
        "sourceid": sourceid,
        "spec": {"engine": "dasel/v3", "file": str(path), "key": key},
    }


def source_manifest(name, repository, reference, path):
    release = bool(re.fullmatch(r"v?\d+\.\d+\.\d+(?:[-+].*)?", reference))
    sources = {}
    targets = {"revision": pin_target(path, "revision", "revision")}
    if release:
        owner, project = repository.split("/")
        sources["version"] = {
            "kind": "githubrelease",
            "spec": {
                "owner": owner,
                "repository": project,
                "token": '{{ env "GITHUB_TOKEN" }}',
                "versionfilter": {"kind": "semver", "pattern": "*"},
            },
        }
        targets["reference"] = pin_target(path, "reference", "version")
    ref = '{{ source "version" }}' if release else reference
    namespace = "tags" if release else "heads"
    refs = f'"refs/{namespace}/$UPDATE_REFERENCE"'
    if release:
        refs += ' "refs/tags/$UPDATE_REFERENCE^{}"'
    sources["revision"] = {
        "kind": "shell",
        "spec": {
            "command": (
                "set -eu\n"
                f"revisions=$(git ls-remote --exit-code {shlex.quote('https://github.com/' + repository + '.git')} {refs})\n"
                'printf "%s\\n" "$revisions" | tail -n 1 | cut -f 1'
            ),
            "environments": [{"name": "UPDATE_REFERENCE", "value": ref}],
        },
    }
    return {
        "name": f"Update Git Source: {name}",
        "pipelineid": f"update-git-{name}",
        "labels": {"group": "git"},
        "sources": sources,
        "targets": targets,
    }


def manifests():
    for name in images():
        data = source(name)
        if "revision" in data:
            yield source_manifest(
                name, data["repository"], data["reference"], Path(name) / "source.json"
            )
        path = Path(name) / "Dockerfile"
        text = (ROOT / path).read_text()
        for package in sorted(set(re.findall(r"\b([\w.-]+)==[0-9][\w.+!-]*", text))):
            yield {
                "name": f"Update Python Package: {name}/{package}",
                "pipelineid": f"update-python-{name}-{package.replace('_', '-')}",
                "labels": {"group": "python"},
                "sources": {"version": {"kind": "pypi", "spec": {"name": package}}},
                "targets": {
                    "pin": {
                        "kind": "file",
                        "sourceid": "version",
                        "spec": {
                            "file": str(path),
                            "matchpattern": rf"({re.escape(package)}==)[0-9][\w.+!-]*",
                            "replacepattern": '${1}{{ source "version" }}',
                        },
                    }
                },
            }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    args.directory.mkdir(exist_ok=True, parents=True)
    for index, manifest in enumerate(manifests()):
        content = subprocess.check_output(
            ["yq", "--input-format=json", "--prettyPrint", "."],
            input=json.dumps(manifest),
            text=True,
        )
        (args.directory / f"{index:03}.yaml").write_text(content)


if __name__ == "__main__":
    main()
