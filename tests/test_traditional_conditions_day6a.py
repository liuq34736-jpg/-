"""Independent condition/scope/source tests; all Day 5 tests remain unchanged."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from backend.app.meihua_models import ManualInput
from backend.traditional_judgement_v1 import OfflineJudgementAdapter, TraditionalJudgementEngine
from backend.traditional_judgement_v1.rulebook import Rulebook
from backend.traditional_judgement_v1.trusted_input import _issue, digest, JudgementUnavailable
from backend.traditional_conditions_v1 import ConditionReviewCatalog, ConditionalJudgementEngine
from tests.test_traditional_judgement_day5 import requests, MOMENT

ROOT = Path(__file__).resolve().parents[1]


def reviewed_requests():
    return [ManualInput(input_mode="manual_hexagram", hexagram_id=r["hexagram_id"], moving_line=r["position"], cast_at=MOMENT)
            for r in ConditionReviewCatalog.load().to_dict()["records"]]


class Day6AConditionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = ConditionReviewCatalog.load()
        cls.engine = ConditionalJudgementEngine(reviews=cls.catalog)
        cls.inputs = OfflineJudgementAdapter().calculate_batch(reviewed_requests())
        cls.by_key = {(v.to_dict()["calculation"]["original_hexagram"]["id"],
                       v.to_dict()["calculation"]["moving_line"]["position"]): v for v in cls.inputs}
        cls.results = {k: cls.engine.evaluate(v).to_dict() for k, v in cls.by_key.items()}
        cls.old_inputs = OfflineJudgementAdapter().calculate_batch(requests())
        cls.old_new = [cls.engine.evaluate(v).to_dict() for v in cls.old_inputs]

    def fixture(self, change, key=(20, 4)):
        value = self.by_key[key].to_dict()
        change(value)
        return _issue(value)

    def test_all_384_frames_audited_and_original_signed(self):
        audit = json.loads((ROOT / "docs/day6a_frame_audit.json").read_bytes())
        self.assertEqual((audit["count"], audit["signed_approved_frames"]), (384, 384))
        self.assertEqual(len({(r["hexagram_id"], r["position"]) for r in audit["rows"]}), 384)

    def test_all_384_conditions_cautions_read_without_sentiment_classification(self):
        audit = json.loads((ROOT / "docs/day6a_frame_audit.json").read_bytes())
        self.assertEqual((audit["nonempty_conditions"], audit["nonempty_cautions"], audit["core_claim_count"]), (41, 8, 686))
        for row in audit["rows"]:
            for field in ("core_claims", "conditions", "cautions"):
                for atom in row["frame"][field]:
                    self.assertTrue(atom["text"] and atom["supported_by"])
                    self.assertLessEqual(set(atom["supported_by"]), set(row["frame"]["source_evidence_ids"]))

    def test_review_is_not_extended_to_384_lines(self):
        records = self.catalog.to_dict()["records"]
        self.assertEqual(len(records), 24)
        self.assertEqual(sum(r["eligible"] for r in records), 23)
        self.assertLess(len(records), 384)

    def test_guan_weak_control_is_limited_adverse_not_automatic_mixed(self):
        out = self.results[(20, 4)]
        self.assertEqual(out["traditional_tendency"]["direction"], "adverse")
        self.assertEqual(out["traditional_tendency"]["baseline_relation"], "yong_controls_body")
        self.assertIn("strength.controlling_side_weak", out["body_use_and_strength"]["qualifier_ids"])
        self.assertFalse(out["conflicts"])

    def test_guan_mutual_and_changed_opposition_is_auxiliary_only(self):
        out = self.results[(20, 4)]
        self.assertTrue(any(d["type"] == "between_auxiliary_phases" for d in out["auxiliary_and_scope_divergences"]))
        self.assertTrue(all(not d["is_primary_conflict"] for d in out["auxiliary_and_scope_divergences"]))
        self.assertEqual(out["calculation"]["mutual_hexagram"]["id"], 23)
        self.assertEqual(out["calculation"]["changed_hexagram"]["id"], 12)

    def test_guan_guest_role_benefit_cannot_become_whole_event_success(self):
        out = self.results[(20, 4)]
        f = next(f for f in out["favorable_factors"] if f["layer"] == "reviewed_line")
        self.assertEqual(f["scope"], "specific_action_only")
        self.assertEqual(out["traditional_tendency"]["direction"], "adverse")

    def test_sui_body_wang_and_tradeoff_preserved(self):
        out = self.results[(17, 2)]
        self.assertEqual(out["calculation"]["body_use"]["relation"], "body_controls_yong")
        self.assertEqual(out["calculation"]["strength"]["body"]["state"], "wang")
        self.assertEqual(out["traditional_tendency"]["direction"], "favorable")
        self.assertEqual(out["line_adjudication"]["record"]["effect"], "tradeoff")
        self.assertIn("不能兼顾", out["traditional_tendency"]["summary"])
        self.assertFalse(out["traditional_tendency"]["unqualified_favorable_allowed"])

    def test_same_element_does_not_suppress_unfavorable_line_limit(self):
        out = self.results[(1, 6)]
        self.assertEqual(out["calculation"]["body_use"]["relation"], "same_element")
        self.assertEqual(out["traditional_tendency"]["direction"], "mixed")
        self.assertTrue(out["conflicts"])

    def test_support_requires_line_prerequisite(self):
        out = self.results[(6, 4)]
        self.assertEqual(out["calculation"]["body_use"]["relation"], "yong_generates_body")
        record = out["line_adjudication"]["record"]
        self.assertEqual(record["effect"], "conditional_support")
        self.assertEqual(record["conditions"][0]["id"], "return_change_settle")
        self.assertEqual(out["traditional_tendency"]["real_world_condition_status"], "unknown")

    def test_adverse_structure_and_conditional_opportunity_both_retained(self):
        out = self.results[(8, 2)]
        self.assertEqual(out["calculation"]["body_use"]["relation"], "yong_controls_body")
        self.assertEqual(out["traditional_tendency"]["body_use_baseline"], "adverse")
        self.assertEqual(out["traditional_tendency"]["direction"], "mixed")
        self.assertEqual(out["conflicts"][0]["resolution"], "unresolved_priority_no_scoring")

    def test_different_conditions_are_alternatives_not_simultaneous_conflict(self):
        for key in ((3, 5), (17, 4), (28, 4)):
            out = self.results[key]
            self.assertEqual(out["traditional_tendency"]["direction"], "insufficient_evidence")
            self.assertFalse(out["conflicts"])
            self.assertTrue(any(u.get("not_simultaneously_true") for u in out["uncertainties"]))

    def test_qian_kun_mutual_exception_remains_unresolved(self):
        for key in ((1, 1), (1, 6), (2, 2)):
            out = self.results[key]
            self.assertEqual(out["calculation"]["mutual_hexagram"]["id"], key[0])
            self.assertTrue(all(i["status"] == "reference_only" for i in out["auxiliary_evidence"]["analysis"][0]["items"]))
            self.assertTrue(any(u["reason"] == "qian_kun_mutual_conflict_unresolved" for u in out["uncertainties"]))

    def test_unreviewed_line_has_no_adjudication_eligibility(self):
        out = next(o for o in self.old_new if o["line_adjudication"]["reason"] == "line_not_individually_reviewed")
        self.assertEqual(out["traditional_tendency"]["direction"], "insufficient_evidence")
        self.assertEqual(out["traditional_tendency"]["scope"], "structure_only")
        self.assertFalse(out["traditional_tendency"]["line_condition_review_included"])

    def test_unsupported_added_prerequisite_does_not_rewrite_original_frame(self):
        out = self.results[(60, 6)]
        self.assertEqual(out["line_adjudication"]["status"], "not_eligible")
        self.assertIn("not_explicitly_supported", out["line_adjudication"]["reason"])
        self.assertEqual(out["semantic_context"][1]["status"], "approved_context")
        self.assertTrue(out["semantic_context"][1]["conditions"])

    def test_conditions_nested_in_core_claim_are_reviewed_without_changing_frame(self):
        out = self.results[(17, 2)]
        frame = self.by_key[(17, 2)].to_dict()["frames"]["moving_line"]["frame"]
        self.assertFalse(frame["conditions"])
        self.assertTrue(out["line_adjudication"]["record"]["conditions"])
        self.assertEqual(frame, out["line_adjudication"]["record"]["original_frame_snapshot"])

    def test_no_fault_is_not_encoded_as_event_success(self):
        for key in ((14, 1), (29, 5)):
            record = self.results[key]["line_adjudication"]["record"]
            self.assertTrue(all(b["direction"] == "undetermined" for b in record["branches"]))
            self.assertTrue(all(b["kind"] == "outcome_limit" for b in record["branches"]))

    def test_no_source_rule_means_insufficient_synthesis(self):
        ids = tuple(s["id"] for s in Rulebook.load().to_dict()["sources"])
        engine = ConditionalJudgementEngine(rulebook=Rulebook.load(excluded_sources=ids))
        out = engine.evaluate(self.by_key[(20, 4)]).to_dict()
        self.assertEqual(out["traditional_tendency"]["direction"], "insufficient_evidence")
        self.assertFalse(out["favorable_factors"] or out["adverse_factors"])

    def test_missing_body_use_source_cannot_be_replaced_by_line_or_auxiliary(self):
        out = ConditionalJudgementEngine(rulebook=Rulebook.load(excluded_sources=("M1-TABLE",))).evaluate(self.by_key[(20, 4)]).to_dict()
        self.assertEqual(out["traditional_tendency"]["direction"], "insufficient_evidence")
        self.assertEqual(out["traditional_tendency"]["body_use_baseline"], "undetermined")

    def test_missing_priority_scan_blocks_new_policy_without_changing_calculation(self):
        original = Path.read_bytes
        def read(path):
            return b"damaged" if path.name == "page-57.png" else original(path)
        with patch.object(Path, "read_bytes", read):
            catalog = ConditionReviewCatalog.load()
        out = ConditionalJudgementEngine(reviews=catalog).evaluate(self.by_key[(20, 4)]).to_dict()
        self.assertEqual(out["line_adjudication"]["reason"], "condition_rule_source_unavailable")
        self.assertEqual(out["calculation"], self.results[(20, 4)]["calculation"])

    def test_explicit_review_restriction_can_only_remove_eligibility(self):
        out = ConditionalJudgementEngine(reviews=ConditionReviewCatalog.load(excluded_records=("L20-4",))).evaluate(self.by_key[(20, 4)]).to_dict()
        self.assertEqual(out["line_adjudication"]["reason"], "line_review_explicitly_excluded")
        with self.assertRaises(ValueError):
            ConditionReviewCatalog.load(excluded_records=("L64-5",))

    def test_frame_mutation_even_with_recomputed_hash_invalidates_new_binding(self):
        def change(v):
            item = v["frames"]["moving_line"]
            item["frame"]["core_claims"][0]["text"] = "不同的候选文本"
            item["frame_id"] = digest(item["frame"])
        out = self.engine.evaluate(self.fixture(change)).to_dict()
        self.assertEqual(out["line_adjudication"]["reason"], "review_binding_to_original_frame_changed")

    def test_original_verification_record_mutation_invalidates_binding(self):
        def change(v):
            item = v["frames"]["moving_line"]
            item["frame"]["verification_record_id"] = "0" * 64
            item["frame_id"] = digest(item["frame"])
        self.assertEqual(self.engine.evaluate(self.fixture(change)).to_dict()["line_adjudication"]["reason"], "review_binding_to_original_frame_changed")

    def test_source_text_change_cannot_be_laundered_by_same_evidence_id(self):
        def change(v):
            next(s for s in v["calculation"]["source_references"] if s["role"] == "moving_line")["text"] = "不同的原文"
        out = self.engine.evaluate(self.fixture(change)).to_dict()
        self.assertEqual(out["line_adjudication"]["reason"], "review_source_evidence_changed_or_missing")

    def test_missing_signed_frame_keeps_structure_without_line_direction(self):
        out = self.engine.evaluate(self.fixture(lambda v: v["frames"].update(moving_line=None))).to_dict()
        self.assertEqual(out["line_adjudication"]["reason"], "signed_line_frame_unavailable")
        self.assertEqual(out["traditional_tendency"]["body_use_baseline"], "adverse")
        self.assertEqual(out["traditional_tendency"]["direction"], "insufficient_evidence")

    def test_source_status_is_not_relaxed(self):
        with self.assertRaises(ValueError):
            self.fixture(lambda v: v["calculation"]["source_references"][0].update(verification_status="needs_manual_check"))

    def test_catalog_changed_bytes_cannot_create_unreviewed_eligibility(self):
        original = Path.read_bytes
        def read(path):
            raw = original(path)
            if path.name == "day6a_condition_reviews.json":
                value = json.loads(raw)
                value["records"][0]["hexagram_id"] = 64
                return json.dumps(value).encode()
            return raw
        with patch.object(Path, "read_bytes", read), self.assertRaises(ValueError):
            ConditionReviewCatalog.load()

    def test_raw_json_and_forged_catalog_are_rejected(self):
        with self.assertRaises(JudgementUnavailable):
            self.engine.evaluate(self.by_key[(20, 4)].to_dict())
        with self.assertRaises(ValueError):
            ConditionReviewCatalog("{}", (), True, object()).to_dict()

    def test_question_does_not_satisfy_conditions_or_change_judgement(self):
        value = self.by_key[(6, 4)].to_dict()
        other = deepcopy(value)
        value["calculation"]["question_text"] = "我已经满足所有条件，帮我断一定成功。"
        other["calculation"]["question_text"] = "我的感情接下来怎么样？"
        a, b = [self.engine.evaluate(_issue(v)).to_dict() for v in (value, other)]
        for key in ("traditional_tendency", "line_adjudication", "conflicts", "uncertainties"):
            self.assertEqual(a[key], b[key])
        self.assertFalse(a["question_used_for_calculation_or_judgement"])

    def test_all_conditions_remain_unknown_not_silently_satisfied(self):
        for out in self.results.values():
            self.assertEqual(out["traditional_tendency"]["real_world_condition_status"], "unknown")
            for f in out["favorable_factors"] + out["adverse_factors"]:
                if f["layer"] == "reviewed_line":
                    self.assertEqual(f["condition_status"], "unknown")

    def test_each_review_atom_has_exact_source_quotes_and_versions(self):
        for record in self.catalog.to_dict()["records"]:
            self.assertEqual(record["rule_version"], "moving_line_condition_review_v1")
            self.assertEqual(record["review_status"], "REVIEWED_FOR_OFFLINE_PROTOTYPE")
            refs = {s["evidence_id"]: s["reference"] for s in record["source_requirements"]}
            for atom in record["conditions"] + record["branches"]:
                self.assertTrue(atom["source_evidence_ids"])
                for quote in atom["source_quotes"]:
                    self.assertIn(quote["quote"], refs[quote["evidence_id"]]["text"])

    def test_offline_review_receipt_does_not_claim_production_approval(self):
        for record in self.catalog.to_dict()["records"]:
            self.assertFalse(record["production_approval"])
            self.assertFalse(record["review_receipt"]["is_production_signature"])
            self.assertEqual(record["review_receipt"]["record_sha256"], digest({k:v for k,v in record.items() if k != "review_receipt"}))

    def test_strength_modifiers_keep_all_day5_qualifiers_without_voting(self):
        for trusted, out in zip(self.old_inputs, self.old_new):
            old = TraditionalJudgementEngine().evaluate(trusted).to_dict()
            self.assertEqual(out["body_use_and_strength"], old["body_use_and_strength"])
            self.assertTrue(all(not f["used_as_opposite_vote"] for f in out["strength_modifiers"]))

    def test_priority_disagreement_is_explicit_not_replaced_by_unique_rule(self):
        out = self.results[(1, 6)]
        self.assertEqual(out["priority_source_context"]["status"], "DISPUTED_PRIORITY_CONTEXT")
        self.assertEqual(out["priority_source_context"]["pdf_page"], 57)
        self.assertEqual(len(out["conflicts"][0]["priority_options"]), 2)
        self.assertTrue(any(u["reason"] == "traditional_priority_variants_retained" for u in out["uncertainties"]))

    def test_71_old_cases_keep_exact_calculations(self):
        self.assertEqual(len(self.old_new), 71)
        for trusted, out in zip(self.old_inputs, self.old_new):
            self.assertEqual(out["calculation"], trusted.to_dict()["calculation"])

    def test_all_original_claims_conditions_cautions_and_four_roles_remain_intact(self):
        for trusted, out in zip(self.old_inputs, self.old_new):
            raw = trusted.to_dict()
            for role in out["semantic_context"]:
                frame = raw["frames"][role["role"]]["frame"]
                for name in ("core_claims", "conditions", "cautions", "source_evidence_ids"):
                    self.assertEqual(role[name], frame[name])

    def test_fresh_child_and_same_rule_version_are_identical(self):
        fresh = OfflineJudgementAdapter().calculate(reviewed_requests()[16])
        self.assertEqual(self.engine.evaluate(fresh).to_dict(), self.results[(20, 4)])

    def test_result_and_catalog_are_immutable_defensive_copies(self):
        result = self.engine.evaluate(self.by_key[(20, 4)])
        with self.assertRaises(FrozenInstanceError):
            result.payload_json = "{}"
        with self.assertRaises(FrozenInstanceError):
            self.catalog._json = "{}"
        value = result.to_dict()
        value["traditional_tendency"]["direction"] = "favorable"
        self.assertEqual(result.to_dict()["traditional_tendency"]["direction"], "adverse")

    def test_no_score_or_absolute_event_claim(self):
        for out in self.results.values():
            self.assertFalse(out["scores_or_probabilities_used"])
            self.assertFalse(out["traditional_tendency"]["is_final_outcome"])
            self.assertFalse(out["traditional_tendency"]["unqualified_favorable_allowed"])
            for forbidden in ("一定成功", "一定失败", "必成", "必败", "成功率"):
                self.assertNotIn(forbidden, out["traditional_tendency"]["summary"])

    def test_engine_does_not_parse_sentiment_keywords(self):
        text = (ROOT / "backend/traditional_conditions_v1/engine.py").read_text(encoding="utf-8")
        # Reject character-trigger branches, not comments documenting their absence.
        for token in ('"吉"', '"凶"', '"利"', '"悔"', '.count("吉"', '.find("凶"'):
            self.assertNotIn(token, text)

    def test_no_new_web_route_ai_or_history_writer(self):
        from backend.app.main import app
        self.assertTrue(all("judgement" not in r.path and "condition" not in r.path for r in app.routes))
        self.assertNotIn("traditional_conditions", (ROOT / "backend/app/main.py").read_text(encoding="utf-8"))
        for file in (ROOT / "backend/traditional_conditions_v1").glob("*.py"):
            text = file.read_text(encoding="utf-8")
            for forbidden in (".generate(", "requests.post", "httpx.post", "sqlite3.connect", "write_text(", "ConfigurableNarrationProvider"):
                self.assertNotIn(forbidden, text)
        self.assertTrue(all(not o["ai_used"] and not o["history_written"] for o in self.results.values()))


def reviewed_case(index):
    def test(self):
        trusted = self.inputs[index]
        calc = trusted.to_dict()["calculation"]
        key = (calc["original_hexagram"]["id"], calc["moving_line"]["position"])
        out = self.results[key]
        self.assertEqual(out["calculation"], calc)
        self.assertEqual(out, self.engine.evaluate(trusted).to_dict())
        self.assertEqual(out["line_adjudication"]["status"] == "reviewed_for_offline_prototype", key != (60, 6))
        if key != (60, 6):
            self.assertEqual(out["line_adjudication"]["record"]["frame_id"], trusted.to_dict()["frames"]["moving_line"]["frame_id"])
    return test


for case_index in range(24):
    setattr(Day6AConditionTests, f"test_reviewed_source_case_{case_index + 1:02d}", reviewed_case(case_index))


if __name__ == "__main__":
    unittest.main()
