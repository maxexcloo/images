"""The worker starts immutable image code without seeding or replacing host state."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ENTRYPOINT = Path(__file__).resolve().parents[1] / "comfyui/entrypoint.sh"


class WorkerEntrypointTests(unittest.TestCase):
    def test_arguments_exit_status_and_media_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "main.py").write_text(
                "import json,sys\nprint(json.dumps(sys.argv[1:]))\nsys.exit(7)\n"
            )
            (root / "saved.png").write_bytes(b"existing media")
            result = subprocess.run(
                ["/bin/bash", str(ENTRYPOINT), "--disable-auto-launch"],
                check=False,
                env={
                    **os.environ,
                    "COMFYUI_ROOT": str(root),
                    "CLI_ARGS": "--cache-classic --disable-mmap",
                },
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 7, result.stderr)
            self.assertEqual(
                json.loads(result.stdout),
                [
                    "--listen",
                    "0.0.0.0",
                    "--port",
                    "8188",
                    "--cache-classic",
                    "--disable-mmap",
                    "--disable-auto-launch",
                ],
            )
            self.assertEqual((root / "saved.png").read_bytes(), b"existing media")
            self.assertEqual(
                sorted(p.name for p in root.iterdir()), ["main.py", "saved.png"]
            )
