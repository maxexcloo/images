"""LoRA file reuse, invalidation and CPU memory limits without loading a GPU."""

import hashlib
import importlib.util
import tempfile
import types
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1] / "comfyui/custom_nodes/ai_lora_cache"


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


cache = module("cache")
validate = module("validate").validate


class LoraCacheTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.path = self.root / "adapter.safetensors"
        self.path.write_bytes(b"weights")
        self.value = ({"weight": b"tensor"}, {"format": "pt"})
        self.original = Mock(
            side_effect=lambda *a, **kw: (
                ({**self.value[0]}, {**self.value[1]})
                if kw["return_metadata"]
                else {**self.value[0]}
            )
        )
        self.cache = cache.LoraCache()
        self.load = cache.cached_loader(
            self.original, self.cache, lambda: [self.root], lambda: False
        )

    def test_reuse_across_calls_and_return_forms_keeps_mapping_edits_private(self):
        state, metadata = self.load(
            str(self.path), safe_load=True, return_metadata=True
        )
        state.pop("weight")
        metadata["format"] = "changed"
        self.assertEqual(self.load(str(self.path), safe_load=True), self.value[0])
        self.assertEqual(
            self.load(str(self.path), safe_load=True, return_metadata=True), self.value
        )
        self.assertEqual(self.original.call_count, 1)

    def test_replaced_file_invalidates_even_when_size_and_name_match(self):
        self.load(str(self.path), safe_load=True)
        replacement = self.root / "new"
        replacement.write_bytes(b"changed")
        replacement.replace(self.path)
        self.load(str(self.path), safe_load=True)
        self.assertEqual(self.original.call_count, 2)
        self.assertEqual(len(self.cache.entries), 1)

    def test_lru_eviction_and_oversized_bypass(self):
        size = cache.retained_bytes(self.value)
        self.cache.budget = size * 2
        paths = [self.root / f"{index}.safetensors" for index in range(3)]
        for path in paths:
            path.write_bytes(b"weights")
        for path in [paths[0], paths[1], paths[0], paths[2], paths[1]]:
            self.load(str(path), safe_load=True)
        self.assertEqual(self.original.call_count, 4)
        self.assertLessEqual(self.cache.bytes, self.cache.budget)
        self.cache.budget = 1
        other = cache.LoraCache(budget=1)
        for _ in range(2):
            other.load(self.path, lambda: self.value)
        self.assertFalse(other.entries)
        self.assertEqual(other.bytes, 0)

    def test_failures_are_not_cached_and_concurrent_reads_are_shared(self):
        self.original.side_effect = RuntimeError("read failed")
        with self.assertRaises(RuntimeError):
            self.load(str(self.path), safe_load=True)
        self.original.side_effect = lambda *a, **kw: self.value
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(
                pool.map(lambda _: self.load(str(self.path), safe_load=True), range(8))
            )
        self.assertTrue(all(value == self.value[0] for value in results))
        self.assertEqual(self.original.call_count, 2)

    def test_only_safe_cpu_lora_files_are_cached(self):
        cases = [
            (self.path, {}),
            (
                self.path,
                {"safe_load": True, "device": types.SimpleNamespace(type="cuda")},
            ),
            (self.root / "adapter.pt", {"safe_load": True}),
            (self.root.parent / "checkpoint.safetensors", {"safe_load": True}),
        ]
        for path, kwargs in cases:
            for _ in range(2):
                self.load(str(path), **kwargs)
        self.assertEqual(self.original.call_count, 8)
        aimdo = cache.cached_loader(
            self.original, self.cache, lambda: [self.root], lambda: True
        )
        for _ in range(2):
            aimdo(str(self.path), safe_load=True)
        self.assertEqual(self.original.call_count, 10)
        self.assertFalse(self.cache.entries)

    def test_shared_tensor_storage_is_counted_once(self):
        class Tensor:
            def untyped_storage(self):
                return types.SimpleNamespace(
                    data_ptr=lambda: 1234, nbytes=lambda: 10000
                )

        value = [Tensor(), Tensor()]
        self.assertLess(cache.retained_bytes(value), 11000)
        self.assertGreaterEqual(cache.retained_bytes(value), 10000)

    def test_file_changed_during_read_is_not_retained(self):
        def read():
            self.path.write_bytes(b"replacement weights")
            return self.value

        self.cache.load(self.path, read)
        self.assertFalse(self.cache.entries)
        self.assertEqual(self.cache.bytes, 0)

    def test_upstream_guard_rejects_changed_function_without_writing(self):
        source = "def load():\n    return 1"
        target = self.root / "utils.py"
        target.write_text(source)
        targets = {
            "utils.py": {
                "class": None,
                "function": "load",
                "sha256": hashlib.sha256(source.encode()).hexdigest(),
            }
        }
        validate(self.root, targets)
        target.write_text(source.replace("1", "2"))
        with self.assertRaisesRegex(RuntimeError, "target changed"):
            validate(self.root, targets)
        self.assertEqual(target.read_text(), source.replace("1", "2"))
