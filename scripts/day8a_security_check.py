"""Credential comparison stays in memory; report contains counts only."""

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from backend.app.deepseek import load_config
    from scripts.audit_git_safety import inspect_git
    credential = load_config().api_key.encode("utf-8")
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    paths = {ROOT / name for name in names if name and (ROOT / name).is_file()}
    paths.update((ROOT / "runtime").glob("*.log"))
    paths.update((ROOT / "runtime").glob("*.json"))
    paths.update(p for p in (ROOT / "frontend/dist").rglob("*") if p.is_file())
    matches = sum(bool(credential and credential in p.read_bytes()) for p in paths)
    del credential
    safety = inspect_git()
    result = {"files_checked": len(paths), "credential_match_count": matches,
              "credential_values_printed_or_saved": False, "credential_check_method": "exact_in_memory_comparison",
              "scope": "new_project_git_candidates_runtime_logs_receipts_frontend_build;_not_windows_system_logs",
              "git_safety": safety, "real_ai_calls": 0, "passed": matches == 0 and safety["passed"]}
    (ROOT / "docs/day8a_security_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "git_safety"}, ensure_ascii=False))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
