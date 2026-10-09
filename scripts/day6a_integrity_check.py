"""Preserve every tracked Day 5 file and the existing production baseline."""

import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DAY5_COMMIT = "d3c721095f30d1e72ea85f498ade35e4fe1188f1"
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect():
    paths = [p for p in subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", "-z", DAY5_COMMIT], cwd=ROOT
    ).decode("utf-8").split("\0") if p]
    baseline_path = ROOT / "docs/day6a_day5_baseline.json"
    if baseline_path.exists():
        pinned = json.loads(baseline_path.read_bytes())
    else:
        if subprocess.check_output(["git", "diff", "--name-only", DAY5_COMMIT, "--", *paths], cwd=ROOT).strip():
            raise ValueError("day5_baseline_already_changed")
        pinned = {"git_commit": DAY5_COMMIT, "files_sha256": {p: sha(ROOT / p) for p in paths}}
        baseline_path.write_text(json.dumps(pinned, ensure_ascii=False, indent=2), encoding="utf-8")
    changed_new = [p for p, h in pinned["files_sha256"].items() if not (ROOT / p).is_file() or sha(ROOT / p) != h]
    baseline = json.loads((ROOT / "docs/production_baseline.json").read_bytes())
    production = Path(baseline["production_root"])
    changed = [r for r, h in baseline["files_sha256"].items()
               if not (p := Path(r) if Path(r).is_absolute() else production / r).is_file() or sha(p) != h]
    cache = production.parent / "资料源/runtime_cache"
    changed_cache = [r for r, h in baseline["signed_cache_sha256"].items()
                     if not (cache / r).is_file() or sha(cache / r) != h]
    history = baseline["history"]
    database = Path(history["path"])
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("SELECT * FROM readings ORDER BY id").fetchall()
        columns = [r[1] for r in connection.execute("PRAGMA table_info(readings)")]
    hashes = {str(r["id"]): hashlib.sha256(json.dumps(dict(r), ensure_ascii=False, sort_keys=True,
               separators=(",", ":")).encode("utf-8")).hexdigest() for r in rows}
    from scripts.audit_git_safety import inspect_git
    security = inspect_git()
    result = {"day5_commit": DAY5_COMMIT, "day5_tracked_files": len(paths),
              "modified_day5_files": changed_new, "production_files": len(baseline["files_sha256"]),
              "changed_production_files": changed, "signed_cache_files": len(baseline["signed_cache_sha256"]),
              "changed_signed_cache_files": changed_cache, "history_rows": len(rows),
              "history_schema_unchanged": columns == history["columns"],
              "history_row_hashes_unchanged": hashes == history["row_hashes"],
              "history_database_bytes_unchanged": sha(database) == history["file_sha256"],
              "git_safety": security, "api_key_read_or_output_by_this_check": False}
    result["passed"] = (not changed_new and not changed and not changed_cache and security["passed"]
                        and all(result[k] for k in ("history_schema_unchanged", "history_row_hashes_unchanged", "history_database_bytes_unchanged")))
    return result


if __name__ == "__main__":
    result = inspect()
    (ROOT / "docs/day6a_integrity_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(int(not result["passed"]))
