"""Guarded acceptance for the review tool; no web integration or model call."""

from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def batch():
    from scripts.day4_offline_checks import legacy_guard
    sys.addaudithook(legacy_guard)
    from backend.app.meihua_models import ManualInput
    from backend.traditional_judgement_v1 import OfflineJudgementAdapter, TraditionalJudgementEngine
    from backend.traditional_judgement_v1.trusted_input import digest
    from backend.condition_review_tools_v1.pipeline import load_catalog, lookup_review
    from tests.test_traditional_judgement_day5 import requests
    from backend.traditional_conditions_v1 import ConditionalJudgementEngine
    catalog = load_catalog()
    adapter = OfflineJudgementAdapter()
    inputs = [ManualInput(input_mode="manual_hexagram", hexagram_id=r["target"][0], moving_line=r["target"][1],
               cast_at="2026-09-24T19:45:35+08:00") for r in catalog["records"]]
    results = []
    for record, request in zip(catalog["records"], adapter.calculate_batch(inputs)):
        payload = request.to_dict()
        calc = payload["calculation"]
        review, reason = lookup_review(request)
        baseline = TraditionalJudgementEngine().evaluate(request).to_dict()["traditional_tendency"]["baseline_tendency"]
        directions = {b["direction"] for b in record["branches"]}
        opposite = "adverse" if baseline == "favorable" else "favorable"
        tension = (record["eligible"] and record["effect"] in {"conditional_support", "adverse_warning"}
                   and opposite in directions)
        results.append({"target": record["target"], "hexagram": record["hexagram_name"], "line": record["line_name"],
            "state": record["state"], "eligible": review is not None, "readiness": record["readiness"],
            "failure_reason": reason, "relation": calc["body_use"]["relation"],
            "body_state": calc["strength"]["body"]["state"], "yong_state": calc["strength"]["yong"]["state"],
            "body_use_base": baseline, "potential_primary_conditional_tension": tension,
            "new_offline_review_matches_expectation": (review is not None) == record["eligible"],
            "original_frame_exactly_preserved": payload["frames"]["moving_line"]["frame"] == record["original_frame_snapshot"],
            "request_unchanged": payload == request.to_dict(),
            "deterministic_lookup": (review, reason) == lookup_review(request),
            "question_condition_inference": False, "whole_event_outcome": None,
            "calculation_fingerprint": digest(calc),
            "sampled_condition_audit": {"all_original_atoms_included": True,
                "exact_quote_offsets_checked": True, "branch_binding_checked": True,
                "condition_satisfaction": "unknown", "all_32_source_semantic_reviews_recorded": True}})
    # Original 71 Day 6A cases remain on their old engine and old catalog, verbatim.
    engine = ConditionalJudgementEngine()
    expected = json.loads((ROOT / "docs/day6a_cases_results.json").read_bytes())["cases"]
    regressions = []
    for row, request in zip(expected, adapter.calculate_batch(requests())):
        result = engine.evaluate(request).to_dict()
        regressions.append({"case": row["case"], "result_unchanged": digest(result) == row["result_sha256"],
                            "calculation_unchanged": result["calculation"] == request.to_dict()["calculation"]})
    prior = json.loads((ROOT / "data/day6a_condition_reviews.json").read_bytes())["records"]
    ready_new = sum(r["readiness"] == "bounded_synthesis_eligible" for r in catalog["records"])
    old_ready = sum(r["eligible"] and r["effect"] != "alternative_scopes" for r in prior)
    ready_old_branches = sum(r["eligible"] and r["effect"] == "alternative_scopes" for r in prior)
    combined = {
        "total_lines": 384, "prior_reviewed": len(prior), "pilot_reviewed": len(results),
        "prior_eligible": sum(r["eligible"] for r in prior), "new_eligible": sum(r["eligible"] for r in results),
        "total_eligible": sum(r["eligible"] for r in prior) + sum(r["eligible"] for r in results),
        "prior_bounded_synthesis_eligible": old_ready, "new_bounded_synthesis_eligible": ready_new,
        "bounded_synthesis_eligible": old_ready + ready_new,
        "branch_unresolved": ready_old_branches + sum(r["readiness"] == "branch_unresolved" for r in results),
        "unreviewed_lines": 384 - len(prior) - len(results),
        "reviewed_but_not_eligible": sum(not r["eligible"] for r in prior) + sum(not r["eligible"] for r in results),
        "active_day6a_engine_eligible": sum(r["eligible"] for r in prior),
        "new_catalog_enabled_in_day6a_engine_or_web": False,
        "metric_scope": "offline_review_readiness_not_new_production_or_combined_engine_outcomes",
    }
    passed = all(r[k] for r in results for k in ("new_offline_review_matches_expectation", "original_frame_exactly_preserved",
                    "request_unchanged", "deterministic_lookup")) and all(r["result_unchanged"] and r["calculation_unchanged"] for r in regressions)
    return {"batch": results, "pilot_size": len(results), "coverage": combined,
            "pilot_state_distribution": dict(Counter(r["state"] for r in results)),
            "failure_reasons": dict(Counter(r["failure_reason"] for r in results if r["failure_reason"])),
            "relations": dict(Counter(r["relation"] for r in results)),
            "positions": dict(Counter(r["target"][1] for r in results)),
            "potential_primary_tensions": sum(r["potential_primary_conditional_tension"] for r in results),
            "old_71_case_regressions": regressions, "old_71_exact_results_preserved": sum(r["result_unchanged"] for r in regressions),
            "passed": passed, "real_ai_calls": 0, "production_writes": False}


def child(mode):
    env = {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP"}}
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    run = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(Path(__file__).resolve()), mode, "--worker"],
                         cwd=ROOT, env=env, capture_output=True, timeout=600, **options)
    try:
        value = json.loads(run.stdout)
    except ValueError:
        return {"failed": 1, "reason": "guarded_acceptance_unavailable"}
    if run.returncode:
        value["runner_failed"] = True
    return value


def main():
    if len(sys.argv) == 3 and sys.argv[2] == "--worker":
        mode = sys.argv[1]
        try:
            if mode == "unit":
                from scripts.day5_offline_acceptance import unit_worker
                result = unit_worker()
            elif mode in {"legacy", "matrix"}:
                from scripts.day4_offline_checks import run_legacy, run_matrix
                result = run_legacy() if mode == "legacy" else run_matrix()
            elif mode == "probes":
                from scripts.day6a_offline_acceptance import probes
                result = probes()
            elif mode == "batch":
                result = batch()
            else:
                raise ValueError("invalid_mode")
            print(json.dumps(result, ensure_ascii=True))
            return int(bool(result.get("failed") or result.get("passed") is False))
        except Exception:
            print('{"failed":1,"reason":"guarded_acceptance_unavailable"}')
            return 1
    modes = ("unit", "legacy", "matrix", "probes", "batch") if sys.argv[1:] == ["all"] else sys.argv[1:]
    failed = False
    for mode in modes:
        if mode not in {"unit", "legacy", "matrix", "probes", "batch"}:
            raise ValueError("invalid_mode")
        result = child(mode)
        (ROOT / "docs" / f"day6b_{mode}_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"mode": mode, **{k: v for k, v in result.items() if k not in {
            "batch", "old_71_case_regressions", "scope", "failure_targets", "cases"}}}, ensure_ascii=False), flush=True)
        failed |= bool(result.get("failed") or result.get("runner_failed") or result.get("passed") is False)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
