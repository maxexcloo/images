"""Exercise recipe discovery in the actual workflow with local GitHub responses."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from image import ROOT


class WorkflowSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = subprocess.check_output(
            [
                "yq",
                "-r",
                '.jobs.prepare.steps[] | select(.id == "recipes") | .run',
                str(ROOT / ".github/workflows/container.yaml"),
            ],
            text=True,
        )
        cls.revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()

    def discover(
        self,
        current_revision,
        image="all",
        ref="refs/heads/main",
        event="workflow_dispatch",
    ):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            gh = temporary / "gh"
            gh.write_text('#!/bin/sh\nprintf "%s\\n" "$TEST_CURRENT_REVISION"\n')
            gh.chmod(0o755)
            output = temporary / "output"
            environment = dict(
                os.environ,
                BASE_REVISION="",
                GITHUB_EVENT_NAME=event,
                GITHUB_OUTPUT=str(output),
                GITHUB_REF=ref,
                GITHUB_REF_TYPE="branch",
                GITHUB_REPOSITORY="owner/images",
                GITHUB_SHA=self.revision,
                IMAGE_NAME=image,
                PATH=f"{temporary}{os.pathsep}{os.environ['PATH']}",
                TEST_CURRENT_REVISION=current_revision,
            )
            subprocess.run(
                ["bash", "-euo", "pipefail", "-c", self.script],
                check=True,
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
            )
            return json.loads(output.read_text().removeprefix("matrix="))

    def test_outdated_manual_main_run_skips_images(self):
        for image in ["all", "gatus-tailscale"]:
            with self.subTest(image=image):
                self.assertFalse(self.discover("f" * 40, image)["required"])

    def test_current_manual_main_run_rebuilds_selected_image(self):
        result = self.discover(self.revision, "gatus-tailscale")
        self.assertEqual(
            [recipe["image"] for recipe in result["include"]], ["gatus-tailscale"]
        )

    def test_manual_feature_branch_still_builds(self):
        result = self.discover("f" * 40, "gatus-tailscale", "refs/heads/feature")
        self.assertTrue(result["required"])

    def test_outdated_push_cannot_advance_successful_publication_baseline(self):
        with self.assertRaises(subprocess.CalledProcessError):
            self.discover("f" * 40, event="push")
