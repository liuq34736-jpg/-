"""Write only Day 8A evidence. Child regressions forbid production writes/AI."""

from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def install_guard():
    from scripts.day4_offline_checks import legacy_guard
    def guard(event, args):
        if event in {"socket.bind", "socket.connect", "socket.connect_ex", "socket.getaddrinfo"}:
            address = args[1] if event != "socket.getaddrinfo" else args[:2]
            if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1", "localhost"} and address[1] not in {5173, 8765}:
                return
        legacy_guard(event, args)
    sys.addaudithook(guard)


def preview_matrix():
    install_guard()
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from backend.app.main import app, traditional_preview_service
    from backend.app.meihua_models import ManualInput
    from backend.traditional_judgement_v1 import OfflineJudgementAdapter
    from backend.traditional_judgement_v1.trusted_input import digest
    from backend.traditional_preview_v1.models import PreviewResponse
    from backend.traditional_preview_v1.registry import FixedReviewRegistry
    inputs = {}
    requests = [ManualInput(input_mode="manual_hexagram", hexagram_id=h, moving_line=p,
                cast_at="2026-09-24T19:45:35+08:00") for h in range(1, 65) for p in range(1, 7)]
    adapter = OfflineJudgementAdapter()
    for start in range(0, 384, 96):
        for request, value in zip(requests[start:start+96], adapter.calculate_batch(requests[start:start+96])):
            inputs[(request.hexagram_id, request.moving_line)] = value
    client, rows, examples = TestClient(app), [], {}
    def guarded_input(request):
        return inputs[(request.hexagram_id, request.moving_line)]
    with patch.object(traditional_preview_service._adapter, "calculate", side_effect=guarded_input):
        for req in requests:
            response = client.post("/api/v1/meihua/traditional-preview", json=req.model_dump())
            value = PreviewResponse.model_validate(response.json())
            c, j = value.reading.model_dump(), value.judgement.model_dump()
            original = guarded_input(req).to_dict()["calculation"]
            rows.append({"hexagram_id": req.hexagram_id, "line_position": req.moving_line, "line_name": c["moving_line"]["name"],
                         "http_status": response.status_code, "review_status": j["review_status"], "direction": j["direction"],
                         "eligible": j["eligible_for_condition_review"], "finite_synthesis_available": j["finite_synthesis_available"],
                         "calculation_exactly_preserved": c == original, "four_approved_roles": sum(m["status"] == "SEMANTIC_APPROVED" for m in c["standard_meanings"]),
                         "conditions_unknown": all(a["satisfaction"] == "unknown" for a in j["conditions"] + j["branches"]),
                         "result_sha256": digest(value.model_dump())})
            if (req.hexagram_id, req.moving_line) in {(20, 4), (17, 2), (1, 6), (1, 4), (36, 6), (40, 1), (3, 5), (64, 1), (1, 3)}:
                examples[f"{req.hexagram_id}:{req.moving_line}"] = value.model_dump()
    passed = sum(r["http_status"] == 200 and r["calculation_exactly_preserved"] and r["four_approved_roles"] == 4 and r["conditions_unknown"] for r in rows)
    return {"combinations": 384, "passed": passed, "failed": 384 - passed,
            "routing_transport": "in_memory_ASGI; only_worker_transport_reuses_fresh_guarded_signed_batch_inputs",
            "actual_http_routes_and_public_schema_executed": True, "live_port_requests": False,
            "registry_coverage": FixedReviewRegistry.coverage(), "route_statuses": dict(Counter(r["review_status"] for r in rows)),
            "cases": rows, "synthetic_examples": examples, "real_ai_calls": 0, "production_writes": False}


def old71():
    install_guard()
    from tests.test_traditional_judgement_day5 import requests
    from backend.traditional_judgement_v1 import OfflineJudgementAdapter
    from backend.traditional_judgement_v1.trusted_input import digest
    from backend.traditional_conditions_v1 import ConditionalJudgementEngine
    expected = json.loads((ROOT / "docs/day6a_cases_results.json").read_bytes())["cases"]
    engine = ConditionalJudgementEngine()
    rows = [{"case": row["case"], "exact_result_sha256_unchanged": digest(engine.evaluate(req).to_dict()) == row["result_sha256"]}
            for row, req in zip(expected, OfflineJudgementAdapter().calculate_batch(requests()))]
    passed = sum(r["exact_result_sha256_unchanged"] for r in rows)
    return {"cases": rows, "total": len(rows), "passed": passed, "failed": len(rows) - passed}


def child(mode):
    env = {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP"}}
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    run = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(Path(__file__).resolve()), mode, "--worker"],
                         cwd=ROOT, env=env, capture_output=True, timeout=900, **options)
    try:
        result = json.loads(run.stdout)
    except ValueError:
        return {"failed": 1, "reason": "guarded_acceptance_unavailable"}
    if run.returncode: result["runner_failed"] = True
    return result


def main():
    modes = {"unit", "legacy", "frozen_matrix", "probes", "preview_matrix", "old71"}
    if len(sys.argv) == 3 and sys.argv[2] == "--worker":
        mode = sys.argv[1]
        try:
            if mode == "unit":
                from scripts.day5_offline_acceptance import unit_worker
                result = unit_worker()
            elif mode in {"legacy", "frozen_matrix"}:
                from scripts.day4_offline_checks import run_legacy, run_matrix
                result = run_legacy() if mode == "legacy" else run_matrix()
            elif mode == "probes":
                from scripts.day6a_offline_acceptance import probes
                result = probes()
            elif mode == "preview_matrix": result = preview_matrix()
            elif mode == "old71": result = old71()
            else: raise ValueError("invalid_mode")
            print(json.dumps(result, ensure_ascii=True))
            return int(bool(result.get("failed") or result.get("passed") is False))
        except Exception:
            print('{"failed":1,"reason":"guarded_acceptance_unavailable"}')
            return 1
    selected = ("unit", "legacy", "frozen_matrix", "probes", "preview_matrix", "old71") if sys.argv[1:] == ["all"] else sys.argv[1:]
    failed = False
    for mode in selected:
        if mode not in modes: raise ValueError("invalid_mode")
        result = child(mode)
        (ROOT / "docs" / f"day8a_{mode}_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"mode": mode, **{k: v for k, v in result.items() if k not in {"cases", "scope", "synthetic_examples"}}}, ensure_ascii=False), flush=True)
        failed |= bool(result.get("failed") or result.get("runner_failed") or result.get("passed") is False)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
