"""Reject changes to the upstream loader contract before installing the wrapper."""

import ast
import hashlib
import json
from pathlib import Path


def validate(root, targets=None):
    if targets is None:
        targets = json.loads(Path(__file__).with_name("targets.json").read_text())
    for filename, target in targets.items():
        source = (Path(root) / filename).read_text()
        parent = ast.parse(source)
        if target["class"]:
            parent = next(
                node
                for node in parent.body
                if isinstance(node, ast.ClassDef) and node.name == target["class"]
            )
        function = next(
            node
            for node in parent.body
            if isinstance(node, ast.FunctionDef) and node.name == target["function"]
        )
        digest = hashlib.sha256(
            ast.get_source_segment(source, function).encode()
        ).hexdigest()
        if digest != target["sha256"]:
            raise RuntimeError(
                f"LoRA cache target changed: {filename}:{target['function']}; review the loader contract"
            )
