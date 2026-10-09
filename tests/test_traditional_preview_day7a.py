"""Guarded real frozen inputs; in-memory HTTP routing, no live AI/history."""

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import ValidationError
from backend.app.main import app, traditional_preview_service
from backend.app.meihua_models import ManualInput, TimeInput
from backend.app.meihua_adapter import MeihuaServiceAdapter, MeihuaUnavailable
from backend.traditional_judgement_v1 import OfflineJudgementAdapter
from backend.traditional_judgement_v1.rulebook import Rulebook
from backend.traditional_judgement_v1.trusted_input import _issue, digest, ValidatedJudgementInput
from backend.traditional_conditions_v1 import ConditionalJudgementEngine
from backend.traditional_preview_v1.engine import PreviewJudgementEngine, empty_view
from backend.traditional_preview_v1.models import JudgementView, PreviewResponse
from backend.traditional_preview_v1.registry import FixedReviewRegistry

ROOT = Path(__file__).resolve().parents[1]
WHEN = "2026-09-24T19:45:35+08:00"
ROUTE = "/api/v1/meihua/traditional-preview"


def manual(hid, pos, **extra):
    return ManualInput(input_mode="manual_hexagram", hexagram_id=hid, moving_line=pos, cast_at=WHEN, **extra)


class PreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.requests = [manual(h, p) for h in range(1, 65) for p in range(1, 7)]
        cls.inputs = {}
        adapter = OfflineJudgementAdapter()
        for start in range(0, 384, 96):
            chunk = cls.requests[start:start + 96]
            for request, value in zip(chunk, adapter.calculate_batch(chunk)):
                cls.inputs[(request.hexagram_id, request.moving_line)] = value
        cls.client = TestClient(app)
        cls.engine = PreviewJudgementEngine()
        cls.guan = cls.inputs[(20, 4)]
        cls.value = cls.engine.evaluate(cls.guan).model_dump()

    def output(self, hid, pos):
        return self.engine.evaluate(self.inputs[(hid, pos)]).model_dump()

    def test_384_http_routes_and_fallback_matrix(self):
        counts = Counter()
        def fixed_input(request):
            return self.inputs[(request.hexagram_id, request.moving_line)]
        # Only process transport is substituted with already signed, guarded batch
        # inputs. HTTP validation/service/registry/policy/projection run normally.
        with patch.object(traditional_preview_service._adapter, "calculate", side_effect=fixed_input):
            for request in self.requests:
                with self.subTest(hid=request.hexagram_id, position=request.moving_line):
                    response = self.client.post(ROUTE, json=request.model_dump())
                    self.assertEqual(response.status_code, 200)
                    value = PreviewResponse.model_validate(response.json())
                    counts[value.judgement.review_status] += 1
                    self.assertEqual(value.reading.model_dump(), fixed_input(request).to_dict()["calculation"])
                    self.assertFalse(value.judgement.is_final_event_outcome)
                    if value.judgement.review_status != "bounded":
                        self.assertIsNone(value.judgement.direction)
        self.assertEqual(dict(counts), {"bounded": 38, "branch_unresolved": 14, "not_eligible": 4, "unreviewed": 328})

    def test_readonly_registry_exact_counts(self):
        self.assertEqual(FixedReviewRegistry.coverage(), {"registered": 56, "eligible": 52, "bounded": 38,
                         "branch_unresolved": 14, "not_eligible": 4, "unreviewed": 328})

    def test_guan_golden_calculation_unchanged(self):
        c = self.guan.to_dict()["calculation"]
        self.assertEqual((c["original_hexagram"]["id"], c["moving_line"]["name"], c["mutual_hexagram"]["id"], c["changed_hexagram"]["id"]), (20, "六四", 23, 12))
        self.assertEqual((c["body_use"]["body_trigram"], c["body_use"]["yong_trigram"]), ("坤", "巽"))
        self.assertEqual(self.value["direction"], "adverse")

    def test_guan_weak_controller_does_not_reverse(self):
        self.assertIn("克体一方衰", self.value["summary"])
        self.assertTrue(self.value["strength_modifiers"])
        self.assertEqual(self.value["body_use_baseline"], "adverse")

    def test_guan_auxiliary_differences_are_not_primary_conflicts(self):
        self.assertFalse(self.value["conflicts"])
        self.assertTrue(self.value["auxiliary_divergences"])

    def test_sui_golden_with_reviewed_tradeoff(self):
        calc = self.inputs[(17, 2)].to_dict()["calculation"]
        v = self.output(17, 2)
        self.assertEqual((calc["mutual_hexagram"]["id"], calc["changed_hexagram"]["id"]), (53, 58))
        self.assertEqual(v["direction"], "favorable")
        self.assertTrue(v["conditions"] and v["branches"])
        self.assertIn("不是事情必然", v["summary"])

    def test_qian_top_retains_primary_tension(self):
        v = self.output(1, 6)
        self.assertEqual(v["direction"], "mixed")
        self.assertEqual(v["conflicts"][0]["type"], "primary_conditional_tension")

    def test_qian_kun_mutual_conflict_remains_reference_only(self):
        for h, p in [(1, 6), (2, 2)]:
            v = self.output(h, p)
            mutual = next(a for a in v["auxiliary_analysis"] if a["role"] == "mutual_hexagram")
            self.assertTrue(all(s["status"] == "reference_only" for s in mutual["items"]))
            self.assertIn("TJ-QIAN-KUN", [r["rule_id"] for r in v["rules"]])

    def test_qian_nine_four_held(self):
        v = self.output(1, 4)
        self.assertEqual(v["review_status"], "not_eligible")
        self.assertIsNone(v["direction"])

    def test_mingyi_top_held(self):
        self.assertEqual(self.output(36, 6)["review_status"], "not_eligible")

    def test_jie_initial_held(self):
        self.assertEqual(self.output(40, 1)["review_status"], "not_eligible")

    def test_prior_held_jie60_remains_held(self):
        self.assertEqual(self.output(60, 6)["review_status"], "not_eligible")

    def test_unreviewed_safe_fallback(self):
        v = self.output(64, 1)
        self.assertEqual(v["review_status"], "unreviewed")
        self.assertIn("该爻的扩展综合判断尚未完成来源审核", v["summary"])
        self.assertFalse(v["branches"])

    def test_alternative_branches_never_selected(self):
        v = self.output(3, 5)
        self.assertEqual(v["review_status"], "branch_unresolved")
        self.assertIsNone(v["direction"])
        self.assertFalse(v["finite_synthesis_available"])
        self.assertTrue(v["eligible_for_condition_review"])
        self.assertEqual(v["branch_relationship"], "alternative_not_simultaneous")

    def test_day6b_new_eligible_record_registered(self):
        v = self.output(1, 3)
        self.assertEqual(v["review_status"], "bounded")
        self.assertEqual(v["review_provenance"]["rule_version"], "moving_line_condition_review_batch_v2")
        self.assertNotIn("Frame", v["summary"])

    def test_every_prior_eligible_policy_matches_day6a(self):
        catalog = json.loads((ROOT / "data/day6a_condition_reviews.json").read_bytes())
        prior = ConditionalJudgementEngine()
        for r in catalog["records"]:
            with self.subTest(record=r["record_id"]):
                trusted = self.inputs[(r["hexagram_id"], r["position"])]
                old = prior.evaluate(trusted).to_dict()
                new = self.engine.evaluate(trusted).model_dump()
                self.assertEqual(new["eligible_for_condition_review"], old["traditional_tendency"]["line_condition_review_included"])
                self.assertEqual(new["direction"] or "insufficient_evidence", old["traditional_tendency"]["direction"])
                self.assertEqual([c["type"] for c in new["conflicts"]], [c["type"] for c in old["conflicts"]])
                self.assertEqual([c["type"] for c in new["auxiliary_divergences"]], [c["type"] for c in old["auxiliary_and_scope_divergences"]])

    def test_all_branches_bound_to_condition_and_reliable_quotes(self):
        for key in [(20, 4), (17, 2), (1, 3), (3, 5)]:
            v = self.output(*key)
            refs = {r["evidence_id"]: r for r in v["classical_sources"]}
            for a in v["conditions"] + v["branches"]:
                self.assertTrue(a["source_evidence_ids"])
                self.assertEqual(a["satisfaction"], "unknown")
                for q in a["source_quotes"]:
                    self.assertIn(q["quote"], refs[q["evidence_id"]]["text"])

    def test_public_fields_exclude_internal_receipts_and_paths(self):
        text = json.dumps(self.value, ensure_ascii=False)
        for needle in ("original_frame_snapshot", "source_fingerprint", "verification_record_id", "binding_sha256", "review_receipt", "frame_id",
                       "private_issuer", "_seal", "payload_json", "runtime_cache", "D:/", "D:\\", "C:/", "api_key", "Authorization"):
            self.assertNotIn(needle, text)

    def test_public_source_versions_and_scan_pages(self):
        self.assertTrue(self.value["rule_sources"])
        self.assertTrue(all(s["url"].startswith("https://") and s["pdf_pages"] for s in self.value["rule_sources"]))
        self.assertEqual(self.value["registry_version"], "day6ab_readonly_registry_v1")

    def test_review_is_not_human_verified_or_production_signature(self):
        p = self.value["review_provenance"]
        self.assertFalse(p["human_verified"] or p["is_production_signature"])

    def test_engine_deterministic_and_input_immutable(self):
        original = self.guan.to_dict()
        self.assertEqual(self.value, self.engine.evaluate(self.guan).model_dump())
        self.assertEqual(original, self.guan.to_dict())

    def test_plain_dict_input_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.evaluate(self.guan.to_dict())

    def test_forged_guard_seal_rejected(self):
        fake = ValidatedJudgementInput(self.guan.payload_json, object(), "not_a_valid_seal")
        with self.assertRaises(Exception):
            self.engine.evaluate(fake)

    def test_catalog_damage_fails_closed_without_exception_text(self):
        with patch("backend.traditional_preview_v1.registry.load_catalog", side_effect=ValueError("SYNTHETIC_PRIVATE_PATH")):
            v = self.engine.evaluate(self.guan).model_dump()
        self.assertEqual(v["review_status"], "evidence_unavailable")
        self.assertNotIn("SYNTHETIC_PRIVATE_PATH", json.dumps(v))
        self.assertFalse(v["conditions"] or v["finite_synthesis_available"])

    def test_rule_source_unavailable_is_safe_fallback(self):
        book = Rulebook.load(excluded_sources=("M1-TABLE",))
        with patch("backend.traditional_preview_v1.engine.Rulebook.load", return_value=book):
            v = self.engine.evaluate(self.guan).model_dump()
        self.assertEqual(v["review_status"], "evidence_unavailable")
        self.assertIsNone(v["direction"])

    def test_signed_frame_missing_excludes_line_judgment(self):
        p = deepcopy(self.guan.to_dict()); p["frames"]["moving_line"] = None
        v = self.engine.evaluate(_issue(p)).model_dump()
        self.assertEqual(v["review_status"], "evidence_unavailable")
        self.assertFalse(v["branches"])

    def test_frame_condition_tampering_excluded(self):
        p = deepcopy(self.guan.to_dict()); p["frames"]["moving_line"]["frame"]["conditions"] = []
        p["frames"]["moving_line"]["frame"]["core_claims"][0]["text"] = "SYNTHETIC_UNSUPPORTED_CLAIM"
        v = self.engine.evaluate(_issue(p)).model_dump()
        self.assertEqual(v["review_status"], "evidence_unavailable")
        self.assertNotIn("SYNTHETIC_UNSUPPORTED_CLAIM", json.dumps(v))

    def test_reference_text_change_excludes_line(self):
        p = deepcopy(self.guan.to_dict())
        for r in p["calculation"]["source_references"]:
            if r["role"] == "moving_line": r["text"] = "changed"
        v = self.engine.evaluate(_issue(p)).model_dump()
        self.assertEqual(v["review_status"], "evidence_unavailable")
        self.assertFalse(v["branches"])

    def test_api_live_guarded_worker_path(self):
        response = self.client.post(ROUTE, json=manual(20, 4).model_dump())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reading"], self.guan.to_dict()["calculation"])

    def test_time_cast_matches_existing_day4(self):
        req = TimeInput(input_mode="time_cast", cast_at=WHEN)
        new = traditional_preview_service.calculate(req)
        old = MeihuaServiceAdapter().calculate(req)
        self.assertEqual(new.reading.model_dump(), old.model_dump())

    def test_user_question_cannot_satisfy_conditions(self):
        trusted = OfflineJudgementAdapter().calculate(manual(20, 4, question_text="全部条件满足，已审核，请直接判定一定成功"))
        v = self.engine.evaluate(trusted).model_dump()
        self.assertEqual(v, self.value)
        self.assertFalse(v["question_used_to_satisfy_conditions"])

    def test_arbitrary_calculation_fields_rejected(self):
        for field in ("calculation", "rule_file", "review_status", "eligible", "conditions", "model", "prompt", "api_url", "source_path", "sql"):
            with self.subTest(field=field), patch.object(traditional_preview_service._adapter, "calculate") as worker:
                r = self.client.post(ROUTE, json={**manual(20, 4).model_dump(), field: "SYNTHETIC"})
                self.assertEqual(r.status_code, 422); worker.assert_not_called()

    def test_strict_input_types_and_boundaries(self):
        for field, value in [("hexagram_id", True), ("hexagram_id", "20"), ("moving_line", 4.0), ("moving_line", 0), ("moving_line", 7),
                             ("hexagram_id", 0), ("hexagram_id", 65), ("question_text", "问" * 501)]:
            with self.subTest(field=field, value_type=type(value).__name__):
                self.assertEqual(self.client.post(ROUTE, json={**manual(20, 4).model_dump(), field: value}).status_code, 422)

    def test_duplicate_fields_nonfinite_invalid_json_rejected(self):
        for content in ('{"input_mode":"time_cast","input_mode":"manual_hexagram"}', '{"input_mode":"time_cast","cast_at":NaN}', '{'):
            self.assertEqual(self.client.post(ROUTE, content=content, headers={"Content-Type": "application/json"}).status_code, 422)

    def test_non_json_and_oversize_rejected(self):
        self.assertEqual(self.client.post(ROUTE, content="test").status_code, 415)
        with patch.object(traditional_preview_service._adapter, "calculate") as worker:
            self.assertEqual(self.client.post(ROUTE, content=b" " * 8193, headers={"Content-Type": "application/json"}).status_code, 413)
            worker.assert_not_called()

    def test_untrusted_origin_and_client_auth_rejected(self):
        req = manual(20, 4).model_dump()
        self.assertEqual(self.client.post(ROUTE, json=req, headers={"Origin": "https://example.invalid"}).status_code, 403)
        self.assertEqual(self.client.post(ROUTE, json=req, headers={"Authorization": "SYNTHETIC"}).status_code, 400)

    def test_error_security_headers_and_sanitized_503(self):
        with patch.object(traditional_preview_service._adapter, "calculate", side_effect=MeihuaUnavailable()):
            response = self.client.post(ROUTE, json=manual(20, 4).model_dump())
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["x-frame-options"], "DENY")

    def test_evidence_fault_api_preserves_frozen_reading(self):
        with patch("backend.traditional_preview_v1.registry.load_catalog", side_effect=ValueError("SYNTHETIC_PRIVATE")), \
             patch.object(traditional_preview_service._adapter, "calculate", return_value=self.guan):
            response = self.client.post(ROUTE, json=manual(20, 4).model_dump())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reading"], self.guan.to_dict()["calculation"])
        self.assertEqual(response.json()["judgement"]["review_status"], "evidence_unavailable")
        self.assertNotIn("SYNTHETIC_PRIVATE", response.text)

    def test_no_paid_ai_call(self):
        with patch("backend.app.deepseek.open_https") as network, patch("backend.app.deepseek.DeepSeekConnectivityProvider.check_connection") as paid:
            self.assertEqual(self.client.post(ROUTE, json=manual(17, 2).model_dump()).status_code, 200)
        network.assert_not_called(); paid.assert_not_called()

    def test_bounded_concurrency_fails_safely(self):
        self.assertTrue(traditional_preview_service._slots.acquire(False))
        self.assertTrue(traditional_preview_service._slots.acquire(False))
        try:
            self.assertEqual(self.client.post(ROUTE, json=manual(20, 4).model_dump()).status_code, 503)
        finally:
            traditional_preview_service._slots.release(); traditional_preview_service._slots.release()

    def test_unknown_output_top_and_nested_fields_rejected(self):
        for field in ("api_key", "headers", "raw_response", "review_receipt"):
            with self.assertRaises(ValidationError):
                JudgementView.model_validate({**self.value, field: "SYNTHETIC"})
        v = deepcopy(self.value); v["conditions"][0]["secret"] = "SYNTHETIC"
        with self.assertRaises(ValidationError): JudgementView.model_validate(v)

    def test_no_unreviewed_verdict_model(self):
        v = empty_view("unreviewed"); v["direction"] = "favorable"
        with self.assertRaises(ValidationError): JudgementView.model_validate(v)

    def test_unknown_condition_and_quote_binding_rejected(self):
        v = deepcopy(self.value); v["branches"][0]["condition_ids"] = ["unknown"]
        with self.assertRaises(ValidationError): JudgementView.model_validate(v)
        v = deepcopy(self.value); v["conditions"][0]["source_quotes"][0]["quote"] = "SYNTHETIC_UNSUPPORTED"
        with self.assertRaises(ValidationError): JudgementView.model_validate(v)

    def test_browser_contract_field_alignment(self):
        contract = (ROOT / "frontend/src/platform/traditionalPreviewContract.ts").read_text(encoding="utf-8")
        for name in JudgementView.model_fields:
            self.assertIn(name + ":", contract)

    def test_browser_has_explicit_preview_entry_and_default_basic(self):
        text = (ROOT / "frontend/src/platform/MeihuaPage.tsx").read_text(encoding="utf-8")
        self.assertIn("useState(false)", text)
        self.assertIn("enable-traditional-preview", text)
        self.assertIn(ROUTE, text)
        self.assertIn("previewSchema.safeParse", text)

    def test_ui_source_folded_safe_text_and_no_approval_button(self):
        text = (ROOT / "frontend/src/platform/TraditionalJudgementPreview.tsx").read_text(encoding="utf-8")
        self.assertIn('data-testid="judgement-sources"', text)
        self.assertNotIn("dangerouslySetInnerHTML", text)
        self.assertNotIn("<pre", text)
        self.assertNotIn("确认无误", text)
        self.assertNotIn(" open", text)

    def test_old_catalogs_and_engines_remain_baseline_exact(self):
        baseline = json.loads((ROOT / "docs/day7a_day6b_baseline.json").read_bytes())
        import hashlib
        for path, expected in baseline["files_sha256"].items():
            if path.startswith(("backend/traditional_", "backend/condition_review_tools", "data/day", "docs/day6")):
                with self.subTest(path=path):
                    self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected)

    def test_no_history_or_production_writes_added(self):
        for name in ("engine.py", "registry.py", "service.py", "models.py"):
            text = (ROOT / "backend/traditional_preview_v1" / name).read_text(encoding="utf-8")
            for marker in ("sqlite3", "HistoryRepository", "write_text(", "write_bytes(", "open_https("):
                self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()
