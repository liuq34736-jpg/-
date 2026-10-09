"""Guarded repeatable acceptance; emits Day 6A artifacts only."""

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def cases():
    from scripts.day4_offline_checks import legacy_guard
    sys.addaudithook(legacy_guard)
    from tests.test_traditional_judgement_day5 import requests
    from tests.test_traditional_conditions_day6a import reviewed_requests
    from backend.traditional_judgement_v1 import OfflineJudgementAdapter, TraditionalJudgementEngine
    from backend.traditional_judgement_v1.trusted_input import digest
    from backend.traditional_conditions_v1 import ConditionalJudgementEngine
    old_cases = json.loads((ROOT / "docs/day5_cases_results.json").read_bytes())["cases"]
    adapter = OfflineJudgementAdapter()
    old_engine, new_engine = TraditionalJudgementEngine(), ConditionalJudgementEngine()
    rows, examples, reviewed_rows = [], {}, []
    for index, trusted in enumerate(adapter.calculate_batch(requests())):
        original = trusted.to_dict()
        old, new = old_engine.evaluate(trusted).to_dict(), new_engine.evaluate(trusted).to_dict()
        calc = new["calculation"]
        old_tag, new_tag = old["traditional_tendency"]["combined_tendency"], new["traditional_tendency"]["direction"]
        included = new["traditional_tendency"]["line_condition_review_included"]
        if not included:
            reason = new["line_adjudication"]["reason"] or "body_use_source_unavailable"
        elif new_tag == "insufficient_evidence":
            reason = "alternative_scope_prerequisites_not_known"
        elif new_tag == "mixed":
            reason = "reviewed_line_and_body_use_conditional_tension"
        elif old_tag == "mixed":
            reason = "strength_modifier_and_auxiliary_divergence_are_not_opposite_votes"
        else:
            reason = "baseline_retained_with_reviewed_line_constraints"
        row = {"case":index+1, "hexagram_id":calc["original_hexagram"]["id"],
               "hexagram":calc["original_hexagram"]["name"], "position":calc["moving_line"]["position"],
               "line":calc["moving_line"]["name"], "cast_at":calc["cast_at"],
               "relation":calc["body_use"]["relation"], "body_state":calc["strength"]["body"]["state"],
               "yong_state":calc["strength"]["yong"]["state"], "day5_tag":old_tag, "day6a_tag":new_tag,
               "label_changed":old_tag != new_tag, "scope":new["traditional_tendency"]["scope"],
               "line_review_included":included, "change_or_retention_reason":reason,
               "day5_result_matches_original_baseline":digest(old)==old_cases[index]["result_sha256"],
               "calculation_unchanged":calc == original["calculation"],
               "input_unchanged":trusted.to_dict()==original,
               "repeat_identical":new==new_engine.evaluate(trusted).to_dict(),
               "four_original_frames_preserved":new["semantic_context"]==old["semantic_context"],
               "result_sha256":digest(new)}
        rows.append(row)
        if index in (64,69,70):
            examples[{64:"guan_manual",69:"sui_manual",70:"guan_time"}[index]] = new
    for trusted in adapter.calculate_batch(reviewed_requests()):
        new = new_engine.evaluate(trusted).to_dict()
        calc = new["calculation"]
        key = f"{calc['original_hexagram']['id']}:{calc['moving_line']['position']}"
        examples[key] = new
        reviewed_rows.append({"target":key, "hexagram":calc["original_hexagram"]["name"],
            "line":calc["moving_line"]["name"], "relation":calc["body_use"]["relation"],
            "body_state":calc["strength"]["body"]["state"], "yong_state":calc["strength"]["yong"]["state"],
            "eligible":new["traditional_tendency"]["line_condition_review_included"],
            "scope":new["traditional_tendency"]["scope"], "direction":new["traditional_tendency"]["direction"],
            "reason":new["line_adjudication"]["reason"], "summary":new["traditional_tendency"]["summary"],
            "condition_count":len(new["line_adjudication"]["record"]["conditions"]) if new["line_adjudication"]["record"] else 0,
            "facts_preserved":new["calculation"]==trusted.to_dict()["calculation"],
            "repeat_identical":new==new_engine.evaluate(trusted).to_dict()})
    checks = ("day5_result_matches_original_baseline", "calculation_unchanged", "input_unchanged", "repeat_identical", "four_original_frames_preserved")
    result = {"cases":rows, "count":len(rows), "passed":sum(all(r[k] for k in checks) for r in rows),
        "labels_changed":sum(r["label_changed"] for r in rows),
        "day5_distribution":dict(Counter(r["day5_tag"] for r in rows)),
        "day6a_distribution":dict(Counter(r["day6a_tag"] for r in rows)),
        "day6a_scope_distribution":dict(Counter(r["scope"] for r in rows)),
        "reason_distribution":dict(Counter(r["change_or_retention_reason"] for r in rows)),
        "reviewed_representative_cases":reviewed_rows,
        "reviewed_cases_passed":sum(r["facts_preserved"] and r["repeat_identical"] for r in reviewed_rows),
        "reviewed_direction_distribution":dict(Counter(r["direction"] for r in reviewed_rows)),
        "real_ai_calls":0, "labels_are_same_scope_between_versions":False,
        "label_comparison_note":"Day 5 只含结构与辅助；Day 6A 未审核者不提供综合标签，基础结构仍单独保留。"}
    return result, examples


def probes():
    from scripts.day5_offline_acceptance import probes_worker
    result = probes_worker()
    # The same guarded worker and original signature failure remain the boundary.
    from backend.app.meihua_worker import FrozenRuntime
    from backend.traditional_judgement_v1.worker import collect
    from backend.traditional_judgement_v1.trusted_input import _issue
    from backend.traditional_conditions_v1 import ConditionalJudgementEngine
    runtime = FrozenRuntime()
    value = collect(runtime, {"input_mode":"manual_hexagram", "hexagram_id":20, "moving_line":4,
                              "cast_at":"2026-09-24T19:45:35+08:00"})
    value["calculation"].update(question_text="", question_applied_to_calculation=False)
    value["frames"]["moving_line"] = None
    out = ConditionalJudgementEngine().evaluate(_issue(value)).to_dict()
    result["new_condition_layer_missing_frame_fails_closed"] = out["traditional_tendency"]["direction"] == "insufficient_evidence"
    result["new_condition_layer_calculation_preserved"] = out["calculation"] == value["calculation"]
    result["passed"] &= result["new_condition_layer_missing_frame_fails_closed"] and result["new_condition_layer_calculation_preserved"]
    return result


def run_child(mode):
    environment = {k:v for k,v in os.environ.items() if k.upper() in {"SYSTEMROOT","WINDIR","PATH","TEMP","TMP"}}
    options = {"creationflags":subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    run = subprocess.run([sys.executable,"-I","-B","-X","utf8",str(Path(__file__).resolve()),mode,"--worker"],
                         cwd=ROOT, env=environment, capture_output=True, timeout=300, **options)
    try:
        value = json.loads(run.stdout)
    except ValueError:
        return {"failed":1,"reason":"day6a_offline_check_failed"}
    if run.returncode:
        value["runner_failed"] = True
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("unit","legacy","matrix","probes","cases","all"))
    parser.add_argument("--worker",action="store_true")
    args = parser.parse_args()
    if args.worker:
        try:
            if args.mode == "unit":
                from scripts.day5_offline_acceptance import unit_worker
                result = unit_worker()
            elif args.mode in {"legacy","matrix"}:
                from scripts.day4_offline_checks import run_legacy, run_matrix
                result = run_legacy() if args.mode == "legacy" else run_matrix()
            elif args.mode == "probes":
                result = probes()
            else:
                result, examples = cases()
                result["examples"] = examples
            print(json.dumps(result,ensure_ascii=True))
            return int(bool(result.get("failed") or result.get("passed") is False
                            or args.mode == "cases" and result["passed"] != result["count"]))
        except Exception:
            print('{"failed":1,"reason":"day6a_offline_check_failed"}')
            return 1
    failed = False
    for mode in (("unit","legacy","matrix","probes","cases") if args.mode == "all" else (args.mode,)):
        result = run_child(mode)
        if "examples" in result:
            (ROOT / "docs/day6a_examples.json").write_text(json.dumps(result.pop("examples"),ensure_ascii=False,indent=2),encoding="utf-8")
        (ROOT / "docs" / f"day6a_{mode}_results.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        brief = {k:v for k,v in result.items() if k not in {"cases","reviewed_representative_cases","scope","failure_targets"}}
        print(json.dumps({"mode":mode,**brief},ensure_ascii=False))
        failed |= bool(result.get("failed") or result.get("runner_failed") or result.get("passed") is False)
        if mode == "cases" and "count" in result:
            failed |= result["passed"] != result["count"] or result["reviewed_cases_passed"] != 24
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
