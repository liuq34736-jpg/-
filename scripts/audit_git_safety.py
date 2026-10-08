"""Check the Git candidate set without printing content or credential values."""

import argparse
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECRET = re.compile(rb"(?:sk-(?:proj-)?[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)")
PRIVATE_NAMES = {".env", "secrets.toml"}
PRIVATE_DIRS = {"runtime", "cache", "caches", ".cache", ".venv", "node_modules", "logs", "private", "__pycache__"}
PRIVATE_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".log", ".pem", ".key", ".pfx"}


def inspect_git(staged=False):
    if staged:
        args = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"]
    else:
        args = ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
    files = sorted(set(subprocess.check_output(args, cwd=ROOT).decode("utf-8").split("\0")) - {""})
    findings = []
    for name in files:
        path = Path(name)
        cache_source = path.parts[:2] == ("src", "cache") and path.suffix == ".py"
        blocked_dirs = PRIVATE_DIRS.intersection(path.parts) - ({"cache"} if cache_source else set())
        if path.name in PRIVATE_NAMES or path.name.startswith(".env.") or path.suffix.lower() in PRIVATE_SUFFIXES or blocked_dirs or ".sqlite3-" in path.name or ".sqlite-" in path.name or ".db-" in path.name:
            findings.append({"path": name, "reason": "private_or_runtime_file"})
            continue
        if staged:
            data = subprocess.check_output(["git", "show", f":{name}"], cwd=ROOT)
        elif (ROOT / path).is_file():
            data = (ROOT / path).read_bytes()
        else:
            continue
        # Binary assets are reviewed as screenshots, not decoded as text.
        if b"\0" not in data and SECRET.search(data):
            findings.append({"path": name, "reason": "credential_pattern"})
    return {"mode": "staged" if staged else "candidate", "files_checked": len(files), "findings": findings, "passed": not findings}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--staged", action="store_true")
    options = parser.parse_args()
    result = inspect_git(options.staged)
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result["passed"] else 1)
