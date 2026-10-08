"""Fixed one-shot Day 3 diagnostic; no free prompts, raw responses or headers."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.deepseek import DeepSeekConfig, DeepSeekConnectivityProvider, load_config


def run_real_once():
    config = load_config()
    if not config.configured:
        return {"executed": False, "reason": "not_configured"}
    runtime = ROOT / "runtime"
    runtime.mkdir(exist_ok=True)
    marker = runtime / "day3_real_api_attempt.json"
    try:
        descriptor = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return {"executed": False, "reason": "already_attempted"}
    with os.fdopen(descriptor, "w", encoding="utf-8") as file:
        json.dump({"started_at": datetime.now(timezone.utc).isoformat(), "maximum_calls": 1}, file)
    result = DeepSeekConnectivityProvider(config).check_connection().public_record()
    report = {"mode": "real", "executed": True, **result, "cost": "unavailable",
              "raw_response_saved": False, "credentials_saved": False,
              "formal_reading_generated": False}
    (ROOT / "docs/day3_api_connectivity_result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def run_mock():
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def read(self, _):
            return json.dumps({"choices": [{"finish_reason": "stop", "message": {"content": '{"status":"ok"}'}}],
                               "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}}).encode()
    provider = DeepSeekConnectivityProvider(DeepSeekConfig(api_key="SYNTHETIC_TEST_VALUE"), transport=lambda *_a, **_k: Response())
    return {"mode": "mock", "executed": True, **provider.check_connection().public_record()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--mock", action="store_true")
    group.add_argument("--real", action="store_true")
    args = parser.parse_args()
    result = run_real_once() if args.real else run_mock()
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result.get("success") else 1)
