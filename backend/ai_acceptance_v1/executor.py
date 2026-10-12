"""Private six-case acceptance orchestration. Not a user interpretation service."""

from dataclasses import dataclass
from copy import deepcopy
import json
from pathlib import Path
import re
import threading
import time

from backend.app.deepseek import strict_json
from backend.question_quality_v1.contract import (ApplicationDraft, IndependentVerdict,
    QualityRequest, validate_draft, validate_verdict)
from backend.question_quality_v1.pipeline import run_offline
from scripts.day8b_prepare import CASES
from .policy import AcceptanceDenied, BATCHES, MODEL, PROVIDER, canonical, sha
from .prompts import messages_for, wire_for

ROOT = Path(__file__).resolve().parents[2]
PREP_SHA = "ca8c47845ce51795b964420ab933ee49a7788b842215a61800503214a5a0962c"
SEVERE = {"implicit_or_absolute_prediction", "time_prediction", "source_condition_determination",
          "locked_fact_declaration", "unprovided_reality_assertion", "unsafe_output",
          "omitted_or_added_limits", "frame_binding", "evidence_binding", "known_source_scope_hold"}


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    status: str
    errors: tuple[str, ...]
    sections: tuple
    checks: dict
    calls: tuple
    production_approved: bool = False
    history_written: bool = False


class AcceptanceExecutor:
    def __init__(self, ledger, transport, token_counter):
        if transport.ledger is not ledger: raise AcceptanceDenied("transport_ledger_mismatch")
        self.ledger, self.transport, self.counter = ledger, transport, token_counter

    @staticmethod
    def _bind(case_id, request):
        if type(request) is not QualityRequest: raise AcceptanceDenied("controlled_quality_request_required")
        case = next((c for c in CASES if c["case_id"] == case_id), None)
        if case is None: raise AcceptanceDenied("unknown_case")
        p = request.checked()
        prep = json.loads((ROOT / "docs/day8b_preparation_results.json").read_bytes())
        if sha(prep) != PREP_SHA: raise AcceptanceDenied("preparation_baseline_changed")
        expected = next(c for c in prep["cases"] if c["case_id"] == case_id)
        if (p["question"] != case["question"] or request.fingerprint != expected["request_fingerprint"]
                or p["calculation"]["original_hexagram"]["id"] != case["hexagram_id"]
                or p["calculation"]["moving_line"]["position"] != case["moving_line"]
                or p["judgement"]["review_status"] != case["expected_status"]):
            raise AcceptanceDenied("case_or_source_changed")
        return p

    def run_case(self, case_id, request, cancel=None):
        cancel = cancel or threading.Event()
        before = deepcopy(self._bind(case_id, request))
        before_hash = sha(before)
        base_sections = tuple((m['role'],m['text']) for m in before['calculation']['standard_meanings'])
        calls = []
        deadline = time.monotonic() + 50

        def fail(errors, phase=None):
            try: unchanged = sha(request.checked()) == before_hash
            except Exception: unchanged = False
            if not unchanged: self.ledger.stop('input_changed')
            return CaseResult(case_id, "BASE_FALLBACK", tuple(errors), base_sections,
                {"local_gate": phase, "independent_review": "not_passed",
                 "facts_unchanged": unchanged,
                 "source_quality": "unverified", "real_model_quality": "unverified"}, tuple(calls))

        def invoke(phase, draft=None):
            if cancel.is_set() or time.monotonic() >= deadline:
                raise AcceptanceDenied("cancelled_before_request")
            if self.ledger.mode=='live': self.ledger.ensure_price_current()
            messages = messages_for(request, phase, draft)
            wire = wire_for(messages, phase)
            try:
                permit = self.ledger.reserve(case_id, phase, self.counter.reserve_input(messages), sha(wire))
            except AcceptanceDenied as e:
                if str(e) in {'request_budget_exceeded','question_budget_exceeded','token_budget_exceeded','fee_budget_exceeded'}:
                    self.ledger.stop('budget_exhausted')
                raise
            try:
                result = self.transport.perform(permit, wire, cancel)
            except Exception:
                # Dispatch/start failures retain the entire conservative charge.
                from .transport import TransportResult
                result = TransportResult("worker_failure")
            # Transport must join its worker before finish() clears active slot.
            if not result.reaped:
                self.ledger.stop("transport_failure")
                raise AcceptanceDenied("cleanup_failed")
            self.ledger.finish(permit, result.usage, result.code, result.http_status, result.latency)
            calls.append({"phase": phase, "provider": PROVIDER, "model": MODEL,
                          "http_status": result.http_status, "code": result.code,
                          "latency_seconds": round(result.latency, 4), "retries": 0,
                          "usage": result.usage.record() if result.usage else None,
                          "worker_reaped": True})
            if result.code != "ok": raise AcceptanceDenied(result.code)
            if self.ledger.snapshot()["stopped"]: raise AcceptanceDenied("usage_unavailable")
            request.checked()
            if sha(request.checked()) != before_hash: raise AcceptanceDenied("input_changed")
            return result.content

        try:
            raw = invoke("candidate")
            draft = ApplicationDraft.model_validate(strict_json(raw))
            errors = validate_draft(request, draft)
            if draft.intent.category != next(c['category'] for c in CASES if c['case_id']==case_id):
                errors.append('intent_category_mismatch')
            if errors:
                if set(errors) & SEVERE or any(e.startswith("unprovided_reality:") for e in errors):
                    self.ledger.stop("safety_rejection")
                return fail(errors, "rejected")
            raw = invoke("reviewer", draft)
            verdict = IndependentVerdict.model_validate(strict_json(raw))
            errors = validate_verdict(request, draft, verdict)
            if errors:
                if any(not all((v.no_prediction, v.no_invented_facts, v.preserves_scope,
                                v.preserves_conditions)) for v in verdict.claims):
                    self.ledger.stop("safety_rejection")
                return fail(errors, "passed")
            # Existing deterministic rendering/gates reused without edits.
            class Candidate:
                def generate(self, r): return draft
            class Reviewer:
                def review(self, r, d): return verdict
            rendered = run_offline(request, Candidate(), Reviewer())
            if rendered.status != "OFFLINE_ACCEPTED": return fail(rendered.errors, "rejected")
            # Do not persist raw draft/intent/reviewer reasons. Test output only.
            if any(re.search(r"authorization|bearer|sk-[a-z0-9_-]{10,}|[a-z]:\\\\|<[^>]*>", text, re.I) for _, text in rendered.sections):
                self.ledger.stop("safety_rejection")
                return fail(["unsafe_output"], "rejected")
            return CaseResult(case_id, "MOCK_CONTRACT_ACCEPTED" if self.ledger.mode == "mock" else "TEST_CONTRACT_ACCEPTED",
                (), rendered.sections, {"local_gate": "passed", "independent_review": "passed",
                "facts_unchanged": sha(request.checked()) == before_hash,
                "intent_category": draft.intent.category, "exact_user_spans": True,
                "conditions_bound": True, "no_known_prediction_pattern": True,
                "source_quality": "requires_separate_source_review", "real_model_quality": "unverified",
                "binding_evidence": [{"role": c.role, "frame_id": c.frame_id,
                    "source_evidence_ids": c.source_evidence_ids, "limit_ids": c.preserved_limit_ids,
                    "six_checks_true": True, "score": next(v.score for v in verdict.claims if v.claim_id == c.claim_id)} for c in draft.claims]}, tuple(calls))
        except AcceptanceDenied as e:
            allowed = {"cancelled_before_request", "cancelled", "timeout", "http_failure", "redirect_blocked",
                "network_failure", "schema_failure", "empty_content", "incomplete_response", "unsafe_response",
                "internal_failure", "usage_unavailable", "worker_failure", "response_too_large", "not_configured",
                "input_changed", "cleanup_failed", "run_stopped", "batch_not_authorized", "request_in_progress",
                "duplicate_attempt_no_retry", "candidate_required", "request_budget_exceeded", "question_budget_exceeded",
                "token_budget_exceeded", "fee_budget_exceeded", "price_reconfirmation_required", "budget_integrity_failure",
                "budget_state_missing", "invalid_reservation"}
            return fail([str(e) if str(e) in allowed else "acceptance_preflight_rejected"])
        except Exception:
            return fail(["schema_or_contract_failure"])

    def run_batch(self, batch, requests, report_path):
        if type(batch) is not int or batch not in BATCHES or tuple(requests) != BATCHES[batch]:
            raise AcceptanceDenied("fixed_batch_required")
        # Before any prompt/token/config work: authority is persistent, not URL state.
        if batch not in self.ledger.snapshot()["authorized_batches"]:
            raise AcceptanceDenied("batch_not_authorized")
        path = Path(report_path).resolve()
        if not (path.is_relative_to(self.ledger.records.parent) or
                (path.parent == ROOT/'docs' and path.name.startswith('day8b1_') and path.suffix=='.json')):
            raise AcceptanceDenied('private_report_path_required')
        rows = []
        deadline = time.monotonic() + 300
        for case_id, request in requests.items():
            if self.ledger.snapshot()["stopped"] or time.monotonic() >= deadline:
                rows.append({"case_id": case_id, "status": "NOT_RUN_STOPPED", "errors": []})
                continue
            result = self.run_case(case_id, request)
            # Explicit whitelist, not arbitrary dataclass/payload serialization.
            rows.append({"case_id": result.case_id, "status": result.status, "errors": list(result.errors),
                         "sections": list(result.sections), "checks": result.checks, "calls": list(result.calls),
                         "production_approved": False, "history_written": False})
        report = {"batch": batch, "mode": self.ledger.mode, "cases": rows,
                  "budget": self.ledger.snapshot(), "real_ai_calls": 0 if self.ledger.mode == "mock" else sum(len(r.get("calls", [])) for r in rows),
                  "mock_results_are_real_quality_acceptance": False, "production_application_enabled": False}
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.ledger.record_batch_report(batch, sha(report))
        return report
