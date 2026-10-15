#!/usr/bin/env python3
"""Discover recipe updates and run Updatecli for local review."""

import argparse
import re
import shlex
import subprocess
import tempfile
from pathlib import Path

from image import ROOT, images, source


def pin_target(path, key, sourceid):
    return {
        'kind': 'json', 'sourceid': sourceid,
        'spec': {'engine': 'dasel/v3', 'file': str(path), 'key': key},
    }


def source_manifest(name, repository, reference, path):
    release = bool(re.fullmatch(r'v?\d+\.\d+\.\d+(?:[-+].*)?', reference))
    sources = {}
    targets = {'revision': pin_target(path, 'revision', 'revision')}
    if release:
        owner, project = repository.split('/')
        sources['version'] = {
            'kind': 'githubrelease',
            'spec': {
                'owner': owner, 'repository': project,
                'token': '{{ env "GITHUB_TOKEN" }}',
                'versionfilter': {'kind': 'semver', 'pattern': '*'},
            },
        }
        targets['reference'] = pin_target(path, 'reference', 'version')
    ref = '{{ source "version" }}' if release else reference
    namespace = 'tags' if release else 'heads'
    refs = f'"refs/{namespace}/$UPDATE_REFERENCE"'
    if release:
        refs += ' "refs/tags/$UPDATE_REFERENCE^{}"'
    sources['revision'] = {
        'kind': 'shell',
        'spec': {
            'command': (
                'set -eu\n'
                f'revisions=$(git ls-remote --exit-code {shlex.quote("https://github.com/" + repository + ".git")} {refs})\n'
                'printf "%s\\n" "$revisions" | tail -n 1 | cut -f 1'
            ),
            'environments': [{'name': 'UPDATE_REFERENCE', 'value': ref}],
        },
    }
    return {
        'name': f'Update Git Source: {name}', 'pipelineid': f'update-git-{name}',
        'labels': {'group': 'git'}, 'sources': sources, 'targets': targets,
    }


def manifests():
    for name in images():
        data = source(name)
        yield source_manifest(name, data['repository'], data['reference'], Path(name) / 'source.json')
        path = Path(name) / 'Dockerfile'
        text = (ROOT / path).read_text()
        for package in sorted(set(re.findall(r'\b([\w.-]+)==[0-9][\w.+!-]*', text))):
            yield {
                'name': f'Update Python Package: {name}/{package}',
                'pipelineid': f'update-python-{name}-{package.replace("_", "-")}',
                'labels': {'group': 'python'},
                'sources': {'version': {'kind': 'pypi', 'spec': {'name': package}}},
                'targets': {'pin': {
                    'kind': 'file', 'sourceid': 'version',
                    'spec': {
                        'file': str(path),
                        'matchpattern': rf'({re.escape(package)}==)[0-9][\w.+!-]*',
                        'replacepattern': '${1}{{ source "version" }}',
                    },
                }},
            }


def yaml_lines(value, indent=0):
    """Emit the mappings, lists and strings used by generated manifests."""
    prefix = ' ' * indent
    if isinstance(value, dict):
        for key in sorted(value, key=lambda key: (isinstance(value[key], (dict, list)), key)):
            item = value[key]
            if isinstance(item, (dict, list)):
                yield f'{prefix}{key}:'
                yield from yaml_lines(item, indent + 2)
            elif '\n' in item:
                yield f'{prefix}{key}: |-'
                yield from (' ' * (indent + 2) + line for line in item.splitlines())
            else:
                yield f"{prefix}{key}: '" + item.replace("'", "''") + "'"
    else:
        for item in value:
            yield prefix + '-'
            yield from yaml_lines(item, indent + 2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['apply', 'diff', 'show', 'validate'], default='diff', nargs='?')
    args, extra = parser.parse_known_args()
    with tempfile.TemporaryDirectory(prefix='images-updates-') as temporary:
        for index, manifest in enumerate(manifests()):
            (Path(temporary) / f'{index:03}.yaml').write_text('\n'.join(yaml_lines(manifest)) + '\n')
        command = ['updatecli', 'manifest' if args.action in {'show', 'validate'} else 'pipeline', args.action]
        command += ['--config', '.updatecli.d', '--config', temporary]
        if args.action == 'validate':
            command += ['--disable-templating', '--strict']
        subprocess.run([*command, *extra], check=True, cwd=ROOT)


if __name__ == '__main__':
    main()
