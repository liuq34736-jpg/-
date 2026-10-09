"""Existing production baseline + Day 6B Git baseline; explicit UI/API edits only."""

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def inspect():
    baseline = json.loads((ROOT / "docs/day7a_day6b_baseline.json").read_bytes())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    changed = [p for p, h in baseline["files_sha256"].items() if not (ROOT / p).is_file() or sha(ROOT / p) != h]
    unexpected = sorted(set(changed) - set(baseline["allowed_modified_files"]))
    from scripts.day6a_integrity_check import inspect as old_inspect
    old = old_inspect()  # Reads existing baselines, no artifact rewriting.
    protection = {k: old[k] for k in ("production_files", "changed_production_files", "signed_cache_files", "changed_signed_cache_files",
        "history_rows", "history_schema_unchanged", "history_row_hashes_unchanged", "history_database_bytes_unchanged", "git_safety")}
    result = {"day6b_commit": baseline["git_commit"], "day6b_tracked_files": len(baseline["files_sha256"]),
              "allowed_modified_files": baseline["allowed_modified_files"], "modified_baseline_files": changed,
              "unexpected_modified_files": unexpected, "old_rulebooks_reviews_engines_frames_preserved": not unexpected,
              **protection, "real_ai_calls": 0}
    result["passed"] = not unexpected and not old["changed_production_files"] and not old["changed_signed_cache_files"] and old["git_safety"]["passed"] and all(old[k] for k in
        ("history_schema_unchanged", "history_row_hashes_unchanged", "history_database_bytes_unchanged")) and old["history_rows"] == 42
    return result


if __name__ == "__main__":
    result = inspect()
    (ROOT / "docs/day7a_integrity_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(int(not result["passed"]))
