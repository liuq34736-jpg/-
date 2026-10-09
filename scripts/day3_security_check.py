"""Exact in-memory credential comparison; output only counts and safe paths."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.deepseek import load_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--day4", action="store_true", help="Keep Day 3 evidence unchanged.")
    args = parser.parse_args()
    credential = load_config().api_key.encode("utf-8")
    candidates = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    paths = {ROOT / name for name in candidates if name and (ROOT / name).is_file()}
    paths.update((ROOT / "runtime").glob("*.log"))
    paths.update((ROOT / "runtime").glob("*.json"))
    paths.update(path for path in (ROOT / "frontend/dist").rglob("*") if path.is_file())
    leaked = []
    for path in paths:
        if credential and credential in path.read_bytes():
            leaked.append(str(path.relative_to(ROOT)))
    result = {"files_checked": len(paths), "credential_available_for_in_memory_check": bool(credential),
              "credential_match_count": len(leaked), "affected_paths": sorted(leaked),
              "scope": "current Git candidates, new-project runtime logs/receipts and frontend build artifacts",
              "passed": not leaked}
    report = "day4_secret_boundary_result.json" if args.day4 else "day3_secret_boundary_result.json"
    (ROOT / "docs" / report).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 1 if leaked else 0


if __name__ == "__main__":
    raise SystemExit(main())
