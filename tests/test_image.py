"""Exercise recipe selection and publication baselines."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".github" / "scripts"))

import image
from image import changes_since, matrix


class MatrixTests(unittest.TestCase):
    def test_metadata_only_changes_need_no_images(self):
        result = matrix(
            changed_files=[
                "README.md",
                ".mise.toml",
                "renovate.json5",
                "tests/test_image.py",
                "macos/README.md",
                "macos/compose.yaml",
                "macos/verify-stream.sh",
            ]
        )
        self.assertFalse(result["required"])
        self.assertEqual(result["build"], [])
        self.assertEqual(result["include"], [])

    def test_one_recipe_selects_all_its_architectures(self):
        for path in ["gatus-tailscale/Dockerfile", "gatus-tailscale/source.json"]:
            with self.subTest(path=path):
                result = matrix(changed_files=[path])
                self.assertEqual(
                    [recipe["image"] for recipe in result["include"]],
                    ["gatus-tailscale"],
                )
                self.assertEqual(
                    {build["architecture"] for build in result["build"]},
                    {"amd64", "arm64"},
                )

    def test_shared_pipeline_changes_validate_without_rebuilding_images(self):
        for path in [
            ".github/workflows/container.yaml",
            ".github/scripts/image.py",
            "new-build-input",
        ]:
            with self.subTest(path=path):
                self.assertFalse(matrix(changed_files=[path])["required"])

    def test_manual_selection_keeps_recipe_architecture_support(self):
        result = matrix("comfyui-radiance")
        self.assertTrue(result["required"])
        self.assertEqual(
            [build["architecture"] for build in result["build"]], ["amd64"]
        )
        self.assertGreater(len(matrix()["include"]), 1)

    def test_release_references_become_version_tags(self):
        versions = {
            recipe["image"]: recipe["version"] for recipe in matrix()["include"]
        }
        self.assertEqual(versions["betterbench"], "")
        self.assertRegex(versions["gatus-tailscale"], r"^v\d+\.\d+\.\d+$")

    def test_partial_git_pin_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "example").mkdir()
            for data in [
                {"repository": "owner/project", "reference": "main"},
                {"repository": "owner/project", "reference": "v1.0.0", "revision": "a"},
                {"repository": "owner/project", "revision": "a" * 40},
            ]:
                with self.subTest(data=data), patch("image.ROOT", root):
                    (root / "example" / "source.json").write_text(json.dumps(data))
                    with self.assertRaises(ValueError):
                        image.source("example")

    def test_unknown_manual_recipe_fails(self):
        with self.assertRaises(ValueError):
            matrix("not-a-recipe")


class PublicationBaselineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for name in image.images():
            (self.root / name).mkdir()
            for file in ["Dockerfile", "source.json"]:
                shutil.copy(image.ROOT / name / file, self.root / name / file)
        self.git("init", "--quiet")
        self.commit()
        self.base = self.git("rev-parse", "HEAD")
        self.patch = patch("image.ROOT", self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def git(self, *arguments):
        return subprocess.check_output(
            ["git", "-C", str(self.root), *arguments], text=True
        ).strip()

    def commit(self):
        self.git("add", ".")
        self.git(
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "Fixture",
        )

    def test_metadata_after_pending_runtime_still_builds_runtime(self):
        (self.root / "gatus-tailscale" / "Dockerfile").write_text("Changed runtime")
        self.commit()
        (self.root / "README.md").write_text("Later metadata")
        self.commit()
        result = matrix(changed_files=changes_since(self.base))
        self.assertEqual(
            [recipe["image"] for recipe in result["include"]], ["gatus-tailscale"]
        )

    def test_delayed_old_run_cannot_overwrite_newer_publication(self):
        (self.root / "gatus-tailscale" / "Dockerfile").write_text("Newer runtime")
        self.commit()
        published = self.git("rev-parse", "HEAD")
        self.git("checkout", "--quiet", self.base)
        self.assertFalse(matrix(changed_files=changes_since(published))["required"])

    def test_no_successful_baseline_builds_all(self):
        self.assertTrue(matrix(changed_files=changes_since(""))["required"])
        self.assertTrue(matrix(changed_files=changes_since("0" * 40))["required"])
        self.assertTrue(matrix(changed_files=changes_since("1" * 40))["required"])


if __name__ == "__main__":
    unittest.main()
