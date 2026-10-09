"""Extractive candidates cannot turn themselves into an approved offline record."""

from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from backend.app.meihua_models import ManualInput
from backend.condition_review_tools_v1 import pipeline as p
from backend.traditional_judgement_v1 import OfflineJudgementAdapter
from backend.traditional_judgement_v1.trusted_input import digest, _issue
from backend.traditional_judgement_v1.rulebook import Rulebook

ROOT = Path(__file__).resolve().parents[1]
MOMENT = "2026-09-24T19:45:35+08:00"


class CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = json.loads((ROOT / "docs/day6b_signed_frame_inventory.json").read_bytes())
        cls.rows = {(r["hexagram_id"], r["position"]): r for r in cls.inventory["rows"]}

    def row(self):
        return deepcopy(self.rows[(4, 1)])

    def test_384_original_signed_frames(self):
        self.assertEqual(len(self.rows), 384)
        self.assertEqual(self.inventory["signed_approved_frames"], 384)
        self.assertTrue(self.inventory["day6a_inventory_matches"])

    def test_all_737_atoms_remain_candidates(self):
        values = [c for r in self.rows.values() for c in p.generate_candidates(r)]
        self.assertEqual(len(values), 737)
        self.assertTrue(all(c["status"] == "candidate" and not c["eligible"] for c in values))

    def test_every_source_id_and_range_exact(self):
        for row in self.rows.values():
            refs = p._refs(row)
            for c in p.generate_candidates(row):
                self.assertTrue(c["source_ranges"])
                for scope in c["source_ranges"]:
                    self.assertTrue(scope["source_id"])
                    self.assertEqual(scope["quote"], refs[scope["evidence_id"]]["text"][scope["start"]:scope["end"]])

    def test_original_limits_preserved_including_core(self):
        for c in p.generate_candidates(self.row()):
            self.assertEqual(c["original_limits"], {f: self.row()["frame"][f] for f in p.FIELDS})

    def test_empty_conditions_never_implies_unconditional(self):
        row = self.rows[(1, 3)]
        self.assertFalse(row["frame"]["conditions"])
        self.assertTrue(all(c["semantic_alignment"] == "requires_individual_review" for c in p.generate_candidates(row)))

    def test_complete_extraction_does_not_approve(self):
        row = self.row()
        out = p.inspect_proposal(p.make_proposal(row), row)
        self.assertTrue(out["mechanically_complete"])
        self.assertFalse(out["eligible"])
        self.assertFalse(out["semantic_review_performed"])

    def test_candidate_condition_omission(self):
        row = self.row()
        proposal = p.make_proposal(row)
        proposal["candidates"] = [c for c in proposal["candidates"] if c["field"] != "conditions"]
        self.assertIn("omitted_original_atom_or_condition", p.inspect_proposal(proposal, row)["findings"])

    def test_caution_omission(self):
        row = deepcopy(self.rows[(18, 2)])
        proposal = p.make_proposal(row)
        proposal["candidates"] = [c for c in proposal["candidates"] if c["field"] != "cautions"]
        self.assertIn("omitted_original_atom_or_condition", p.inspect_proposal(proposal, row)["findings"])

    def test_limits_array_omission(self):
        row = self.row()
        proposal = p.make_proposal(row)
        proposal["original_limits"]["conditions"] = []
        self.assertIn("omitted_or_changed_original_limits", p.inspect_proposal(proposal, row)["findings"])

    def test_expanded_candidate_meaning(self):
        row = self.row()
        proposal = p.make_proposal(row)
        proposal["candidates"][0]["text"] += "所以事情一定成功"
        self.assertIn("candidate_changed_or_expanded", p.inspect_proposal(proposal, row)["findings"])

    def test_fake_extra_candidate(self):
        row = self.row()
        proposal = p.make_proposal(row)
        proposal["candidates"].append({"candidate_id": "fake", "text": "大吉"})
        self.assertIn("unsupported_candidate_or_expanded_meaning", p.inspect_proposal(proposal, row)["findings"])

    def test_false_candidate_promotion(self):
        row = self.row()
        proposal = p.make_proposal(row)
        proposal["candidates"][0].update(status="reviewed", eligible=True)
        self.assertIn("unauthorized_candidate_promotion", p.inspect_proposal(proposal, row)["findings"])

    def test_duplicate_candidate(self):
        row = self.row()
        proposal = p.make_proposal(row)
        proposal["candidates"].append(proposal["candidates"][0])
        self.assertIn("duplicate_candidate", p.inspect_proposal(proposal, row)["findings"])

    def test_source_fingerprint_change(self):
        row = self.row()
        proposal = p.make_proposal(row)
        row["frame"]["source_fingerprint"] = "changed"
        self.assertIn("source_or_frame_binding_changed", p.inspect_proposal(proposal, row)["findings"])

    def test_source_unusable(self):
        row = self.row()
        for ref in row["source_references"]:
            ref["verification_status"] = "needs_manual_check"
        self.assertIn("source_status_unusable", p.row_failures(row))

    def test_source_missing(self):
        row = self.row()
        row["source_references"] = []
        self.assertIn("evidence_missing", p.row_failures(row))

    def test_atom_source_mismatch(self):
        row = self.row()
        row["frame"]["core_claims"][0]["supported_by"] = ["unknown-source"]
        self.assertIn("atom_evidence_inconsistent", p.row_failures(row))

    def test_source_variant_does_not_auto_decide_version(self):
        row = self.rows[(32, 3)]
        proposal = p.make_proposal(row)
        self.assertIn("source_variant_requires_scope_review", p.inspect_proposal(proposal, row)["findings"])
        quotes = [s["quote"] for c in proposal["candidates"] for s in c["source_ranges"]]
        self.assertTrue(any("𢘆" in q for q in quotes))
        self.assertTrue(any("恒" in q for q in quotes))

    def test_opposite_candidate_branches_need_scope_review(self):
        row = self.row()
        proposal = p.make_proposal(row)
        proposal["branches"] = [{"direction": "favorable"}, {"direction": "adverse"}]
        self.assertIn("potential_contradiction_requires_scope_review", p.inspect_proposal(proposal, row)["findings"])

    def test_process_meta_text_flagged(self):
        row = self.rows[(40, 1)]
        self.assertIn("process_meta_text_requires_scope_review", p.inspect_proposal(p.make_proposal(row), row)["findings"])

    def test_deterministic_proposal(self):
        self.assertEqual(p.make_proposal(self.row()), p.make_proposal(self.row()))

    def test_no_effect_enum_from_keyword(self):
        for c in p.generate_candidates(self.row()):
            self.assertNotIn("direction", c)
            self.assertNotIn("effect", c)

    def test_source_cues_surface_missing_array_conditions_without_approval(self):
        row = self.rows[(1, 3)]
        signals = [s for c in p.generate_candidates(row) for s in c["potential_signals"]]
        self.assertTrue(any(s["quote"] == "惕" for s in signals))
        self.assertTrue(any(s["quote"] == "若" for s in signals))
        self.assertTrue(all(not s["semantic_condition_established"] for s in signals))

    def test_potential_scope_and_result_cues_are_exact(self):
        row = self.rows[(2, 3)]
        signals = [s for c in p.generate_candidates(row) for s in c["potential_signals"]]
        self.assertTrue(any(s["kind"] == "potential_alternative_scope" for s in signals))
        self.assertTrue(all(s["quote"] == s["context"][s["start"]:s["end"]] for s in signals))

    def test_polarity_words_never_generate_direction(self):
        self.assertEqual(p.potential_signals("吉凶利悔", "test"), [])


class ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = p.load_catalog()
        inventory = json.loads((ROOT / "docs/day6b_signed_frame_inventory.json").read_bytes())
        cls.rows = {(r["hexagram_id"], r["position"]): r for r in inventory["rows"]}
        requests = [ManualInput(input_mode="manual_hexagram", hexagram_id=r["target"][0], moving_line=r["target"][1], cast_at=MOMENT)
                    for r in cls.catalog["records"]]
        cls.trusted = dict(zip([tuple(r["target"]) for r in cls.catalog["records"]], OfflineJudgementAdapter().calculate_batch(requests)))

    def test_32_new_targets_disjoint_from_prior_24(self):
        prior = json.loads((ROOT / "data/day6a_condition_reviews.json").read_bytes())
        old = {(r["hexagram_id"], r["position"]) for r in prior["records"]}
        self.assertEqual(len(self.trusted), 32)
        self.assertFalse(set(self.trusted) & old)

    def test_eligibility_count_and_states(self):
        records = self.catalog["records"]
        self.assertEqual(sum(r["eligible"] for r in records), 29)
        self.assertEqual(sum(r["state"] == "disputed" for r in records), 2)
        self.assertEqual(sum(r["state"] == "insufficient_evidence" for r in records), 1)

    def test_branch_unresolved_count(self):
        self.assertEqual(sum(r["readiness"] == "branch_unresolved" for r in self.catalog["records"]), 11)

    def test_not_human_verified_or_production_signed(self):
        for r in self.catalog["records"]:
            self.assertFalse(r["human_verified"])
            self.assertFalse(r["production_approval"])
            self.assertFalse(r["review_receipt"]["is_production_signature"])

    def test_candidate_not_trusted_input(self):
        self.assertEqual(p.lookup_review(p.make_proposal(self.rows[(4, 1)]))[1], "guarded_signed_input_required")

    def test_arbitrary_catalog_and_fake_receipt_cannot_approve(self):
        value = deepcopy(self.catalog)
        r = value["records"][0]
        r["summary"] = "必然成功"
        r["review_receipt"]["record_sha256"] = digest({k: v for k, v in r.items() if k != "review_receipt"})
        self.assertEqual(p.lookup_review(self.trusted[(1, 3)], catalog=value)[1], "untrusted_offline_catalog")

    def test_changed_source_cannot_use_review(self):
        value = self.trusted[(1, 3)].to_dict()
        for r in value["calculation"]["source_references"]:
            if r["role"] == "moving_line":
                r["text"] += "changed"
        self.assertIsNone(p.lookup_review(_issue(value))[0])

    def test_changed_frame_cannot_use_review(self):
        value = self.trusted[(1, 3)].to_dict()
        value["frames"]["moving_line"]["frame"]["core_claims"][0]["text"] = "一定成功"
        self.assertIsNone(p.lookup_review(_issue(value))[0])

    def test_missing_frame_cannot_use_review(self):
        value = self.trusted[(1, 3)].to_dict()
        value["frames"]["moving_line"] = None
        self.assertEqual(p.lookup_review(_issue(value))[1], "signed_frame_unavailable")

    def test_unavailable_rule_source_fails_closed(self):
        book = Rulebook.load(excluded_sources=("M1-TABLE",))
        self.assertEqual(p.lookup_review(self.trusted[(1, 3)], book=book)[1], "condition_rule_source_unavailable")

    def test_arbitrary_rulebook_rejected(self):
        self.assertEqual(p.lookup_review(self.trusted[(1, 3)], book=object())[1], "untrusted_rulebook")

    def test_pinned_catalog_cannot_be_changed_on_disk(self):
        value = deepcopy(self.catalog)
        value["records"][0]["eligible"] = False
        original_read = Path.read_bytes
        def changed_read(path):
            if path == ROOT / "data/day6b_condition_reviews.json":
                return json.dumps(value).encode("utf-8")
            return original_read(path)
        with patch.object(Path, "read_bytes", changed_read), self.assertRaises(ValueError):
            p.load_catalog()

    def test_invalid_range_rejected(self):
        r = deepcopy(self.catalog["records"][0])
        r["conditions"][0]["source_quotes"][0]["start"] = 9999
        self.assertIn("review_exact_source_range_invalid", p.validate_review_record(r, self.rows[tuple(r["target"])]))

    def test_branch_undefined_condition_rejected(self):
        r = deepcopy(self.catalog["records"][0])
        r["branches"][0]["condition_ids"] = ["unknown"]
        self.assertIn("invalid_branch_condition_binding", p.validate_review_record(r, self.rows[tuple(r["target"])]))

    def test_original_condition_coverage_must_not_be_omitted(self):
        r = deepcopy(next(r for r in self.catalog["records"] if r["target"] == [4, 1]))
        r["covered_atoms"] = [a for a in r["covered_atoms"] if not a.startswith("conditions:")]
        self.assertIn("original_atom_review_omitted", p.validate_review_record(r, self.rows[(4, 1)]))

    def test_real_world_prerequisites_cannot_be_assumed(self):
        r = deepcopy(self.catalog["records"][0])
        r["condition_satisfaction"] = "true"
        self.assertIn("real_world_conditions_must_remain_unknown", p.validate_review_record(r, self.rows[tuple(r["target"])]))

    def test_disputed_cannot_gain_eligibility(self):
        r = deepcopy(next(r for r in self.catalog["records"] if r["state"] == "disputed"))
        r["eligible"] = True
        self.assertIn("nonreviewed_eligibility_forbidden", p.validate_review_record(r, self.rows[tuple(r["target"])]))

    def test_branches_do_not_share_opposite_prerequisites(self):
        for r in self.catalog["records"]:
            if r["effect"] == "alternative_scopes":
                self.assertEqual(r["branch_relationship"], "alternative_not_simultaneous")
                self.assertFalse(set(r["branches"][0]["condition_ids"]) & set(r["branches"][1]["condition_ids"]))

    def test_receipt_tamper_rejected(self):
        r = deepcopy(self.catalog["records"][0])
        r["summary"] += "tamper"
        self.assertIn("offline_receipt_invalid", p.validate_review_record(r, self.rows[tuple(r["target"])]))

    def test_prior_day6a_catalog_pin_unchanged(self):
        from backend.traditional_conditions_v1.catalog import CATALOG_SHA256, ConditionReviewCatalog
        self.assertEqual(digest(ConditionReviewCatalog.load().to_dict()), CATALOG_SHA256)


class WorksheetTests(unittest.TestCase):
    def test_384_review_table_states_isolated(self):
        from scripts.day6b_review_cli import review_table
        table = review_table()
        self.assertEqual(len(table["rows"]), 384)
        self.assertEqual(table["state_counts"], {"reviewed": 52, "insufficient_evidence": 2, "candidate": 328, "disputed": 2})

    def test_worksheet_cannot_replace_prior_review(self):
        from scripts.day6b_review_cli import worksheet
        with self.assertRaises(ValueError):
            worksheet(["20:4"])

    def test_worksheet_cannot_replace_new_review(self):
        from scripts.day6b_review_cli import worksheet
        with self.assertRaises(ValueError):
            worksheet(["4:1"])

    def test_next_worksheet_stays_candidate(self):
        from scripts.day6b_review_cli import worksheet
        value = worksheet(["1:2"])
        self.assertFalse(value["promotion_supported"])
        self.assertFalse(value["rows"][0]["eligible"])

    def test_target_whitelist_and_limits(self):
        from scripts.day6b_review_cli import parse_targets
        for targets in ([], ["65:1"], ["1:0"], ["1:7"], ["../../secret"], ["1:2", "1:2"], ["1:2"] * 49):
            with self.subTest(targets=targets), self.assertRaises(ValueError):
                parse_targets(targets)

    def test_worksheet_deterministic(self):
        from scripts.day6b_review_cli import worksheet
        self.assertEqual(worksheet(["1:2"]), worksheet(["1:2"]))


def _pilot_test(target):
    def run(self):
        record = next(r for r in self.catalog["records"] if tuple(r["target"]) == target)
        self.assertFalse(p.validate_review_record(record, self.rows[target]))
        request = self.trusted[target]
        original = request.to_dict()
        result, reason = p.lookup_review(request)
        self.assertEqual(result is not None, record["eligible"])
        if not record["eligible"]:
            self.assertEqual(reason, record["failure_reason"])
        else:
            self.assertEqual(result, record)
        self.assertEqual(original, request.to_dict())
        self.assertEqual((result, reason), p.lookup_review(request))
    return run


for _r in json.loads((ROOT / "data/day6b_condition_reviews.json").read_bytes())["records"]:
    _target = tuple(_r["target"])
    setattr(ReviewTests, f"test_pilot_{_target[0]:02d}_{_target[1]}", _pilot_test(_target))
