#!/usr/bin/env python3
"""Safe workspace wrapper for Modickx's Electron capture mode."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


MAX_TARGETS = 64
MAX_WAIT_MS = 60_000
MIN_VIEWPORT = 200
MAX_VIEWPORT = 8_000
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


@dataclass(frozen=True)
class CaptureRuntime:
    executable: Path
    capture_script: Path | None


def _runtime_config_candidates() -> list[Path]:
    here = Path(__file__).resolve().parent
    return [here / "modickx_runtime.json", here / "shared-scripts" / "modickx_runtime.json"]


def _read_runtime_config() -> dict[str, Any]:
    for path in _runtime_config_candidates():
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            return value
    return {}


def _discover_app_root(config: dict[str, Any]) -> Path | None:
    explicit = str(config.get("app_root", "")).strip()
    if explicit:
        return Path(explicit).expanduser().resolve()
    backend = str(config.get("backend_dir", "")).strip()
    if backend:
        return Path(backend).expanduser().resolve().parent
    for parent in Path(__file__).resolve().parents:
        if (parent / "capture.js").is_file():
            return parent
    return None


def _resolve_runtime() -> CaptureRuntime:
    config = _read_runtime_config()
    app_root = _discover_app_root(config)
    executable_text = os.environ.get("MH_ELECTRON_EXE", "").strip() or str(
        config.get("electron_executable", "")
    ).strip()
    capture_text = os.environ.get("MH_ELECTRON_CAPTURE_JS", "").strip() or str(
        config.get("capture_script", "")
    ).strip()

    executable = Path(executable_text).expanduser().resolve() if executable_text else None
    capture_script = Path(capture_text).expanduser().resolve() if capture_text else None
    if app_root is not None:
        if executable is None:
            candidates = [
                app_root / "node_modules" / "electron" / "dist" / "electron.exe",
                app_root / "node_modules" / "electron" / "dist" / "electron",
            ]
            executable = next((path.resolve() for path in candidates if path.is_file()), None)
        if capture_script is None and (app_root / "capture.js").is_file():
            capture_script = (app_root / "capture.js").resolve()

    if executable is None or not executable.is_file():
        raise RuntimeError("Electron executable is unavailable")
    if capture_script is not None and not capture_script.is_file():
        raise RuntimeError("Electron capture.js is unavailable")
    if executable.name.lower() in {"electron", "electron.exe"} and capture_script is None:
        raise RuntimeError("Development Electron requires capture.js")
    return CaptureRuntime(executable=executable, capture_script=capture_script)


def _has_symlink_component(path: Path, root: Path) -> bool:
    current = path
    while True:
        if current.exists() and current.is_symlink():
            return True
        if current == root or current.parent == current:
            return False
        current = current.parent


def _workspace_path(
    value: str,
    workspace: Path,
    *,
    must_exist: bool = False,
    label: str = "path",
) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = workspace / candidate
    unresolved = candidate.absolute()
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(f"{label} escapes the workspace") from exc
    if _has_symlink_component(unresolved, workspace):
        raise ValueError(f"{label} cannot use symlinks")
    if must_exist and not resolved.is_file():
        raise ValueError(f"{label} must be an existing file")
    return resolved


def _safe_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("capture URL must use http or https")
    if parsed.username or parsed.password or parsed.hostname not in LOOPBACK_HOSTS:
        raise ValueError("capture URL must be an unauthenticated loopback URL")
    return value


def _bounded_int(value: Any, label: str, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer") from exc
    if not minimum <= number <= maximum:
        raise ValueError(f"{label} must be between {minimum} and {maximum}")
    return number


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _optional_bool(target: dict[str, Any], key: str) -> bool:
    value = target.get(key, False)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _normalize_target(target: dict[str, Any], workspace: Path) -> dict[str, Any]:
    if not isinstance(target, dict):
        raise ValueError("capture target must be an object")
    has_file = bool(_text(target.get("file")))
    has_url = bool(_text(target.get("url")))
    if has_file == has_url:
        raise ValueError("capture target requires exactly one file or url")

    normalized: dict[str, Any] = {}
    if has_file:
        normalized["file"] = str(
            _workspace_path(str(target["file"]), workspace, must_exist=True, label="input file")
        )
    else:
        normalized["url"] = _safe_url(str(target["url"]))

    geom_check = _optional_bool(target, "geomCheck")
    out = _text(target.get("out"))
    if out:
        normalized["out"] = str(_workspace_path(out, workspace, label="output path"))
    elif not geom_check:
        raise ValueError("capture target requires out unless it is geometry-only")

    output_format = _text(target.get("format")).lower()
    if output_format:
        if output_format not in {"png", "pdf"}:
            raise ValueError("capture format must be png or pdf")
        normalized["format"] = output_format
    if "waitMs" in target:
        normalized["waitMs"] = _bounded_int(target["waitMs"], "waitMs", 0, MAX_WAIT_MS)
    selector = _text(target.get("waitForSelector"))
    if selector:
        if len(selector) > 500:
            raise ValueError("waitForSelector is too long")
        normalized["waitForSelector"] = selector
    for source_key, target_key in (
        ("fullPage", "fullPage"),
        ("renderMath", "renderMath"),
        ("geomCheck", "geomCheck"),
    ):
        if _optional_bool(target, source_key):
            normalized[target_key] = True
    return normalized


def _normalize_config(config: dict[str, Any], workspace: Path) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise ValueError("capture config must be an object")
    targets = config.get("targets")
    if not isinstance(targets, list) or not 1 <= len(targets) <= MAX_TARGETS:
        raise ValueError(f"capture config must contain 1 to {MAX_TARGETS} targets")
    viewport = config.get("viewport") or {}
    if not isinstance(viewport, dict):
        raise ValueError("viewport must be an object")
    normalized: dict[str, Any] = {
        "viewport": {
            "width": _bounded_int(viewport.get("width", 1280), "width", MIN_VIEWPORT, MAX_VIEWPORT),
            "height": _bounded_int(viewport.get("height", 800), "height", MIN_VIEWPORT, MAX_VIEWPORT),
        },
        "targets": [_normalize_target(target, workspace) for target in targets],
    }
    result_path = _text(config.get("resultPath"))
    if result_path:
        normalized["resultPath"] = str(
            _workspace_path(result_path, workspace, label="resultPath")
        )
    return normalized


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--config")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--file")
    source.add_argument("--url")
    source.add_argument("--geom-check", metavar="FILE")
    parser.add_argument("--out")
    parser.add_argument("--format", choices=("png", "pdf"))
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=800)
    parser.add_argument("--wait-ms", type=int, default=1000)
    parser.add_argument("--wait-for-selector")
    parser.add_argument("--full-page", action="store_true")
    parser.add_argument("--render-math", action="store_true")
    return parser


def _config_from_args(args: argparse.Namespace, workspace: Path) -> dict[str, Any]:
    if args.config:
        if args.file or args.url or args.geom_check or args.out:
            raise ValueError("--config cannot be combined with a simple capture target")
        path = _workspace_path(args.config, workspace, must_exist=True, label="config")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("capture config is not valid JSON") from exc
        return _normalize_config(raw, workspace)

    source_value = args.geom_check or args.file or args.url
    if not source_value:
        raise ValueError("provide --config, --file, --url, or --geom-check")
    target: dict[str, Any] = {
        "out": args.out,
        "format": args.format,
        "waitMs": args.wait_ms,
        "waitForSelector": args.wait_for_selector,
        "fullPage": args.full_page,
        "renderMath": args.render_math,
        "geomCheck": bool(args.geom_check),
    }
    target["file" if args.geom_check or args.file else "url"] = source_value
    return _normalize_config(
        {"viewport": {"width": args.width, "height": args.height}, "targets": [target]},
        workspace,
    )


def _command(runtime: CaptureRuntime, config_path: Path) -> list[str]:
    command = [str(runtime.executable)]
    if runtime.capture_script is not None:
        command.append(str(runtime.capture_script))
    command.extend(["--mh-capture", str(config_path)])
    return command


def _capture_timeout(config: dict[str, Any]) -> int:
    return min(1800, max(120, 90 * len(config.get("targets", []))))


def _read_result(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {"results": [], "error": f"capture result unavailable: {str(exc)[:300]}"}
    if not isinstance(value, dict) or not isinstance(value.get("results"), list):
        return {"results": [], "error": "capture result has an invalid structure"}
    return value


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(sys.argv[1:] if argv is None else argv)
    try:
        runtime = _resolve_runtime()
        if args.check:
            print(f"CAPTURE_READY: {runtime.executable}")
            return 0
        workspace = Path.cwd().resolve()
        config = _config_from_args(args, workspace)
        temporary_result = "resultPath" not in config
        if temporary_result:
            with tempfile.NamedTemporaryFile(
                suffix=".json", prefix="modickx-capture-result-", dir=workspace, delete=False
            ) as result_handle:
                result_path = Path(result_handle.name)
            config["resultPath"] = str(result_path)
        else:
            result_path = Path(str(config["resultPath"]))
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", prefix="modickx-capture-", dir=workspace,
            encoding="utf-8", delete=False
        ) as handle:
            json.dump(config, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            config_path = Path(handle.name)
        try:
            completed = subprocess.run(
                _command(runtime, config_path),
                cwd=str(workspace),
                timeout=_capture_timeout(config),
            )
            print(json.dumps(_read_result(result_path), ensure_ascii=False, indent=2))
        finally:
            config_path.unlink(missing_ok=True)
            if temporary_result:
                result_path.unlink(missing_ok=True)
        return int(completed.returncode)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"CAPTURE_UNAVAILABLE: {str(exc)[:500]}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
