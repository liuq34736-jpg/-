"""Read-only SHA-256 verification. Never serializes production row contents."""

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--day4", action="store_true", help="Keep the prior integrity report unchanged.")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    baseline = json.loads((root / "docs/production_baseline.json").read_text(encoding="utf-8"))
    production = Path(baseline["production_root"])
    changed = []
    for relative, expected in baseline["files_sha256"].items():
        path = Path(relative) if Path(relative).is_absolute() else production / relative
        if not path.is_file() or digest(path) != expected:
            changed.append(relative)
    cache_root = production.parent / "资料源/runtime_cache"
    changed_cache = [name for name, expected in baseline["signed_cache_sha256"].items() if not (cache_root / name).is_file() or digest(cache_root / name) != expected]
    history = baseline["history"]
    database = Path(history["path"])
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("SELECT * FROM readings ORDER BY id").fetchall()
        columns = [row[1] for row in connection.execute("PRAGMA table_info(readings)")]
    row_hashes = {
        str(row["id"]): hashlib.sha256(json.dumps(dict(row), sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
        for row in rows
    }
    result = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "production_files": len(baseline["files_sha256"]), "changed_production_files": changed,
        "signed_cache_files": len(baseline["signed_cache_sha256"]), "changed_signed_cache_files": changed_cache,
        "history_rows": len(rows), "history_schema_unchanged": columns == history["columns"],
        "history_row_hashes_unchanged": row_hashes == history["row_hashes"],
        "history_database_bytes_unchanged": digest(database) == history["file_sha256"],
    }
    result["passed"] = not changed and not changed_cache and all(result[name] for name in ("history_schema_unchanged", "history_row_hashes_unchanged", "history_database_bytes_unchanged"))
    report = "day4_production_integrity_result.json" if args.day4 else "production_integrity_result.json"
    (root / "docs" / report).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
