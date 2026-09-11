"""CLI bridge from figure Skills to Modickx's configured vision provider."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path


def _load_runtime() -> tuple[object, object, str]:
    config_path = Path(__file__).with_name("modickx_runtime.json")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        backend_dir = Path(str(config["backend_dir"])).resolve()
        db_path = Path(str(config["db_path"])).resolve()
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("Modickx runtime configuration is unavailable") from exc
    os.environ["MH_DB_PATH"] = str(db_path)
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    from services.data_fig_vision import VISION_PROMPT, parse_vision_response
    from services.llm_client import describe_image

    return describe_image, parse_vision_response, VISION_PROMPT


async def _review(image_path: Path) -> dict[str, object]:
    describe_image, parse_vision_response, prompt = _load_runtime()
    raw = await describe_image(str(image_path), prompt)
    if not raw:
        raise RuntimeError("Vision API unavailable or no multimodal model configured")
    return parse_vision_response(raw)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("Usage: data_fig_vision_check.py <image>")
        return 2
    image_path = Path(args[0]).expanduser().resolve()
    if not image_path.is_file() or image_path.suffix.lower() not in {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }:
        print("SKIPPED: input must be an existing PNG/JPEG/WebP image")
        return 2
    try:
        result = asyncio.run(_review(image_path))
    except Exception as exc:
        print(f"SKIPPED: {str(exc)[:500]}")
        return 2
    if result["status"] == "PASS":
        print("PASS")
        return 0
    for issue in result["issues"]:
        print(f"ISSUE {issue}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
