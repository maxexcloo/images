"""MiniMax references retain their entire frame at every canvas aspect."""

import ast
import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from patches.patch_minimax import AFTER, BEFORE, LEGACY_AFTER, LEGACY_BEFORE
from patches.patch_minimax import patch as patch_core


class ShapeImage:
    """Track tensor geometry without loading a GPU framework in static tests."""

    def __init__(self, shape):
        self.shape = shape

    def __getitem__(self, key):
        return self

    def movedim(self, source, destination):
        shape = list(self.shape)
        shape.insert(destination % len(shape), shape.pop(source))
        return ShapeImage(tuple(shape))


class MiniMaxGeometryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.target = self.root / "comfy_extras/nodes_minimax_h3.py"
        self.target.parent.mkdir()
        self.original = (
            BEFORE
            + "\n\nclass MiniMaxH3ImageToVideo:\n"
            + "    def execute(first_frame, width, height):\n"
            + LEGACY_BEFORE
            + "\n            # follower: aspect-preserving cover-crop\n            return img\n"
        ).encode()
        self.target.write_bytes(self.original)
        self.digest = patch(
            "patches.patch_minimax.UPSTREAM_SHA256",
            hashlib.sha256(self.original).hexdigest(),
        )
        self.digest.start()
        self.addCleanup(self.digest.stop)

    def test_entire_reference_fits_landscape_portrait_and_aligned_canvases(self):
        patch_core(self.root)
        for source_width, source_height, width, height in [
            (768, 1376, 1344, 768),
            (768, 1376, 864, 1184),
            (864, 1152, 768, 448),
            (768, 1376, 736, 1344),
            (1024, 1024, 1024, 1024),
        ]:
            calls = {}

            def upscale(
                samples, fitted_width, fitted_height, method, crop, calls=calls
            ):
                calls.update(width=fitted_width, height=fitted_height, crop=crop)
                return ShapeImage((1, 3, fitted_height, fitted_width))

            def pad(samples, padding, value):
                left, right, top, bottom = padding
                self.assertTrue(all(side >= 0 for side in padding))
                return ShapeImage(
                    (
                        1,
                        3,
                        samples.shape[2] + top + bottom,
                        samples.shape[3] + left + right,
                    )
                )

            namespace = {
                "comfy": SimpleNamespace(utils=SimpleNamespace(common_upscale=upscale)),
                "F": SimpleNamespace(pad=pad),
            }
            exec(  # noqa: S102 -- Execute only the locally patched geometry fixture.
                compile(ast.parse(self.target.read_text()), str(self.target), "exec"),
                namespace,
            )
            for crop in ["disabled", "center"]:
                result = namespace["_resize"](
                    ShapeImage((1, source_height, source_width, 3)), width, height, crop
                )
                self.assertEqual(result.shape, (1, height, width, 3))
                self.assertEqual(calls["crop"], "disabled")
                self.assertLessEqual(
                    abs(
                        calls["width"] / source_width - calls["height"] / source_height
                    ),
                    1 / min(source_width, source_height),
                )
                self.assertTrue(calls["width"] == width or calls["height"] == height)

    def test_restart_is_idempotent(self):
        patch_core(self.root)
        expected = self.target.read_bytes()
        patch_core(self.root)
        self.assertEqual(self.target.read_bytes(), expected)
        self.assertIn(AFTER.encode(), expected)

    def test_prior_centre_crop_patch_upgrades_without_losing_other_source(self):
        self.target.write_bytes(
            self.original.replace(LEGACY_BEFORE.encode(), LEGACY_AFTER.encode())
        )
        patch_core(self.root)
        self.assertIn(AFTER.encode(), self.target.read_bytes())
        self.assertNotIn(LEGACY_AFTER.encode(), self.target.read_bytes())
        patch_core(self.root)

    def test_changed_upstream_and_changed_patched_file_fail_without_writing(self):
        patch_core(self.root)
        patched = self.target.read_bytes()
        for content in [
            self.original + b"# upstream change\n",
            self.original.replace(LEGACY_BEFORE.encode(), LEGACY_AFTER.encode())
            + b"# upstream change\n",
            patched + b"# upstream change\n",
        ]:
            self.target.write_bytes(content)
            with self.assertRaisesRegex(RuntimeError, "target changed"):
                patch_core(self.root)
            self.assertEqual(self.target.read_bytes(), content)
