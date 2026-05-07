#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
VALID_IMAGE_ID = re.compile(r"^img_[0-9a-zA-Z]+$")
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".bmp")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Heidou vocab command router: #img_xxx -> vocab extractor"
    )
    sub = parser.add_subparsers(dest="action", required=True)

    def add_common_flags(p: argparse.ArgumentParser) -> None:
        p.add_argument("--profile", default="heidou")
        p.add_argument(
            "--image-id",
            default="",
            help="img_xxx or #img_xxx; empty means use the latest cached image",
        )
        p.add_argument("--threshold", type=float, default=0.75)
        p.add_argument("--max-pages", type=int, default=3)
        p.add_argument("--timeout-sec", type=int, default=120)

    add_common_flags(sub.add_parser("extract", help="Run extraction and emit summary"))
    add_common_flags(
        sub.add_parser(
            "extract-and-export",
            help="Run extraction and ensure PDF is generated",
        )
    )
    add_common_flags(
        sub.add_parser(
            "export-pdf",
            help="Return existing PDF if present; otherwise run extraction",
        )
    )
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def profile_home(profile: str) -> Path:
    return Path.home() / ".hermes" / "profiles" / profile


def state_file(profile: str) -> Path:
    return profile_home(profile) / "cache" / "vocab_router_state.json"


def load_state(profile: str) -> dict[str, Any]:
    path = state_file(profile)
    if not path.exists():
        return {"images": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("images"), dict):
            return data
    except Exception:
        pass
    return {"images": {}}


def save_state(profile: str, data: dict[str, Any]) -> None:
    path = state_file(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def normalize_image_id(raw: str) -> str:
    value = (raw or "").strip()
    if value.startswith("#"):
        value = value[1:]
    if not VALID_IMAGE_ID.fullmatch(value):
        raise ValueError(f"Invalid image id: {raw!r}. Expected format: #img_xxx")
    return value


def resolve_latest_image_id(profile: str) -> str:
    cache_dir = profile_home(profile) / "cache" / "images"
    if not cache_dir.exists():
        raise FileNotFoundError(f"Image cache dir not found: {cache_dir}")
    candidates: list[Path] = []
    for ext in IMAGE_EXTS:
        candidates.extend(cache_dir.glob(f"*{ext}"))
    if not candidates:
        raise FileNotFoundError("No cached image found; please send an image first.")
    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    image_id = latest.stem
    if not VALID_IMAGE_ID.fullmatch(image_id):
        raise RuntimeError(f"Latest cached image does not look like img_xxx: {latest.name}")
    return image_id


def resolve_target_image_id(profile: str, raw_image_id: str) -> str:
    if (raw_image_id or "").strip():
        return normalize_image_id(raw_image_id)
    return resolve_latest_image_id(profile)


def resolve_image_path(profile: str, image_id: str) -> Path:
    cache_dir = profile_home(profile) / "cache" / "images"
    if not cache_dir.exists():
        raise FileNotFoundError(f"Image cache dir not found: {cache_dir}")

    for ext in IMAGE_EXTS:
        candidate = cache_dir / f"{image_id}{ext}"
        if candidate.exists():
            return candidate

    candidates = sorted(cache_dir.glob(f"{image_id}.*"))
    if not candidates:
        raise FileNotFoundError(f"Image not found in cache: {image_id}")
    if len(candidates) > 1:
        names = ", ".join(p.name for p in candidates)
        raise RuntimeError(f"Multiple image files matched for {image_id}: {names}")
    return candidates[0]


def safe_load_json(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def run_extractor(
    *,
    profile: str,
    image_path: Path,
    threshold: float,
    max_pages: int,
    timeout_sec: int,
) -> dict[str, Any]:
    cmd = [
        sys.executable,
        "-m",
        "tools.vocab_extractor",
        "--profile",
        profile,
        "--image-file",
        str(image_path),
        "--threshold",
        str(threshold),
        "--max-pages",
        str(max_pages),
        "--timeout-sec",
        str(timeout_sec),
        "--pretty",
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )

    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()

    payload: dict[str, Any] = {}
    parse_error = ""
    if stdout:
        try:
            obj = json.loads(stdout)
            if isinstance(obj, dict):
                payload = obj
            else:
                parse_error = "Extractor output is not a JSON object"
        except Exception as exc:
            parse_error = f"Could not parse extractor JSON output: {exc}"
    else:
        parse_error = "Extractor output is empty"

    return {
        "ok": proc.returncode == 0 and not parse_error,
        "returncode": proc.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "payload": payload,
        "parse_error": parse_error,
        "command": cmd,
    }


def summarise_payload(payload: dict[str, Any]) -> dict[str, Any]:
    artifacts = payload.get("artifacts") or {}
    summary = payload.get("summary") or {}
    result_file = safe_load_json(str(artifacts.get("json", "")))
    items_main = result_file.get("items_main") or []
    items_suspected = result_file.get("items_suspected") or []

    def preview(items: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for item in items[:limit]:
            out.append(
                {
                    "word": item.get("word"),
                    "meaning_zh": item.get("meaning_zh"),
                    "confidence": item.get("confidence"),
                }
            )
        return out

    return {
        "task_id": payload.get("task_id"),
        "summary": summary,
        "artifacts": artifacts,
        "errors": payload.get("errors") or [],
        "main_preview": preview(items_main),
        "suspected_preview": preview(items_suspected),
    }


def emit(output: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return code


def handle_extract(args: argparse.Namespace) -> int:
    image_id = resolve_target_image_id(args.profile, args.image_id)
    image_path = resolve_image_path(args.profile, image_id)
    run = run_extractor(
        profile=args.profile,
        image_path=image_path,
        threshold=args.threshold,
        max_pages=args.max_pages,
        timeout_sec=args.timeout_sec,
    )
    if not run["ok"]:
        return emit(
            {
                "ok": False,
                "action": "extract",
                "profile": args.profile,
                "image_id": image_id,
                "image_path": str(image_path),
                "error": run["parse_error"] or "extractor failed",
                "returncode": run["returncode"],
                "stderr": run["stderr"],
                "stdout": run["stdout"][:4000],
            },
            code=1,
        )

    summary = summarise_payload(run["payload"])
    errors = summary.get("errors") or []
    total_detected = int((summary.get("summary") or {}).get("total_detected") or 0)
    enrich_only_errors = bool(errors) and all(str(e).startswith("enrich:") for e in errors)
    partial_ok = enrich_only_errors and total_detected > 0

    if errors and not partial_ok:
        state = load_state(args.profile)
        if image_id in (state.get("images") or {}):
            state["images"].pop(image_id, None)
            save_state(args.profile, state)
        return emit(
            {
                "ok": False,
                "action": "extract",
                "profile": args.profile,
                "image_id": image_id,
                "image_path": str(image_path),
                **summary,
                "error": "extractor returned errors",
            },
            code=1,
        )

    state = load_state(args.profile)
    state.setdefault("images", {})[image_id] = {
        "updated_at": now_iso(),
        "task_id": summary.get("task_id"),
        "image_path": str(image_path),
        "artifacts": summary.get("artifacts"),
        "summary": summary.get("summary"),
    }
    save_state(args.profile, state)

    if partial_ok:
        summary["warnings"] = ["enrich_partial_timeout"]

    return emit(
        {
            "ok": True,
            "action": "extract",
            "profile": args.profile,
            "image_id": image_id,
            "image_path": str(image_path),
            **summary,
        },
        code=0,
    )


def handle_export_pdf(args: argparse.Namespace) -> int:
    image_id = resolve_target_image_id(args.profile, args.image_id)
    state = load_state(args.profile)
    image_state = (state.get("images") or {}).get(image_id) or {}
    pdf_path = (
        ((image_state.get("artifacts") or {}).get("pdf"))
        if isinstance(image_state, dict)
        else None
    )
    cache_ok = False
    if pdf_path and Path(pdf_path).exists():
        json_path = ((image_state.get("artifacts") or {}).get("json")) if isinstance(image_state, dict) else None
        if json_path and Path(json_path).exists():
            json_payload = safe_load_json(str(json_path))
            cache_ok = not bool(json_payload.get("errors"))
        else:
            cache_ok = False

    if cache_ok:
        return emit(
            {
                "ok": True,
                "action": "export-pdf",
                "profile": args.profile,
                "image_id": image_id,
                "task_id": image_state.get("task_id"),
                "artifacts": image_state.get("artifacts"),
                "summary": image_state.get("summary"),
                "source": "state-cache",
            },
            code=0,
        )

    return handle_extract(args)


def main() -> int:
    args = parse_args()
    try:
        if args.action in ("extract", "extract-and-export"):
            return handle_extract(args)
        if args.action == "export-pdf":
            return handle_export_pdf(args)
        return emit({"ok": False, "error": f"Unknown action: {args.action}"}, code=2)
    except Exception as exc:
        return emit(
            {
                "ok": False,
                "action": getattr(args, "action", ""),
                "error": str(exc),
            },
            code=1,
        )


if __name__ == "__main__":
    raise SystemExit(main())
