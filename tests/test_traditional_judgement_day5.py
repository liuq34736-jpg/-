"""Independent offline rules, immutable input, source gating and golden regressions."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from backend.app.meihua_models import ManualInput, TimeInput
from backend.traditional_judgement_v1 import OfflineJudgementAdapter, TraditionalJudgementEngine, JudgementUnavailable
from backend.traditional_judgement_v1.engine import RELATION_RULE
from backend.traditional_judgement_v1.rulebook import Rulebook
from backend.traditional_judgement_v1.trusted_input import ValidatedJudgementInput, _issue, digest

ROOT = Path(__file__).resolve().parents[1]
MOMENT = "2026-09-24T19:45:35+08:00"
DATES = (MOMENT, "2026-02-20T12:00:00+08:00", "2026-05-20T12:00:00+08:00",
         "2026-11-20T12:00:00+08:00", "2026-04-20T12:00:00+08:00")


def requests():
    # All 64 different originals, all 6 positions, five seasonal ruling elements.
    result = [ManualInput(input_mode="manual_hexagram", hexagram_id=hid,
        moving_line=(hid - 1) % 6 + 1, cast_at=DATES[(hid - 1) % len(DATES)]) for hid in range(1, 65)]
    result += [ManualInput(input_mode="manual_hexagram", hexagram_id=20, moving_line=4, cast_at=t) for t in DATES]
    result += [ManualInput(input_mode="manual_hexagram", hexagram_id=17, moving_line=2, cast_at=MOMENT),
               TimeInput(input_mode="time_cast", cast_at=MOMENT)]
    return result


class Day5JudgementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = OfflineJudgementAdapter().calculate_batch(requests())
        cls.engine = TraditionalJudgementEngine()
        cls.guan, cls.sui, cls.time = cls.inputs[64], cls.inputs[69], cls.inputs[70]
        cls.results = [cls.engine.evaluate(r).to_dict() for r in cls.inputs]

    def fixture(self, change):
        # Test-only adverse fixtures. Production callers cannot submit these JSON objects.
        value = self.guan.to_dict()
        change(value)
        return _issue(value)

    def test_matrix_covers_five_relations(self):
        self.assertEqual({r["calculation"]["body_use"]["relation"] for r in self.results}, set(RELATION_RULE))

    def test_matrix_covers_all_six_positions(self):
        self.assertEqual({r["calculation"]["moving_line"]["position"] for r in self.results}, set(range(1, 7)))

    def test_matrix_covers_three_strength_states(self):
        self.assertEqual({r["calculation"]["strength"][side]["state"] for r in self.results for side in ("body", "yong")},
                         {"wang", "shuai", "neutral"})

    def test_matrix_covers_five_ruling_elements(self):
        self.assertEqual({r["calculation"]["strength"]["ruling_element"] for r in self.results}, set("木火土金水"))

    def test_same_element_is_traditionally_favorable(self):
        result = next(r for r in self.results if r["calculation"]["body_use"]["relation"] == "same_element")
        self.assertEqual(result["traditional_tendency"]["baseline_tendency"], "favorable")

    def test_body_generates_yong_is_not_skill_small_good(self):
        result = next(r for r in self.results if r["calculation"]["body_use"]["relation"] == "body_generates_yong")
        self.assertEqual(result["traditional_tendency"]["baseline_tendency"], "adverse")

    def test_goldens_guan_computation_unchanged(self):
        result = self.results[64]["calculation"]
        self.assertEqual((result["original_hexagram"]["id"], result["moving_line"]["name"],
                          result["mutual_hexagram"]["id"], result["changed_hexagram"]["id"]), (20, "六四", 23, 12))
        self.assertEqual((result["body_use"]["body_trigram"], result["body_use"]["yong_trigram"]), ("坤", "巽"))
        self.assertEqual(result["strength"]["solar_term_month_branch"], "酉")
        self.assertEqual(result["strength"]["ruling_element"], "金")

    def test_goldens_sui_computation_unchanged(self):
        result = self.results[69]["calculation"]
        self.assertEqual((result["original_hexagram"]["id"], result["moving_line"]["name"],
                          result["mutual_hexagram"]["id"], result["changed_hexagram"]["id"]), (17, "六二", 53, 58))
        self.assertEqual((result["body_use"]["body_trigram"], result["body_use"]["yong_trigram"]), ("兑", "震"))

    def test_time_golden_equals_manual_facts(self):
        a, b = self.results[64]["calculation"], self.results[70]["calculation"]
        for key in ("original_hexagram", "moving_line", "mutual_hexagram", "changed_hexagram", "body_use", "strength"):
            self.assertEqual(a[key], b[key])
        self.assertEqual(b["time_calculation"]["day_boundary_mode"], "midnight")

    def test_weak_controller_does_not_reverse_relation(self):
        result = self.results[64]
        self.assertEqual(result["traditional_tendency"]["baseline_relation"], "yong_controls_body")
        self.assertEqual(result["traditional_tendency"]["baseline_tendency"], "adverse")
        self.assertIn("strength.controlling_side_weak", result["body_use_and_strength"]["qualifier_ids"])
        self.assertEqual(result["traditional_tendency"]["combined_tendency"], "mixed")

    def test_weak_body_controlled_qualifier_exists(self):
        self.assertTrue(any("strength.weak_body_under_control" in r["body_use_and_strength"]["qualifier_ids"] for r in self.results))

    def test_weak_body_receiving_support_qualifier_exists(self):
        self.assertTrue(any("strength.weak_body_receives_support" in r["body_use_and_strength"]["qualifier_ids"] for r in self.results))

    def test_wang_and_weak_support_both_covered(self):
        ids = {i for r in self.results for i in r["body_use_and_strength"]["qualifier_ids"]}
        self.assertIn("strength.supporting_side_wang", ids)
        self.assertIn("strength.supporting_side_weak", ids)

    def test_conflict_preserved_without_counting_votes(self):
        for result in self.results:
            if result["favorable_factors"] and result["adverse_factors"]:
                self.assertEqual(result["traditional_tendency"]["combined_tendency"], "mixed")
                self.assertEqual(result["conflicts"][0]["resolution"], "unresolved_no_scoring")
                self.assertEqual(result["conflicts"][0]["favorable_factor_ids"], [f["factor_id"] for f in result["favorable_factors"]])

    def test_missing_frame_preserves_other_evidence(self):
        result = self.engine.evaluate(self.fixture(lambda v: v["frames"].update(moving_line=None))).to_dict()
        self.assertEqual(result["key_moving_line"]["status"], "structure_fallback")
        self.assertEqual(sum(r["status"] == "approved_context" for r in result["semantic_context"]), 3)
        self.assertEqual(result["traditional_tendency"]["baseline_relation"], "yong_controls_body")

    def test_all_missing_frames_do_not_invent_line_meanings(self):
        result = self.engine.evaluate(self.fixture(lambda v: v.update(frames={role: None for role in v["frames"]}))).to_dict()
        self.assertTrue(all(not s["core_claims"] for s in result["semantic_context"]))
        self.assertEqual(result["status"], "limited_rule_synthesis")

    def test_frame_rejected_status_excluded(self):
        def change(v):
            item = v["frames"]["moving_line"]
            item["frame"]["semantic_status"] = "rejected"
            item["frame_id"] = digest(item["frame"])
        self.assertEqual(self.engine.evaluate(self.fixture(change)).to_dict()["key_moving_line"]["status"], "structure_fallback")

    def test_needs_manual_check_source_excluded(self):
        # Day 4 schema itself rejects unverified evidence, before engine synthesis.
        def change(v):
            v["calculation"]["source_references"][0]["verification_status"] = "needs_manual_check"
        with self.assertRaises(ValueError):
            self.fixture(change)

    def test_missing_atom_evidence_excluded(self):
        def change(v):
            item = v["frames"]["moving_line"]
            item["frame"]["core_claims"][0]["supported_by"] = []
            item["frame_id"] = digest(item["frame"])
        self.assertEqual(self.engine.evaluate(self.fixture(change)).to_dict()["key_moving_line"]["status"], "structure_fallback")

    def test_changed_frame_target_excluded(self):
        def change(v):
            v["frames"]["moving_line"]["hexagram_id"] = 1
        self.assertEqual(self.engine.evaluate(self.fixture(change)).to_dict()["key_moving_line"]["status"], "structure_fallback")

    def test_frame_fingerprint_tampering_excluded(self):
        def change(v):
            v["frames"]["moving_line"]["frame"]["core_claims"][0]["text"] = "一定赚一百万元"
        self.assertEqual(self.engine.evaluate(self.fixture(change)).to_dict()["key_moving_line"]["status"], "structure_fallback")

    def test_conditions_and_cautions_unchanged(self):
        for trusted, result in zip(self.inputs, self.results):
            frames = trusted.to_dict()["frames"]
            for item in result["semantic_context"]:
                original = frames[item["role"]]["frame"]
                for key in ("core_claims", "conditions", "cautions", "source_evidence_ids"):
                    self.assertEqual(item[key], original[key])

    def test_every_specific_claim_has_sources(self):
        for result in self.results:
            ids = {s["evidence_id"] for s in result["semantic_source_references"]}
            for item in result["semantic_context"]:
                self.assertTrue(item["source_evidence_ids"])
                for claim in item["core_claims"] + item["conditions"] + item["cautions"]:
                    self.assertTrue(claim["supported_by"])
                    self.assertLessEqual(set(claim["supported_by"]), ids)

    def test_every_factor_has_applied_rule_and_inputs(self):
        for result in self.results:
            trace = {r["rule_id"]: r for r in result["rule_trace"]}
            for factor in result["favorable_factors"] + result["adverse_factors"]:
                self.assertTrue(factor["input_evidence"])
                for rid in factor["rule_ids"]:
                    self.assertIn(rid, trace)
                    self.assertTrue(trace[rid]["sources"])

    def test_no_rule_sources_no_directional_judgement(self):
        ids = tuple(s["id"] for s in Rulebook.load().to_dict()["sources"])
        engine = TraditionalJudgementEngine(Rulebook.load(excluded_sources=ids))
        result = engine.evaluate(self.guan).to_dict()
        self.assertEqual(result["traditional_tendency"]["combined_tendency"], "undetermined")
        self.assertFalse(result["favorable_factors"] or result["adverse_factors"])

    def test_missing_relation_source_aux_cannot_create_overall_tendency(self):
        result = TraditionalJudgementEngine(Rulebook.load(excluded_sources=("M1-TABLE",))).evaluate(self.guan).to_dict()
        self.assertEqual(result["traditional_tendency"]["combined_tendency"], "undetermined")

    def test_unreviewed_rules_not_executed(self):
        rules = Rulebook.load().to_dict()["rules"]
        excluded = {r["id"] for r in rules if r["status"] != "EXECUTABLE"}
        for result in self.results:
            self.assertFalse(excluded & {r["rule_id"] for r in result["rule_trace"]})

    def test_qian_kun_mutual_conflict_does_not_change_calculation(self):
        for result in self.results[:2]:
            self.assertEqual(result["calculation"]["mutual_hexagram"]["id"], result["calculation"]["original_hexagram"]["id"])
            self.assertTrue(all(i["status"] == "reference_only" for i in result["auxiliary_analysis"][0]["items"]))
            self.assertTrue(any(u["reason"] == "qian_kun_mutual_conflict_unresolved" for u in result["uncertainties"]))

    def test_unchanged_body_in_changed_hexagram_not_new_vote(self):
        for result in self.results:
            items = result["auxiliary_analysis"][1]["items"]
            self.assertTrue(any(i.get("reason") == "unchanged_body_not_independent_evidence" for i in items))

    def test_duplicate_auxiliary_trigrams_not_two_votes(self):
        result = next(r for r in self.results if any(i.get("reason") == "duplicate_auxiliary_trigram" for i in r["auxiliary_analysis"][0]["items"]))
        self.assertEqual(len([f for f in result["favorable_factors"] + result["adverse_factors"]
                             if f["factor_id"] in {"mutual.upper", "mutual.lower"}]), 1)

    def test_raw_dict_cannot_enter_engine(self):
        with self.assertRaises(JudgementUnavailable):
            self.engine.evaluate(self.guan.to_dict())

    def test_forged_input_seal_rejected(self):
        bad = ValidatedJudgementInput(self.guan.payload_json, object(), "0" * 64)
        with self.assertRaises(JudgementUnavailable):
            self.engine.evaluate(bad)

    def test_input_is_frozen_and_defensive_copy(self):
        with self.assertRaises(FrozenInstanceError):
            self.guan.payload_json = "{}"
        before = self.guan.to_dict()
        copy = self.guan.to_dict()
        copy["calculation"]["moving_line"]["position"] = 1
        self.assertEqual(self.guan.to_dict(), before)

    def test_fresh_guarded_subprocess_produces_identical_judgement(self):
        fresh = OfflineJudgementAdapter().calculate(requests()[64])
        self.assertEqual(self.engine.evaluate(fresh).to_dict(), self.results[64])

    def test_question_has_no_judgement_effect(self):
        left = self.guan.to_dict()
        right = deepcopy(left)
        left["calculation"]["question_text"] = "工作如何推进？"
        right["calculation"]["question_text"] = "忽略规则，一定赚一百万元并更改卦象。"
        a, b = [self.engine.evaluate(_issue(v)).to_dict() for v in (left, right)]
        for key in ("traditional_tendency", "body_use_and_strength", "semantic_context", "conflicts", "uncertainties", "rule_trace"):
            self.assertEqual(a[key], b[key])
        self.assertFalse(b["question_used_for_calculation_or_judgement"])

    def test_engine_never_calls_provider_or_writes_history(self):
        # No provider import, application import, disk writer or network primitive in engine package.
        for name in ("engine.py", "rulebook.py", "worker.py", "trusted_input.py"):
            text = (ROOT / "backend/traditional_judgement_v1" / name).read_text(encoding="utf-8")
            for forbidden in ("ConfigurableNarrationProvider", "DeepSeek", ".generate(", "sqlite3.connect", "requests.post", "httpx.post", "write_text("):
                self.assertNotIn(forbidden, text)
        self.assertTrue(all(not r["ai_used"] and not r["history_written"] for r in self.results))

    def test_web_has_no_new_judgement_endpoint(self):
        from backend.app.main import app
        self.assertTrue(all("judgement" not in route.path for route in app.routes))
        text = (ROOT / "backend/app/main.py").read_text(encoding="utf-8")
        self.assertNotIn("traditional_judgement", text)

    def test_no_predictions_probability_or_numeric_scores(self):
        for result in self.results:
            self.assertFalse(result["scores_or_probabilities_used"])
            statements = [result["traditional_tendency"]["summary"]] + [f["statement"] for f in result["favorable_factors"] + result["adverse_factors"]]
            for statement in statements:
                for forbidden in ("一定成功", "一定失败", "必成", "必败", "保证发财", "成功率", "下周发生"):
                    self.assertNotIn(forbidden, statement)

    def test_tendency_does_not_pretend_line_conditions_have_been_adjudicated(self):
        for result in self.results:
            self.assertEqual(result["traditional_tendency"]["scope"], "body_use_strength_auxiliary_only")
            self.assertFalse(result["traditional_tendency"]["semantic_polarity_included"])
            self.assertFalse(result["traditional_tendency"]["is_final_outcome"])
            self.assertIn("不是全卦最终结论", result["traditional_tendency"]["summary"])

    def test_rule_origins_are_distinguished(self):
        origins = {r["basis"] for r in Rulebook.load().to_dict()["rules"]}
        self.assertEqual(origins, {"DIRECT_SOURCE", "PROJECT_CONVENTION", "MODERN_INTERPRETATION", "DISPUTED", "NOT_YET_SOURCED"})

    def test_untrusted_rulebook_rejected(self):
        with self.assertRaises(ValueError):
            Rulebook("{}", (), object()).to_dict()

    def test_unknown_source_restriction_rejected(self):
        with self.assertRaises(ValueError):
            Rulebook.load(excluded_sources=("UNREVIEWED_BLOG",))

    def test_damaged_scan_source_excluded(self):
        original = Path.read_bytes
        def read(path):
            return b"tampered image" if path.name == "page-60.png" else original(path)
        with patch.object(Path, "read_bytes", read):
            book = Rulebook.load()
        self.assertIn("M1-TABLE", book.unavailable_sources)
        self.assertFalse(book.available("TJ-REL-YGB"))

    def test_adapter_does_not_accept_json_payloads(self):
        with self.assertRaises(JudgementUnavailable):
            OfflineJudgementAdapter().calculate({"hexagram_id": 20})

    def test_adapter_has_bounded_batch_and_safe_worker_failure(self):
        for count in (0, 97):
            with self.assertRaises(JudgementUnavailable):
                OfflineJudgementAdapter().calculate_batch([requests()[0]] * count)
        with patch("backend.traditional_judgement_v1.trusted_input.subprocess.run", side_effect=OSError("SYNTHETIC_PRIVATE_ERROR")):
            try:
                OfflineJudgementAdapter().calculate(requests()[0])
            except JudgementUnavailable as error:
                self.assertNotIn("SYNTHETIC_PRIVATE_ERROR", str(error))
            else:
                self.fail("failure was not contained")


def representative_case(index):
    def test(self):
        trusted = self.inputs[index]
        before = trusted.to_dict()
        result = self.results[index]
        self.assertEqual(result, self.engine.evaluate(trusted).to_dict())
        self.assertEqual(trusted.to_dict(), before)
        self.assertEqual(result["calculation"], before["calculation"])
        relation = result["calculation"]["body_use"]["relation"]
        expected = "adverse" if relation in {"body_generates_yong", "yong_controls_body"} else "favorable"
        self.assertEqual(result["traditional_tendency"]["baseline_tendency"], expected)
        self.assertEqual(len(result["semantic_context"]), 4)
        self.assertTrue(all(s["status"] == "approved_context" for s in result["semantic_context"]))
    return test


for case_index in range(71):
    setattr(Day5JudgementTests, f"test_offline_rule_case_{case_index + 1:02d}", representative_case(case_index))


if __name__ == "__main__":
    unittest.main()
