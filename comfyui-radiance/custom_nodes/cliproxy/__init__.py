"""Grok media through the configured CLIProxyAPI; outputs stay in this ComfyUI instance."""

import base64
import io
import json
import math
import os
import time
import uuid
from pathlib import Path
from urllib import error, parse, request

import folder_paths
from PIL import Image, PngImagePlugin

MODELS = {
    "image": (
        "grok-imagine-image",
        "grok-imagine-image-2.0",
        "grok-imagine-image-quality",
    ),
    "video": (
        "grok-imagine-video",
        "grok-imagine-video-1.5",
    ),
}
DEFAULT_MODELS = {
    "image": "grok-imagine-image-quality",
    "video": "grok-imagine-video-1.5",
}


def media_model(kind, model=""):
    if kind not in MODELS:
        raise ValueError("Unsupported media kind.")
    selected = model or DEFAULT_MODELS[kind]
    if selected not in MODELS[kind]:
        raise ValueError(f"Unsupported {kind} model: {selected}.")
    return selected


RESOLUTIONS = {
    "grok-imagine-image-2.0": ("1k", "2k"),
    "grok-imagine-video": ("480p", "720p"),
    "grok-imagine-video-1.5": ("480p", "720p", "1080p"),
}


def media_resolution(kind, model, resolution="", width=1024, height=1024):
    selected = media_model(kind, model)
    allowed = RESOLUTIONS.get(selected, ())
    if not allowed:
        if resolution:
            raise ValueError(f"Resolution is not adjustable for {selected}.")
        return ""
    fallback = (
        "720p" if kind == "video" else "2k" if max(width, height) > 1024 else "1k"
    )
    value = resolution or fallback
    if value not in allowed:
        raise ValueError(f"Unsupported resolution for {selected}: {value}.")
    return value


class Proxy:
    def __init__(self):
        self.base = os.environ.get("CLIPROXYAPI_URL", "").rstrip("/")
        self.key = os.environ.get("CLIPROXYAPI_KEY", "")
        parsed = parse.urlsplit(self.base)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            raise ValueError(
                "Configure CLIPROXYAPI_URL as the provider's base HTTP(S) address."
            )
        if not self.key:
            raise ValueError(
                "Configure CLIPROXYAPI_KEY in the private provider environment."
            )

    def call(self, path, body=None, content_type="application/json"):
        data = json.dumps(body).encode() if isinstance(body, dict) else body
        headers = {"Authorization": f"Bearer {self.key}"}
        if data is not None:
            headers["Content-Type"] = content_type
        req = request.Request(self.base + path, data=data, headers=headers)

        # Never follow provider redirects with the bearer credential.
        class NoRedirect(request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None

        try:
            with request.build_opener(NoRedirect).open(req, timeout=300) as response:
                return json.load(response)
        except error.HTTPError as exc:
            raise RuntimeError(
                f"CLIProxyAPI returned HTTP {exc.code}; inspect provider health."
            ) from None

    def image(self, prompt, size, reference=None, model="", resolution=""):
        fields = {
            "model": media_model("image", model),
            "prompt": prompt,
            "response_format": "b64_json",
            "size": size,
        }
        width, height = (int(value) for value in size.split("x"))
        resolution = media_resolution(
            "image", fields["model"], resolution, width, height
        )
        if fields["model"] == "grok-imagine-image-2.0":
            divisor = math.gcd(width, height)
            del fields["size"]
            fields["aspect_ratio"] = f"{width // divisor}:{height // divisor}"
            fields["resolution"] = resolution
            if reference is not None:
                fields["image"] = {
                    "type": "image_url",
                    "url": "data:image/png;base64,"
                    + base64.b64encode(reference).decode(),
                }
            result = self.call(
                "/v1/images/edits"
                if reference is not None
                else "/v1/images/generations",
                fields,
            )
        elif reference is None:
            result = self.call("/v1/images/generations", fields)
        else:
            boundary = uuid.uuid4().hex
            parts = []
            for name, value in fields.items():
                parts.append(
                    f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
                )
            parts.extend(
                [
                    f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="reference.png"\r\nContent-Type: image/png\r\n\r\n'.encode(),
                    reference,
                    f"\r\n--{boundary}--\r\n".encode(),
                ]
            )
            result = self.call(
                "/v1/images/edits",
                b"".join(parts),
                f"multipart/form-data; boundary={boundary}",
            )
        item = result["data"][0]
        return (
            base64.b64decode(item["b64_json"], validate=True)
            if item.get("b64_json")
            else download(item["url"])
        )

    def video(
        self, prompt, width, height, seconds, reference=None, model="", resolution=""
    ):
        if (
            isinstance(seconds, bool)
            or not isinstance(seconds, int)
            or not 1 <= seconds <= 15
        ):
            raise ValueError("Video duration must be between 1 and 15 seconds.")
        model = media_model("video", model)
        resolution = media_resolution("video", model, resolution, width, height)
        divisor = math.gcd(width, height)
        body = {
            "aspect_ratio": f"{width // divisor}:{height // divisor}",
            "duration": seconds,
            "model": media_model("video", model),
            "prompt": prompt,
            "resolution": resolution,
        }
        if reference is not None:
            body["image"] = {
                "url": "data:image/png;base64," + base64.b64encode(reference).decode()
            }
        submitted = self.call("/v1/videos/generations", body)
        job = submitted.get("request_id")
        if not isinstance(job, str) or not job:
            raise RuntimeError(
                "CLIProxyAPI returned no video request ID; inspect provider before retrying."
            )
        deadline = time.monotonic() + 900
        while time.monotonic() < deadline:
            result = self.call("/v1/videos/" + parse.quote(job, safe=""))
            if result.get("status") in {"completed", "done"}:
                url = (
                    (result.get("video") or {}).get("url")
                    or result.get("video_url")
                    or result.get("output_url")
                )
                if not url:
                    raise RuntimeError(
                        "CLIProxyAPI completed the video without an output URL."
                    )
                return download(url)
            if result.get("status") in {"error", "failed"}:
                raise RuntimeError("CLIProxyAPI video failed; inspect provider health.")
            time.sleep(2)
        raise TimeoutError(
            "Video still pending after 15 minutes; inspect provider before retrying."
        )


def download(url):
    if parse.urlsplit(url).scheme != "https":
        raise ValueError("Provider media must use an HTTPS download URL.")
    # A separate request deliberately carries no provider credential.
    with request.urlopen(url, timeout=300) as response:
        return response.read()


class GrokMedia:
    CATEGORY = "AI/Grok"
    FUNCTION = "generate"
    OUTPUT_NODE = True
    RETURN_TYPES = ()

    @classmethod
    def INPUT_TYPES(cls):
        files = sorted(
            name
            for name in os.listdir(folder_paths.get_input_directory())
            if Path(name).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        )
        return {
            "required": {
                "kind": (["image", "video"],),
                "prompt": ("STRING", {"multiline": True}),
                "width": ("INT", {"default": 1024, "min": 256, "max": 2048, "step": 8}),
                "height": (
                    "INT",
                    {"default": 1024, "min": 256, "max": 2048, "step": 8},
                ),
                "seconds": ("INT", {"default": 6, "min": 1, "max": 15}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
            },
            "optional": {
                "count": ("INT", {"default": 1, "min": 1, "max": 8}),
                "image": ([""] + files, {"image_upload": True}),
                "model": ([""] + list(MODELS["image"]) + list(MODELS["video"]),),
                "resolution": (["", "1k", "2k", "480p", "720p", "1080p"],),
            },
            "hidden": {"workflow_prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Provider does not support reproducible seeds; each queued job is new.
        return float("nan")

    def generate(self, kind, prompt, width, height, seconds, seed, count=1, **kwargs):
        if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= 8:
            raise ValueError("Choose between one and eight image outputs.")
        key = "images" if kind == "image" else "videos"
        outputs = []
        for index in range(count if kind == "image" else 1):
            result = self._generate_one(
                kind, prompt, width, height, seconds, seed + index, **kwargs
            )
            outputs.extend(result["ui"][key])
        return {"ui": {key: outputs}, "result": ()}

    def _generate_one(
        self,
        kind,
        prompt,
        width,
        height,
        seconds,
        seed,
        image="",
        workflow_prompt=None,
        extra_pnginfo=None,
        model="",
        resolution="",
    ):
        model = media_model(kind, model)
        resolution = media_resolution(kind, model, resolution, width, height)
        reference = None
        if image:
            reference_path = Path(folder_paths.get_annotated_filepath(image)).resolve()
            input_root = Path(folder_paths.get_input_directory()).resolve()
            if not reference_path.is_relative_to(input_root):
                raise ValueError(
                    "References must belong to this instance's input folder."
                )
            with Image.open(reference_path) as original:
                stream = io.BytesIO()
                original.convert("RGB").save(stream, format="PNG")
                reference = stream.getvalue()
        proxy = Proxy()
        if kind == "image":
            content = proxy.image(
                prompt,
                f"{width}x{height}",
                reference,
                model=model,
                resolution=resolution,
            )
        elif kind == "video":
            content = proxy.video(
                prompt,
                width,
                height,
                seconds,
                reference,
                model=model,
                resolution=resolution,
            )
        else:
            raise ValueError("Unsupported media kind.")
        output = Path(folder_paths.get_output_directory()) / "grok"
        output.mkdir(parents=True, exist_ok=True)
        filename = uuid.uuid4().hex + (".png" if kind == "image" else ".mp4")
        destination = output / filename
        metadata = {
            "model": model,
            "prompt": prompt,
            "provider": "cliproxyapi",
            "reference": image,
            "resolution": resolution or None,
            "seconds": seconds if kind == "video" else None,
        }
        if kind == "image":
            pnginfo = PngImagePlugin.PngInfo()
            pnginfo.add_text("prompt", json.dumps(workflow_prompt or {}))
            pnginfo.add_text(
                "parameters",
                f"{prompt}\nSteps: 1, Model: {metadata['model']}, Size: {width}x{height}",
            )
            for key, value in (extra_pnginfo or {}).items():
                pnginfo.add_text(key, json.dumps(value))
            with Image.open(io.BytesIO(content)) as generated:
                generated.save(destination, pnginfo=pnginfo)
        else:
            destination.write_bytes(content)
        destination.with_suffix(destination.suffix + ".json").write_text(
            json.dumps(metadata, indent=2) + "\n"
        )
        return {
            "ui": {
                "images" if kind == "image" else "videos": [
                    {"filename": filename, "subfolder": "grok", "type": "output"}
                ]
            },
            "result": (),
        }


NODE_CLASS_MAPPINGS = {"GrokMedia": GrokMedia}
NODE_DISPLAY_NAME_MAPPINGS = {"GrokMedia": "Grok Image & Video"}
