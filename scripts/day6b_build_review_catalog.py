"""Build the explicit pilot artifact only; no candidate auto-promotion interface."""

from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.traditional_judgement_v1.trusted_input import digest
from backend.condition_review_tools_v1.pipeline import FIELDS, row_binding, validate_review_record
from scripts.day6b_review_definitions import DEFINITIONS, FAILURES, BRANCH_CONDITION_BINDINGS


def build():
    inventory = json.loads((ROOT / "docs/day6b_signed_frame_inventory.json").read_bytes())
    prior = json.loads((ROOT / "data/day6a_condition_reviews.json").read_bytes())
    old_keys = {(r["hexagram_id"], r["position"]) for r in prior["records"]}
    by_key = {(r["hexagram_id"], r["position"]): r for r in inventory["rows"]}
    if not 24 <= len(DEFINITIONS) <= 48 or len({d[:2] for d in DEFINITIONS}) != len(DEFINITIONS):
        raise ValueError("invalid_pilot_size")
    records = []
    for hid, pos, state, effect, note, conditions, branches in deepcopy(DEFINITIONS):
        if (hid, pos) in old_keys:
            raise ValueError("prior_review_replacement_forbidden")
        row = by_key[(hid, pos)]
        frame = row["frame"]
        refs = {r["evidence_id"]: r for r in row["source_references"] if r["evidence_id"] in frame["source_evidence_ids"]}
        for i, atom in enumerate(conditions):
            atom["id"] = f"condition_{i+1}"
        for i, atom in enumerate(branches):
            atom["id"] = f"branch_{i+1}"
            binding = BRANCH_CONDITION_BINDINGS.get((hid, pos))
            indexes = binding[i] if binding else range(len(conditions))
            atom["condition_ids"] = [conditions[j]["id"] for j in indexes]
        for atom in conditions + branches:
            matches = [r for r in refs.values() if r["section_type"] == atom["field"] and atom["quote"] in r["text"]]
            if not matches:
                raise ValueError(f"exact_source_quote_unavailable:{hid}:{pos}:{atom['id']}")
            atom["source_evidence_ids"] = [r["evidence_id"] for r in matches]
            atom["source_quotes"] = [{"evidence_id": r["evidence_id"], "start": r["text"].index(atom["quote"]),
                "end": r["text"].index(atom["quote"]) + len(atom["quote"]), "quote": atom["quote"]} for r in matches]
            atom["basis"] = "SOURCE_BOUNDED_PROJECT_ENCODING"
        record = {
            "record_id": f"DAY6B-L{hid:02d}-{pos}", "target": [hid, pos],
            "hexagram_name": row["hexagram_name"], "line_name": row["line_name"],
            "rule_version": "moving_line_condition_review_batch_v2",
            "policy_version": "traditional_condition_synthesis_v1",
            "state": state, "eligible": state == "reviewed", "effect": effect,
            "summary": note, "failure_reason": FAILURES.get((hid, pos)),
            "conditions": conditions, "branches": branches,
            "branch_relationship": "alternative_not_simultaneous" if effect == "alternative_scopes" else "joint_source_constraints",
            "scope_limits": [], "covered_atoms": [f"{f}:{i}" for f in FIELDS for i, a in enumerate(frame[f])],
            "frame_id": row["frame_id"], "source_fingerprint": frame["source_fingerprint"],
            "original_verification_record_id": frame["verification_record_id"],
            "original_frame_snapshot": frame, "source_metadata": row["source_metadata"],
            "source_requirements": [{"evidence_id": r["evidence_id"], "reference_sha256": digest(r), "reference": r} for r in refs.values()],
            "binding_sha256": row_binding(row), "condition_satisfaction": "unknown",
            "review_method": "individual_literal_source_and_signed_frame_scope_review",
            "semantic_review_note": note,
            "human_verified": False, "production_approval": False,
            "readiness": "branch_unresolved" if state == "reviewed" and effect == "alternative_scopes" else
                         "bounded_synthesis_eligible" if state == "reviewed" else "new_adjudication_excluded",
            "review_limits": ["离线逐条语义复核记录，不是人工 verified 或原生产签名。",
                "未判断用户现实满足条件；所有前提保持 unknown。",
                "异文保留原始见证，不自动选择正确版本。",
                "未导入任何新古注，不涉及应期或现实必然结果。"],
        }
        record["review_receipt"] = {"version": "offline_condition_review_receipt_v2", "record_sha256": digest(record),
                                    "is_production_signature": False}
        failures = validate_review_record(record, row)
        if failures:
            raise ValueError(f"invalid_review:{hid}:{pos}:{failures}")
        records.append(record)
    result = {"version": "moving_line_condition_review_batch_v2", "policy_version": "traditional_condition_synthesis_v1",
              "prior_review_catalog_sha256": digest(prior), "signed_inventory_sha256": digest(inventory),
              "definitions_sha256": digest(DEFINITIONS), "production_approval": False, "records": records}
    target = ROOT / "data/day6b_condition_reviews.json"
    if target.exists() and digest(json.loads(target.read_bytes())) != digest(result):
        raise ValueError("existing_batch_replacement_requires_new_version")
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    result = build()
    print(json.dumps({"pilot": len(result["records"]), "eligible": sum(r["eligible"] for r in result["records"]),
                      "catalog_sha256": digest(result)}))
