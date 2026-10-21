"""Keep worker build inputs pinned independently of the host configuration."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WorkerSourcesTests(unittest.TestCase):
    def test_every_upstream_has_an_exact_git_revision(self):
        sources = json.loads((ROOT / "sources.json").read_text())
        self.assertTrue(sources)
        for source in sources:
            with self.subTest(path=source["path"]):
                self.assertRegex(source["revision"], r"^[0-9a-f]{40}$")
                self.assertTrue(source["url"].startswith("https://github.com/"))
                self.assertEqual(Path(source["path"]).parent, Path("custom_nodes"))
        paths = [source["path"] for source in sources]
        self.assertEqual(len(paths), len(set(paths)))

    def test_core_uses_pinned_upstream_context(self):
        source = json.loads((ROOT / "source.json").read_text())
        self.assertFalse(source.get("private", False))
        self.assertEqual(source["repository"], "Comfy-Org/ComfyUI")
        self.assertRegex(source["reference"], r"^v\d+\.\d+\.\d+$")
        self.assertRegex(source["revision"], r"^[0-9a-f]{40}$")
        self.assertIn(
            "COPY --from=upstream / /root/ComfyUI/", (ROOT / "Dockerfile").read_text()
        )
