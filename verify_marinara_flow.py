"""Verify the proposed Marinara media contract against ToAPIs, outside the app.

Default: quote only. --live creates at most two image tasks and one short video.
Saved receipts resume existing tasks; changing --run-id explicitly starts a new run.
"""
from pathlib import Path
from decimal import Decimal
import argparse
import hashlib
import json
import os
import sys
import uuid

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "toapis-models"))
from unified_client import Client, generate, prepare, save

IMAGE_PROMPT = "Cinematic 16:9 scene illustration of an empty sunlit fantasy library, wooden shelves, arched windows, a reading desk and warm gold light, no characters, no text, no watermark."
EDIT_PROMPT = "Preserve the library layout and objects. Change the sunlight to cool blue moonlight and add a small glowing blue crystal on the desk. No characters, text or watermark."
VIDEO_PROMPT = "Slow gentle camera push into the library. Preserve the room layout, desk and crystal. Subtle moving light, no scene cuts, no characters, no text, no audio."


def presets():
    image = {"model": "gpt-image-2", "kind": "image",
             "request": {"model": "gpt-image-2", "size": "16:9", "resolution": "1k", "n": 1},
             "pricing_conditions": {"resolution": "1K", "n": 1, "input_image_count": 0}}
    edit = json.loads(json.dumps(image))
    edit["pricing_conditions"]["input_image_count"] = 1
    video = {"model": "seedance-2-mini", "kind": "video", "needs_image": True,
             "request": {"model": "seedance-2-mini", "duration": 4, "aspect_ratio": "16:9",
                         "resolution": "480p", "generate_audio": False},
             "pricing_conditions": {"resolution": "480p", "duration": 4, "has_video_input": False,
                                    "has_image_input": True, "has_audio_input": False,
                                    "generate_audio": False, "input_image_count": 1}}
    return image, edit, video


class ProjectClient(Client):
    def upload_png(self, path):
        # The shared video helper uses this method name. Accept the documented
        # image formats without converting or changing the generated pixels.
        raw = Path(path).read_bytes()
        if raw.startswith(b"\x89PNG\r\n\x1a\n"):
            mime, ext = "image/png", "png"
        elif raw.startswith(b"\xff\xd8\xff"):
            mime, ext = "image/jpeg", "jpg"
        elif raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
            mime, ext = "image/webp", "webp"
        elif raw[:6] in (b"GIF87a", b"GIF89a"):
            mime, ext = "image/gif", "gif"
        else:
            raise ValueError("Reference must be a PNG, JPEG, WebP or GIF")
        if len(raw) > 10 * 1024 * 1024:
            raise ValueError("Reference exceeds the 10 MiB limit")
        cache = self.state / ("upload-" + hashlib.sha256(raw).hexdigest() + ".json")
        if cache.exists():
            return json.loads(cache.read_text(encoding="utf-8"))["url"]
        boundary = "ToAPIs" + uuid.uuid4().hex
        data = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="reference.{ext}"\r\n'
                f"Content-Type: {mime}\r\n\r\n").encode() + raw + f"\r\n--{boundary}--\r\n".encode()
        response = self.json("uploads/images", data, "multipart/form-data; boundary=" + boundary)
        url = response["data"]["url"]
        if not isinstance(url, str) or not url.startswith("https://"):
            raise ValueError("Upload returned no HTTPS reference URL")
        save(cache, {"url": url})
        return url


def quote_flow(client, maximum):
    configs = presets()
    prompts = (IMAGE_PROMPT, EDIT_PROMPT, VIDEO_PROMPT)
    quotes = [prepare(client, config, prompt, maximum) for config, prompt in zip(configs, prompts)]
    total = sum((Decimal(item["estimated_usd"]) for item in quotes), Decimal("0"))
    if total > Decimal(str(maximum)):
        raise ValueError("Combined forecast exceeds --max-usd; no generation submitted")
    return {"forecast_usd": str(total), "forecast_only": True,
            "video_token_estimate_not_a_locked_quote": True,
            "planned_tasks": 3, "native_marinara_verified": False}


def run_flow(client, output_dir, maximum="0.50", live=False, run_id="marinara-media-flow-v1"):
    plan = quote_flow(client, maximum)
    if not live:
        return plan
    configs = presets()
    results = []
    first = generate(client, configs[0], IMAGE_PROMPT, output_dir, maximum, True, run_id=run_id + "-image")
    results.append(first)
    if first.get("status") != "completed":
        return {"status": "stopped", "results": results, "native_marinara_verified": False}
    source = Path(first["output"])
    configs[1]["request"]["reference_images"] = [client.upload_png(source)]
    edit = generate(client, configs[1], EDIT_PROMPT, output_dir, maximum, True, run_id=run_id + "-edit")
    results.append(edit)
    if edit.get("status") != "completed":
        return {"status": "stopped", "results": results, "native_marinara_verified": False}
    video = generate(client, configs[2], VIDEO_PROMPT, output_dir, maximum, True,
                     image=Path(edit["output"]), run_id=run_id + "-video")
    results.append(video)
    return {"status": "completed" if video.get("status") == "completed" else "stopped",
            "results": results, "native_marinara_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--max-usd", default="0.50", help="Forecast allowance, not an upstream billing cap")
    parser.add_argument("--state", default=str(ROOT / ".toapis-state" / "marinara-flow"))
    parser.add_argument("--output-dir", default=str(ROOT / ".toapis-state" / "marinara-flow" / "assets"))
    parser.add_argument("--run-id", default="marinara-media-flow-v1")
    args = parser.parse_args()
    result = run_flow(ProjectClient(state=args.state), args.output_dir, args.max_usd, args.live, args.run_id)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
