"""Install the pinned ComfyUI extensions while building the worker image."""

import importlib.metadata
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def install(source, target):
    target = Path(target)
    sources = json.loads(Path(source).read_text())
    core = next(item for item in sources if item["path"] == "comfyui/upstream/ComfyUI")
    subprocess.run(
        ["git", "-C", str(target), "fetch", "--depth", "1", "origin", core["revision"]],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(target), "checkout", "--detach", core["revision"]], check=True
    )
    for item in sources:
        if not item["path"].startswith("comfyui/custom_nodes/"):
            continue
        destination = target / "custom_nodes" / Path(item["path"]).name
        subprocess.run(
            [
                "git",
                "clone",
                "--no-checkout",
                "--filter=blob:none",
                item["url"],
                str(destination),
            ],
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(destination),
                "fetch",
                "--depth",
                "1",
                "origin",
                item["revision"],
            ],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(destination), "checkout", "--detach", item["revision"]],
            check=True,
        )
        shutil.rmtree(destination / ".git")
    # Core and extension dependencies must retain the image's ROCm PyTorch installation.
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt") as constraints:
        for name in ["torch", "torchaudio", "torchvision"]:
            constraints.write(f"{name}=={importlib.metadata.version(name)}\n")
        constraints.flush()
        for requirements in [
            target / "requirements.txt",
            *sorted((target / "custom_nodes").glob("*/requirements.txt")),
        ]:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--no-cache-dir",
                    "--constraint",
                    constraints.name,
                    "--requirement",
                    str(requirements),
                ],
                check=True,
            )


if __name__ == "__main__":
    install(*sys.argv[1:])
