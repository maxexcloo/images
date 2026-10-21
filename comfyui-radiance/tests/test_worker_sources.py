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
        paths = [source["path"] for source in sources]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(paths.count("comfyui/upstream/ComfyUI"), 1)

    def test_worker_build_has_no_private_source_context(self):
        source = json.loads((ROOT / "source.json").read_text())
        self.assertFalse(source.get("private", False))
        self.assertNotIn("revision", source)
        self.assertNotIn("--from=upstream", (ROOT / "Dockerfile").read_text())
