"""Repeatable offline tests/evidence. Writes only Day 5 reports, not Day 4 files."""

import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def unit_worker():
    from scripts.day4_offline_checks import legacy_guard
    def guard(event, args):
        if event in {"socket.bind", "socket.connect", "socket.connect_ex", "socket.getaddrinfo"}:
            # Windows asyncio creates a loopback socket pair even for in-memory ASGI.
            # Allow only that local plumbing, never the live app ports or external hosts.
            address = args[1] if event != "socket.getaddrinfo" else args[:2]
            if (isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1", "localhost"}
                    and address[1] not in {5173, 8765}):
                return
        legacy_guard(event, args)
    sys.addaudithook(guard)
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    return {"collected": result.testsRun, "passed": result.testsRun - len(result.errors) - len(result.failures) - len(result.skipped),
            "failed": len(result.errors) + len(result.failures), "skipped": len(result.skipped),
            "failed_test_ids": [t.id() for t, _ in result.errors + result.failures],
            "external_network_allowed": False, "live_app_ports_allowed": False,
            "loopback_event_loop_plumbing_allowed": True, "production_writes_allowed": False, "real_ai_calls": 0}


def probes_worker():
    from backend.app.meihua_worker import FrozenRuntime
    from backend.traditional_judgement_v1.worker import collect
    runtime = FrozenRuntime()
    data = {"input_mode": "manual_hexagram", "hexagram_id": 20, "moving_line": 4, "cast_at": "2026-09-24T19:45:35+08:00"}
    value = collect(runtime, data)
    # Capture a real signed record, then modify it. The old issuer must reject it.
    bundle = runtime.corpus.bundle(20, 4, "primary_change")
    proof = runtime.proof(bundle)
    record = runtime.frame(bundle, proof)
    record["frame"]["core_claims"][0]["text"] = "一定赚一百万元"
    original_frame = runtime.frame
    runtime.frame = lambda b, p: record if b["target_role"] == "primary_change" else original_frame(b, p)
    tampered = collect(runtime, data)
    from backend.traditional_judgement_v1.trusted_input import _issue
    from backend.traditional_judgement_v1.engine import TraditionalJudgementEngine
    # Populate only missing public fields; signing the test DTO never skips old frame validation.
    for v in (value, tampered):
        v["calculation"].update(question_text="", question_applied_to_calculation=False)
    rendered = TraditionalJudgementEngine().evaluate(_issue(tampered)).to_dict()
    blocked = {}
    import socket
    import sqlite3
    attempts = {
        "production_write": lambda: (ROOT.parent / "streamlit_mvp/day5-forbidden-probe.txt").write_text("test"),
        "new_project_write": lambda: (ROOT / "runtime/day5-forbidden-probe.txt").write_text("test"),
        "network": lambda: socket.getaddrinfo("example.invalid", 443),
        "production_sqlite": lambda: sqlite3.connect(str(ROOT.parent / "streamlit_mvp/day5-forbidden-probe.db")),
    }
    for name, attempt in attempts.items():
        try:
            attempt()
            blocked[name] = False
        except PermissionError:
            blocked[name] = True
    fact_fields = ("original_hexagram", "moving_line", "mutual_hexagram", "changed_hexagram", "body_use",
                   "strength", "time_calculation", "versions")
    facts_preserved = all(value["calculation"][key] == rendered["calculation"][key] for key in fact_fields)
    passed = (all(blocked.values()) and tampered["frames"]["moving_line"] is None
              and rendered["key_moving_line"]["status"] == "structure_fallback"
              and facts_preserved and rendered["calculation"] == tampered["calculation"])
    return {"passed": passed, "probes": blocked, "tampered_original_frame_rejected": tampered["frames"]["moving_line"] is None,
            "other_frames_retained": sum(f is not None for f in tampered["frames"].values()),
            "calculations_preserved": facts_preserved, "engine_input_preserved": rendered["calculation"] == tampered["calculation"],
            "real_ai_calls": 0}


def cases():
    from tests.test_traditional_judgement_day5 import requests
    from backend.traditional_judgement_v1 import OfflineJudgementAdapter, TraditionalJudgementEngine
    from backend.traditional_judgement_v1.trusted_input import digest
    inputs = OfflineJudgementAdapter().calculate_batch(requests())
    engine = TraditionalJudgementEngine()
    rows, examples = [], {}
    for index, item in enumerate(inputs):
        before = item.to_dict()
        output = engine.evaluate(item).to_dict()
        calculation = output["calculation"]
        rows.append({"case": index + 1, "hexagram_id": calculation["original_hexagram"]["id"],
            "hexagram": calculation["original_hexagram"]["name"], "line": calculation["moving_line"]["name"],
            "position": calculation["moving_line"]["position"], "cast_at": calculation["cast_at"],
            "relation": calculation["body_use"]["relation"], "body_state": calculation["strength"]["body"]["state"],
            "yong_state": calculation["strength"]["yong"]["state"], "baseline": output["traditional_tendency"]["baseline_tendency"],
            "combined": output["traditional_tendency"]["combined_tendency"], "conflict": bool(output["conflicts"]),
            "four_approved_frames": sum(s["status"] == "approved_context" for s in output["semantic_context"]),
            "input_unchanged": before == item.to_dict() and calculation == before["calculation"],
            "repeat_identical": output == engine.evaluate(item).to_dict(), "result_sha256": digest(output)})
        if index in (64, 69, 70):
            examples[{64: "guan_manual", 69: "sui_manual", 70: "guan_time"}[index]] = output
    return {"cases": rows, "count": len(rows),
            "passed": sum(r["input_unchanged"] and r["repeat_identical"] and r["four_approved_frames"] == 4 for r in rows),
            "real_ai_calls": 0}, examples


def run_child(kind):
    environment = {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP"}}
    completed = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(Path(__file__).resolve()), kind, "--worker"],
                               env=environment, cwd=ROOT, capture_output=True, timeout=300)
    try:
        result = json.loads(completed.stdout)
    except ValueError:
        result = {"failed": 1, "reason": "offline_check_failed"}
    if completed.returncode:
        result["runner_failed"] = True
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("unit", "legacy", "matrix", "probes", "cases", "all"))
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        try:
            if args.mode in {"legacy", "matrix"}:
                from scripts.day4_offline_checks import run_legacy, run_matrix
                result = run_legacy() if args.mode == "legacy" else run_matrix()
            else:
                result = unit_worker() if args.mode == "unit" else probes_worker()
            print(json.dumps(result, ensure_ascii=True))
            return int(bool(result.get("failed") or result.get("passed") is False))
        except Exception:
            print('{"failed":1,"reason":"offline_check_failed"}')
            return 1
    kinds = ("unit", "legacy", "matrix", "probes", "cases") if args.mode == "all" else (args.mode,)
    failed = False
    for kind in kinds:
        if kind == "cases":
            result, examples = cases()
            (ROOT / "docs/day5_golden_examples.json").write_text(json.dumps(examples, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            result = run_child(kind)
        (ROOT / "docs" / f"day5_{kind}_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        brief = {k: v for k, v in result.items() if k not in {"cases", "scope"}}
        print(json.dumps({"mode": kind, **brief}, ensure_ascii=False))
        failed |= bool(result.get("runner_failed") or result.get("failed") or result.get("passed") is False)
        if kind == "cases":
            failed |= result["passed"] != result["count"]
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
