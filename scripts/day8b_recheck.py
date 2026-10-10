"""Day8A verification, with new Day8B reports only; never a paid API runner."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def child(kind):
    environment = {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP"}}
    # The old /config route performs a server credential lookup. Supply an
    # explicit synthetic value so offline tests cannot fall back to the user's
    # Windows registry credential. Networking is separately denied by the suite.
    environment["DEEPSEEK_API_KEY"] = "SYNTHETIC_DAY8B_CONFIG_CHECK"
    run = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(Path(__file__).resolve()), kind, "--worker"],
                         env=environment, cwd=ROOT, capture_output=True, timeout=240,
                         creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    value = json.loads(run.stdout)
    if run.returncode:
        value["runner_failed"] = True
    return value


def baseline():
    names = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "-z", "16d2809"], cwd=ROOT).decode().split("\0")
    return {n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names if n}


def main():
    if len(sys.argv) == 3 and sys.argv[2] == "--worker":
        if sys.argv[1] == "unit":
            from scripts.day5_offline_acceptance import unit_worker
            value = unit_worker()  # All existing tests; protected writes/network denied.
        elif sys.argv[1] == "failures":
            from unittest.mock import patch
            from scripts import day8a_quality_evaluation
            original_write = Path.write_text
            def redirect(path, data, *args, **kwargs):
                if path.resolve() != (ROOT/'docs/day8a_quality_evaluation_results.json').resolve():
                    raise PermissionError("unexpected_report_write")
                return original_write(ROOT/'docs/day8b_failure_recheck_results.json', data, *args, **kwargs)
            with patch.object(Path, "write_text", redirect):
                failed = day8a_quality_evaluation.main()
            value = json.loads((ROOT/'docs/day8b_failure_recheck_results.json').read_bytes())
            return failed  # The existing script already printed safe counts.
        else:
            raise ValueError("unknown_offline_check")
        print(json.dumps(value, ensure_ascii=True))
        return int(bool(value.get("failed")))

    before = baseline()
    unit = child("unit")
    failures = child("failures")
    # These functions read existing baselines and SQLite in mode=ro. No old main()
    # is called, so none of the previous stage's reports are overwritten.
    assert (ROOT/'docs/day6a_day5_baseline.json').is_file()
    from scripts.day6a_integrity_check import inspect
    integrity = inspect()
    after = baseline()
    changed = [n for n in before if before[n] != after[n]]
    result = {"base_commit": "16d2809", "baseline_files": len(before), "changed_baseline_files": changed,
        "unit": unit, "failure_replay": failures,
        "production_files": integrity['production_files'], "changed_production_files": integrity['changed_production_files'],
        "signed_cache_files": integrity['signed_cache_files'], "changed_signed_cache_files": integrity['changed_signed_cache_files'],
        **{k: integrity[k] for k in ('history_rows', 'history_schema_unchanged', 'history_row_hashes_unchanged', 'history_database_bytes_unchanged', 'git_safety')},
        "real_ai_calls": 0, "new_unit_tests": 0,
        "scope": "all_existing_offline_unit_tests_and_old_failure_replay; no_Chrome_or_real_AI_quality_claim"}
    result['passed'] = (not changed and unit.get('failed') == 0 and failures.get('failed') == 0
        and not integrity['changed_production_files'] and not integrity['changed_signed_cache_files']
        and integrity['history_rows'] == 42 and integrity['git_safety']['passed'] and all(integrity[k] for k in
        ('history_schema_unchanged', 'history_row_hashes_unchanged', 'history_database_bytes_unchanged')))
    (ROOT/'docs/day8b_recheck_results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'git_safety'}, ensure_ascii=False))
    return int(not result['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
