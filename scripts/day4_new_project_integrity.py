"""Compare Day 3 tracked files; only the documented Day 4 surface may change."""

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "c096ccd946ed926cf2161d0a9b6180d22c91bd9c"
ALLOWED = {
    "backend/app/main.py", "backend/requirements.lock.txt", "frontend/package.json", "frontend/pnpm-lock.yaml",
    "frontend/src/config/modules.ts", "frontend/src/platform/PlatformPreview.tsx",
    "scripts/browser_smoke.py", "scripts/day3_security_check.py", "scripts/verify_production.py",
    "tests/test_deepseek_day3.py", "tests/test_preview_api.py", "docs/dependency_licenses.json",
    "docs/frontend_resolved_graph.json",
}
PROTECTED = {"LICENSE", "backend/app/deepseek.py", "scripts/check_deepseek_connectivity.py",
    "scripts/start-local.ps1", "scripts/stop-local.ps1", "scripts/local-service.py", "scripts/local-runtime.ps1",
    "frontend/vite.config.ts", "frontend/src/config/brand.ts", "docs/production_baseline.json",
    "docs/day3_api_connectivity_result.json", "docs/day3_secret_boundary_result.json"}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8")


def main():
    tracked = git("ls-tree", "-r", "--name-only", BASE).splitlines()
    changed = sorted(set(git("diff", "--name-only", BASE, "--").splitlines()) & set(tracked))
    unexpected = sorted(set(changed) - ALLOWED)
    # Git diff normalizes line endings; SHA256 additionally records current bytes.
    protected = {name: {"unchanged": name in tracked and name not in changed,
                        "sha256": hashlib.sha256((ROOT / name).read_bytes()).hexdigest()}
                 for name in sorted(PROTECTED) if (ROOT / name).is_file()}
    result = {"day3_commit": BASE, "day3_tracked_files": len(tracked),
              "expected_modified_files": sorted(set(changed) & ALLOWED),
              "unexpected_modified_files": unexpected, "protected_files": protected,
              "day3_branch_unchanged": git("rev-parse", "day3/deepseek-security").strip() == BASE,
              "passed": not unexpected and len(protected) == len(PROTECTED)
                        and all(item["unchanged"] for item in protected.values())}
    (ROOT / "docs/day4_new_project_integrity.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "protected_files"}))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
