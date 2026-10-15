"""Exercise recipe selection and the required build/publishing gate."""

import unittest

from image import matrix, results_succeeded


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
