"""Reuse CPU LoRA files across core and rgthree loaders without changing recipes."""

import logging
from pathlib import Path

import comfy.memory_management
import comfy.utils
import folder_paths

from .cache import CACHE_BYTES, LoraCache, cached_loader
from .validate import validate

try:
    validate(Path(comfy.utils.__file__).resolve().parents[1])
except Exception as exc:
    # ComfyUI swallows ordinary extension errors; an incompatible wrapper must stop startup.
    raise SystemExit(f"AI LoRA cache: {exc}") from exc

if not getattr(comfy.utils.load_torch_file, "ai_lora_cache", False):
    CACHE = LoraCache()
    comfy.utils.load_torch_file = cached_loader(
        comfy.utils.load_torch_file,
        CACHE,
        lambda: folder_paths.get_folder_paths("loras"),
        lambda: comfy.memory_management.aimdo_enabled,
    )
    comfy.utils.load_torch_file.ai_lora_cache = True
    logging.getLogger(__name__).info(
        "AI CPU LoRA file cache: %s MiB per worker", CACHE_BYTES // 1024**2
    )

NODE_CLASS_MAPPINGS = {}
