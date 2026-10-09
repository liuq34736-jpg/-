"""Read-only baselines; no history row content, credentials or old reports emitted."""

import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DAY4_COMMIT = "d8227cbe740d6a22f7a4b2890ecd4ab1ba6ddd6c"
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
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
    files = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "-z", DAY4_COMMIT], cwd=ROOT).decode("utf-8").split("\0")
    files = [f for f in files if f]
    # Git's clean conversion handles CRLF without rewriting the worktree.
    changes = subprocess.check_output(["git", "diff", "--name-only", "--diff-filter=MD", DAY4_COMMIT, "--", *files], cwd=ROOT).decode("utf-8").splitlines()
    missing = [f for f in files if not (ROOT / f).is_file()]
    from scripts.audit_git_safety import inspect_git
    security = inspect_git()
    result = {"day4_commit": DAY4_COMMIT, "new_project_baseline_files": len(files),
              "modified_existing_new_project_files": sorted(set(changes + missing)),
              "production_files": len(baseline["files_sha256"]), "changed_production_files": changed,
              "signed_cache_files": len(baseline["signed_cache_sha256"]), "changed_signed_cache_files": changed_cache,
              "history_rows": len(rows), "history_schema_unchanged": columns == history["columns"],
              "history_row_hashes_unchanged": hashes == history["row_hashes"],
              "history_database_bytes_unchanged": sha(database) == history["file_sha256"],
              "git_safety": security,
              "api_key_read_or_output_by_this_check": False}
    result["passed"] = (not changed and not changed_cache and not changes and not missing and security["passed"]
                        and all(result[k] for k in ("history_schema_unchanged", "history_row_hashes_unchanged", "history_database_bytes_unchanged")))
    (ROOT / "docs/day5_integrity_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
