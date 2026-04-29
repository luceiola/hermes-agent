from __future__ import annotations

import argparse
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from tools.homework_eval.providers.baidu_correct_edu import BaiduCorrectEduProvider
from tools.homework_eval.providers.zhipu_homework import ZhipuHomeworkProvider
from tools.homework_eval.schema import CompareOutput, ProviderResult
from tools.homework_eval.utils import merge_env, now_ms


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Baidu + Zhipu homework correction APIs with a unified output schema"
    )
    parser.add_argument("--image-url", help="Public image URL for homework page")
    parser.add_argument("--image-file", help="Local image file path")
    parser.add_argument("--providers", default="baidu,zhipu", help="Comma-separated: baidu,zhipu")
    parser.add_argument("--profile", help="Load env from ~/.hermes/profiles/<profile>/.env")
    parser.add_argument("--env-file", action="append", default=[], help="Additional env file path, repeatable")
    parser.add_argument("--timeout-sec", type=int, default=30)
    parser.add_argument("--poll-interval-sec", type=int, default=5)
    parser.add_argument("--poll-attempts", type=int, default=24)
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("--no-raw", action="store_true", help="Hide raw payload in output")
    return parser.parse_args()


def build_env_paths(args: argparse.Namespace) -> list[Path]:
    paths: list[Path] = []
    if args.profile:
        paths.append(Path.home() / ".hermes" / "profiles" / args.profile / ".env")
    for item in args.env_file:
        paths.append(Path(item).expanduser())
    default_local = Path.cwd() / ".env.homework"
    if default_local.exists():
        paths.append(default_local)
    return paths


def main() -> int:
    args = parse_args()

    if not args.image_url and not args.image_file:
        print("--image-url or --image-file is required")
        return 2

    env = merge_env(build_env_paths(args))

    provider_builders: dict[str, Callable[[], object]] = {
        "baidu": lambda: BaiduCorrectEduProvider(
            env=env,
            timeout_sec=args.timeout_sec,
            poll_interval_sec=args.poll_interval_sec,
            poll_attempts=args.poll_attempts,
        ),
        "zhipu": lambda: ZhipuHomeworkProvider(env=env, timeout_sec=args.timeout_sec),
    }

    requested = [item.strip().lower() for item in args.providers.split(",") if item.strip()]
    outputs: list[ProviderResult] = []
    started_at = utc_now_iso()
    start_ms = now_ms()

    for key in requested:
        builder = provider_builders.get(key)
        if builder is None:
            outputs.append(
                ProviderResult(
                    provider=key,
                    success=False,
                    elapsed_ms=0,
                    errors=[f"Unsupported provider: {key}"],
                )
            )
            continue

        try:
            provider = builder()
            result = provider.run(image_url=args.image_url, image_file=args.image_file)
            outputs.append(result)
        except Exception as exc:
            outputs.append(
                ProviderResult(
                    provider=key,
                    success=False,
                    elapsed_ms=now_ms() - start_ms,
                    errors=[f"Unhandled exception: {exc}", traceback.format_exc()],
                )
            )

    payload = CompareOutput(
        image_url=args.image_url,
        image_file=args.image_file,
        started_at=started_at,
        finished_at=utc_now_iso(),
        outputs=outputs,
    ).to_dict(include_raw=not args.no_raw)

    if args.pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
