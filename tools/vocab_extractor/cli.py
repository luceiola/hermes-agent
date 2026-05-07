from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.homework_eval.utils import merge_env
from tools.vocab_extractor.doubao_client import QwenVisionClient
from tools.vocab_extractor.pipeline import ensure_output_dir, result_to_jsonable, run_extraction
from tools.vocab_extractor.render import build_markdown, build_pdf, write_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract marked vocabulary from reading materials via Qwen multimodal model")
    parser.add_argument("--image-url", help="Image URL")
    parser.add_argument("--image-file", help="Local image or PDF path")
    parser.add_argument("--profile", help="Load env from ~/.hermes/profiles/<profile>/.env")
    parser.add_argument("--env-file", action="append", default=[], help="Additional env file")
    parser.add_argument("--output-dir", default="artifacts/vocab_extractor")
    parser.add_argument("--threshold", type=float, default=0.75)
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--timeout-sec", type=int, default=60)
    parser.add_argument("--skip-pdf", action="store_true", help="Skip PDF generation")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def env_paths(args: argparse.Namespace) -> list[Path]:
    paths: list[Path] = []
    if args.profile:
        paths.append(Path.home() / ".hermes" / "profiles" / args.profile / ".env")
    for item in args.env_file:
        paths.append(Path(item).expanduser())
    if Path.cwd().joinpath(".env.vocab").exists():
        paths.append(Path.cwd() / ".env.vocab")
    return paths


def main() -> int:
    args = parse_args()

    if not args.image_url and not args.image_file:
        print("--image-url or --image-file is required")
        return 2

    env = merge_env(env_paths(args))
    # Stage 1 (vision detect): prefer VOCAB_* so vocab extraction can be routed
    # to an independent multimodal endpoint.
    api_key = env.get("VOCAB_API_KEY") or env.get("API_KEY")
    model = env.get("VOCAB_MODEL") or env.get("MODEL")
    base_url = env.get("VOCAB_BASE_URL") or env.get("BASE_URL")
    # Stage 2 (text enrich): prefer main model/provider to avoid heavy
    # multimodal completion latency.
    enrich_api_key = env.get("API_KEY") or api_key
    enrich_model = env.get("MODEL") or model
    enrich_base_url = env.get("BASE_URL") or base_url

    if not api_key:
        print("Missing VOCAB_API_KEY (or API_KEY)")
        return 2
    if not model:
        print("Missing VOCAB_MODEL (or MODEL)")
        return 2
    if not base_url:
        print("Missing VOCAB_BASE_URL (or BASE_URL)")
        return 2

    client = QwenVisionClient(
        api_key=api_key,
        model=model,
        base_url=base_url,
        timeout_sec=args.timeout_sec,
        enrich_api_key=enrich_api_key,
        enrich_model=enrich_model,
        enrich_base_url=enrich_base_url,
        enrich_timeout_sec=max(args.timeout_sec, 45),
    )

    result, provider_raw = run_extraction(
        client=client,
        image_url=args.image_url,
        image_file=args.image_file,
        threshold=args.threshold,
        max_pages=args.max_pages,
    )

    out_dir = ensure_output_dir(args.output_dir)
    json_path = out_dir / f"{result.task_id}.json"
    markdown_path = out_dir / f"{result.task_id}.md"
    pdf_path = out_dir / f"{result.task_id}.pdf"
    raw_path = out_dir / f"{result.task_id}.raw.json"

    markdown_text = build_markdown(result)
    write_markdown(markdown_path, markdown_text)

    if not args.skip_pdf:
        build_pdf(result, pdf_path)

    json_payload = result_to_jsonable(result)
    result.artifacts = {
        "json": str(json_path),
        "markdown": str(markdown_path),
    }
    if not args.skip_pdf:
        result.artifacts["pdf"] = str(pdf_path)

    json_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    raw_path.write_text(json.dumps(provider_raw, ensure_ascii=False, indent=2), encoding="utf-8")

    output = {
        "task_id": result.task_id,
        "summary": result.summary,
        "artifacts": result.artifacts,
        "errors": result.errors,
    }
    if args.pretty:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(output, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
