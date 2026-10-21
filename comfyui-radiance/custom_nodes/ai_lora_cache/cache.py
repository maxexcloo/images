"""Bounded CPU LoRA file reuse, independent of node instances and strengths."""

import copy
import sys
import threading
from collections import OrderedDict
from pathlib import Path

CACHE_BYTES = 1024**3


def retained_bytes(value, seen=None, storages=None):
    """Count container overhead and tensor storage, including shared views once."""
    seen = set() if seen is None else seen
    storages = set() if storages is None else storages
    if id(value) in seen:
        return 0
    seen.add(id(value))
    size = sys.getsizeof(value)
    if hasattr(value, "untyped_storage"):
        storage = value.untyped_storage()
        key = (storage.data_ptr(), storage.nbytes())
        if key not in storages:
            storages.add(key)
            size += storage.nbytes()
    elif isinstance(value, dict):
        size += sum(
            retained_bytes(part, seen, storages)
            for pair in value.items()
            for part in pair
        )
    elif isinstance(value, (list, tuple)):
        size += sum(retained_bytes(part, seen, storages) for part in value)
    return size


class LoraCache:
    def __init__(self, budget=CACHE_BYTES):
        self.budget = budget
        self.bytes = 0
        self.entries = OrderedDict()
        self.lock = threading.Lock()

    def load(self, path, loader):
        path = Path(path).resolve()
        # Serialise misses as well: concurrent requests must not duplicate a large read.
        with self.lock:
            stat = path.stat()
            identity = (
                stat.st_dev,
                stat.st_ino,
                stat.st_size,
                stat.st_mtime_ns,
                stat.st_ctime_ns,
            )
            key = (path, identity)
            for old in list(self.entries):
                if old[0] == path and old != key:
                    self.bytes -= self.entries.pop(old)[1]
            if key in self.entries:
                value, size = self.entries.pop(key)
                self.entries[key] = (value, size)
            else:
                value = loader()
                size = retained_bytes(value)
                # Do not retain a read that raced with a library replacement.
                after = path.stat()
                unchanged = identity == (
                    after.st_dev,
                    after.st_ino,
                    after.st_size,
                    after.st_mtime_ns,
                    after.st_ctime_ns,
                )
                if unchanged and size <= self.budget:
                    while self.entries and self.bytes + size > self.budget:
                        self.bytes -= self.entries.popitem(last=False)[1][1]
                    self.entries[key] = (value, size)
                    self.bytes += size
            state, metadata = value
            # ComfyUI consumes tensors without mutating their storage, but may remove keys.
            return state.copy(), copy.deepcopy(metadata)


def cached_loader(original, cache, roots, aimdo_enabled):
    def load(ckpt, safe_load=False, device=None, return_metadata=False):
        path = Path(ckpt).resolve()
        cpu = device is None or getattr(device, "type", None) == "cpu"
        eligible = (
            safe_load
            and cpu
            and not aimdo_enabled()
            and path.suffix.lower() in {".safetensors", ".sft"}
            and any(path.is_relative_to(Path(root).resolve()) for root in roots())
        )
        if not eligible:
            return original(
                ckpt,
                safe_load=safe_load,
                device=device,
                return_metadata=return_metadata,
            )
        state, metadata = cache.load(
            path,
            lambda: original(ckpt, safe_load=True, device=device, return_metadata=True),
        )
        return (state, metadata) if return_metadata else state

    return load
