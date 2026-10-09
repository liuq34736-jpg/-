"""Pin all Day 6A files and reuse the existing production/history checks read-only."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DAY6A_COMMIT = "00f613af50fbd46fadc2f097b1ff4b098a71de7c"


def inspect():
    paths = [p for p in subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "-z", DAY6A_COMMIT],
             cwd=ROOT).decode("utf-8").split("\0") if p]
    target = ROOT / "docs/day6b_day6a_baseline.json"
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    if not target.exists():
        if subprocess.check_output(["git", "diff", "--name-only", DAY6A_COMMIT, "--", *paths], cwd=ROOT).strip():
            raise ValueError("day6a_changed_before_baseline")
        target.write_text(json.dumps({"git_commit": DAY6A_COMMIT,
            "files_sha256": {p: sha(ROOT / p) for p in paths}}, ensure_ascii=False, indent=2), encoding="utf-8")
    pinned = json.loads(target.read_bytes())
    changed = [p for p, h in pinned["files_sha256"].items() if not (ROOT / p).is_file() or sha(ROOT / p) != h]
    from scripts.day6a_integrity_check import inspect as old_inspect
    previous = old_inspect()  # Existing baseline exists; no old report is rewritten.
    return {**previous, "day6a_commit": DAY6A_COMMIT, "day6a_tracked_files": len(paths),
            "modified_day6a_files": changed, "all_24_review_records_unchanged": not changed,
            "passed": previous["passed"] and not changed}


if __name__ == "__main__":
    result = inspect()
    (ROOT / "docs/day6b_integrity_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "git_safety"}, ensure_ascii=False))
    raise SystemExit(int(not result["passed"]))
