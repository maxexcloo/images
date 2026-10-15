"""Exercise recipe selection and the required build/publishing gate."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import image
from image import changes_since, matrix, results_succeeded


class MatrixTests(unittest.TestCase):
    def test_metadata_only_changes_need_no_images(self):
        result = matrix(
            changed_files=["README.md", ".mise.toml", ".updatecli.d/mise.yaml"]
        )
        self.assertFalse(result["required"])
        self.assertEqual(result["build"], [])
        self.assertEqual(result["include"], [])

    def test_one_recipe_selects_all_its_architectures(self):
        for path in ["redlib/Dockerfile", "redlib/source.json"]:
            with self.subTest(path=path):
                result = matrix(changed_files=[path])
                self.assertEqual(
                    [recipe["image"] for recipe in result["include"]], ["redlib"]
                )
                self.assertEqual(
                    {build["architecture"] for build in result["build"]},
                    {"amd64", "arm64"},
                )

    def test_shared_pipeline_and_unknown_inputs_require_all_images(self):
        full = matrix()
        for path in [
            ".github/workflows/container.yaml",
            ".github/scripts/image.py",
            "new-build-input",
        ]:
            with self.subTest(path=path):
                self.assertEqual(matrix(changed_files=[path]), full)

    def test_manual_selection_keeps_recipe_architecture_support(self):
        result = matrix("comfyui-rocm")
        self.assertTrue(result["required"])
        self.assertEqual(
            [build["architecture"] for build in result["build"]], ["amd64"]
        )
        self.assertGreater(len(matrix()["include"]), 1)

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
            shutil.copy(
                image.ROOT / name / "source.json", self.root / name / "source.json"
            )
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
        (self.root / "redlib" / "Dockerfile").write_text("Changed runtime")
        self.commit()
        (self.root / "README.md").write_text("Later metadata")
        self.commit()
        result = matrix(changed_files=changes_since(self.base))
        self.assertEqual([recipe["image"] for recipe in result["include"]], ["redlib"])

    def test_delayed_old_run_cannot_overwrite_newer_publication(self):
        (self.root / "redlib" / "Dockerfile").write_text("Newer runtime")
        self.commit()
        published = self.git("rev-parse", "HEAD")
        self.git("checkout", "--quiet", self.base)
        self.assertFalse(matrix(changed_files=changes_since(published))["required"])

    def test_no_successful_baseline_builds_all(self):
        self.assertTrue(matrix(changed_files=changes_since(""))["required"])
        self.assertTrue(matrix(changed_files=changes_since("0" * 40))["required"])


class ResultTests(unittest.TestCase):
    def test_metadata_run_requires_successful_prepare(self):
        self.assertTrue(
            results_succeeded("success", "skipped", "skipped", "false", "true")
        )
        for result in ["failure", "cancelled", "skipped", ""]:
            with self.subTest(result=result):
                self.assertFalse(
                    results_succeeded(result, "skipped", "skipped", "false", "true")
                )

    def test_pr_build_must_pass_and_cannot_publish(self):
        self.assertTrue(
            results_succeeded("success", "success", "skipped", "true", "false")
        )
        for result in ["failure", "cancelled", "skipped"]:
            self.assertFalse(
                results_succeeded("success", result, "skipped", "true", "false")
            )
        self.assertFalse(
            results_succeeded("success", "success", "success", "true", "false")
        )

    def test_main_build_requires_successful_publishing(self):
        self.assertTrue(
            results_succeeded("success", "success", "success", "true", "true")
        )
        self.assertFalse(
            results_succeeded("success", "success", "skipped", "true", "true")
        )
        self.assertFalse(
            results_succeeded("success", "success", "failure", "true", "true")
        )

    def test_missing_prepare_output_cannot_pass(self):
        self.assertFalse(results_succeeded("success", "skipped", "skipped", "", "true"))


if __name__ == "__main__":
    unittest.main()
