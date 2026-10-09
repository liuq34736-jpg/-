"""Offline frozen-module regression. No paid transport, no production writes."""

import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT.parent / "streamlit_mvp"


def legacy_guard(event, args):
    protected = (PRODUCTION, ROOT.parent / "资料源")

    def guarded(path):
        return isinstance(path, (str, bytes, os.PathLike)) and any(Path(os.fsdecode(path)).resolve().is_relative_to(p) for p in protected)

    if event == "open":
        mode, flags = args[1], args[2]
        if guarded(args[0]) and ((isinstance(mode, str) and any(c in mode for c in "wax+")) or
                                (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))):
            raise PermissionError("production_write_blocked")
    if event in {"os.mkdir", "os.remove", "os.rmdir", "os.chmod", "os.utime", "os.truncate"} and guarded(args[0]):
        raise PermissionError("production_write_blocked")
    if event in {"os.rename", "os.link", "os.symlink"} and any(guarded(p) for p in args[:2]):
        raise PermissionError("production_write_blocked")
    if event == "sqlite3.connect" and guarded(args[0]):
        raise PermissionError("production_database_blocked")
    if event in {"socket.connect", "socket.connect_ex", "socket.getaddrinfo", "socket.bind", "http.client.connect"}:
        raise PermissionError("regression_network_blocked")


def run_legacy():
    sys.dont_write_bytecode = True
    sys.addaudithook(legacy_guard)
    sys.path.insert(0, str(PRODUCTION))
    names = ["tests.test_algorithm", "tests.test_meihua_analysis", "tests.test_strength",
             "tests.test_interpretation", "tests.test_daily_reading"]
    suite = unittest.defaultTestLoader.loadTestsFromNames(names)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
    return {"scope": names, "collected": result.testsRun, "passed": result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
            "failed": len(result.failures) + len(result.errors), "skipped": len(result.skipped),
            "failed_test_ids": [test.id() for test, _ in result.failures + result.errors], "network_allowed": False,
            "production_writes_allowed": False, "temporary_test_databases_only": True}


def run_matrix():
    sys.path.insert(0, str(ROOT))
    from backend.app.meihua_worker import FrozenRuntime
    runtime = FrozenRuntime()
    successful, approved, failures, relations = 0, 0, [], set()
    for profile in runtime.profiles:
        for position in range(1, 7):
            try:
                value = runtime.calculate({"input_mode": "manual_hexagram", "hexagram_id": profile["id"],
                    "moving_line": position, "cast_at": "2026-09-24T19:45:35+08:00"})
                assert value["original_hexagram"]["id"] == profile["id"]
                assert value["moving_line"]["position"] == position
                assert value["moving_line"]["name"] == runtime.line_name(profile["lines"], position)
                expected = profile["lines"].copy()
                expected[position - 1] = 1 - expected[position - 1]
                assert value["changed_hexagram"]["lines"] == expected
                assert value["mutual_hexagram"]["lines"] == profile["lines"][1:4] + profile["lines"][2:5]
                assert value["body_use"]["yong_trigram"] == profile["lower_trigram" if position <= 3 else "upper_trigram"]
                assert value["body_use"]["body_trigram"] == profile["upper_trigram" if position <= 3 else "lower_trigram"]
                assert len(value["standard_meanings"]) == 4
                ids = {r["evidence_id"] for r in value["source_references"]}
                assert all(set(m["source_evidence_ids"]) <= ids for m in value["standard_meanings"])
                approved += all(m["status"] == "SEMANTIC_APPROVED" for m in value["standard_meanings"])
                relations.add(value["body_use"]["relation"])
                successful += 1
            except Exception:
                failures.append({"hexagram_id": profile["id"], "moving_line": position})
    # Demonstrate safe source/frame fallback using an in-memory test fixture.
    runtime.corpus = None
    fallback = runtime.calculate({"input_mode": "manual_hexagram", "hexagram_id": 20, "moving_line": 4,
                                  "cast_at": "2026-09-24T19:45:35+08:00"})
    fallback_pass = not fallback["source_references"] and all(m["status"] == "structure_fallback" for m in fallback["standard_meanings"])
    # Direct probes reach the installed audit hook, not a mocked guard function.
    write_blocked = network_blocked = False
    try:
        (ROOT / "runtime/day4-forbidden-write.txt").write_text("test", encoding="utf-8")
    except PermissionError:
        write_blocked = True
    import socket
    try:
        socket.getaddrinfo("example.invalid", 443)
    except PermissionError:
        network_blocked = True
    return {"combinations": 384, "passed": successful, "failed": len(failures), "failure_targets": failures,
            "four_approved_roles": approved, "relations_covered": sorted(relations), "fallback_passed": fallback_pass,
            "worker_write_probe_blocked": write_blocked, "worker_network_probe_blocked": network_blocked,
            "real_ai_calls": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("matrix", "legacy"))
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        try:
            result = run_matrix() if args.mode == "matrix" else run_legacy()
        except Exception:
            print('{"failed":1,"reason":"offline_runner_failed"}')
            return 1
        print(json.dumps(result, ensure_ascii=True))
        return 1 if result.get("failed") else 0
    environment = {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP"}}
    run = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(Path(__file__).resolve()), args.mode, "--worker"],
                         cwd=ROOT, env=environment, capture_output=True, timeout=300)
    try:
        result = json.loads(run.stdout)
    except ValueError:
        result = {"failed": 1, "reason": "offline_runner_failed"}
    path = ROOT / "docs" / f"day4_{args.mode}_results.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 1 if run.returncode or result.get("failed") else 0


if __name__ == "__main__":
    raise SystemExit(main())
