"""Candidates cannot grant eligibility. Only the pinned, individually reviewed batch can.

Text spans are literal code-point offsets, not semantic truth proofs. Semantic review
is explicitly separate; no sentiment/吉凶 classifier or automatic promotion exists.
"""

from copy import deepcopy
import json
from pathlib import Path

from backend.traditional_judgement_v1.trusted_input import digest, ValidatedJudgementInput

ROOT = Path(__file__).resolve().parents[2]
VERSION = "condition_review_tools_v1"
STATES = {"candidate", "reviewed", "disputed", "insufficient_evidence"}
FIELDS = ("core_claims", "conditions", "cautions")
USABLE = {"verified", "machine_verified"}
# Search cues only: no 吉/凶/利/悔 polarity classification. A cue never establishes
# a logical prerequisite or a conclusion; it points the reviewer to a literal span.
POTENTIAL_CUES = {
    "potential_prerequisite": ("若", "如果", "只要", "才能", "須", "须"),
    "potential_behavior_reminder": ("勿", "不可", "敬", "慎", "惕", "不要"),
    "potential_alternative_scope": ("或", "君子", "小人", "從王事", "从王事"),
    "potential_outcome_limit": ("无咎", "無咎", "无譽", "無譽", "未大失", "不敗", "不可用"),
}
# Filled after explicit source/semantic review, never by the candidate extractor.
CATALOG_SHA256 = "0696c750b4fd1c94429e28ed82bed48740bf17d8b9f1b954e3eafcd7896c1bbd"


def _refs(row):
    ids = set(row["frame"]["source_evidence_ids"])
    return {r["evidence_id"]: r for r in row["source_references"] if r["evidence_id"] in ids}


def row_binding(row):
    return digest({"target": [row["hexagram_id"], row["position"]],
                   "frame": row["frame"], "references": _refs(row),
                   "source_metadata": row["source_metadata"]})


def row_failures(row):
    failures = []
    frame = row["frame"]
    refs = _refs(row)
    if row["frame_id"] != digest(frame) or frame["semantic_status"] != "SEMANTIC_APPROVED":
        failures.append("frame_binding_invalid")
    if not frame["source_evidence_ids"] or set(refs) != set(frame["source_evidence_ids"]):
        failures.append("evidence_missing")
    if any(r["verification_status"] not in USABLE for r in refs.values()):
        failures.append("source_status_unusable")
    if set(row["source_metadata"]) != set(refs):
        failures.append("source_metadata_missing")
    for field in FIELDS:
        for atom in frame[field]:
            if not atom["supported_by"] or not set(atom["supported_by"]) <= set(refs):
                failures.append("atom_evidence_inconsistent")
    return sorted(set(failures))


def potential_signals(text, origin):
    signals = []
    for kind, cues in POTENTIAL_CUES.items():
        for cue in cues:
            start = text.find(cue)
            while start >= 0:
                signals.append({"kind": kind, "origin": origin, "start": start,
                    "end": start + len(cue), "quote": cue, "status": "candidate",
                    "context": text, "semantic_condition_established": False})
                start = text.find(cue, start + len(cue))
    return signals


def generate_candidates(row):
    """Literal extraction of *every* signed atom, including all restrictions in core.

Core atoms remain unclassified. conditions/cautions reflect the existing array,
not inferred polarity. Full source ranges accompany each atom; no guessed alignment.
"""
    refs = _refs(row)
    all_limits = {k: deepcopy(row["frame"][k]) for k in FIELDS}
    failures = row_failures(row)
    results = []
    for field in FIELDS:
        for index, atom in enumerate(row["frame"][field]):
            ids = list(atom["supported_by"])
            scope = [{"evidence_id": eid, "source_id": row["source_metadata"].get(eid, {}).get("source_id"),
                      "start": 0, "end": len(refs[eid]["text"]), "quote": refs[eid]["text"],
                      "reference_sha256": digest(refs[eid]),
                      "metadata": deepcopy(row["source_metadata"].get(eid, {}))}
                     for eid in ids if eid in refs]
            value = {"version": VERSION, "target": [row["hexagram_id"], row["position"]],
                     "field": field, "atom_index": index, "text": atom["text"],
                     "frame_range": {"start": 0, "end": len(atom["text"]), "quote": atom["text"]},
                     "potential_kind": {"core_claims": "unclassified_scope",
                                        "conditions": "potential_prerequisite_or_branch",
                                        "cautions": "potential_behavior_or_outcome_limit"}[field],
                     "source_evidence_ids": ids, "source_ranges": scope,
                     "potential_signals": potential_signals(atom["text"], f"frame.{field}:{index}") +
                         [signal for eid in ids if eid in refs
                          for signal in potential_signals(refs[eid]["text"], eid)],
                     "frame_id": row["frame_id"], "source_fingerprint": row["frame"]["source_fingerprint"],
                     "verification_record_id": row["frame"]["verification_record_id"],
                     "binding_sha256": row_binding(row), "original_limits": all_limits,
                     "status": "candidate", "eligible": False, "production_approval": False,
                     "flags": failures,
                     "semantic_alignment": "requires_individual_review",
                     "scope_note": "来源范围为全文上下文，不声称逐字翻译或已判定现实条件。"}
            value["candidate_id"] = "C-" + digest(value)
            results.append(value)
    return results


def inspect_proposal(proposal, row):
    """Fail closed on mechanical omissions/changes. Passing is NOT semantic approval.

An arbitrary fluent paraphrase cannot be certified by this function. New meaning,
opposite directions and source variants require the separate per-record review.
"""
    expected = {c["candidate_id"]: c for c in generate_candidates(row)}
    findings = list(row_failures(row))
    if proposal.get("binding_sha256") != row_binding(row):
        findings.append("source_or_frame_binding_changed")
    atoms = proposal.get("candidates", [])
    if type(atoms) is not list:
        return {"findings": ["invalid_candidate_list"], "eligible": False, "status": "candidate"}
    seen = set()
    for candidate in atoms:
        cid = candidate.get("candidate_id")
        if cid in seen:
            findings.append("duplicate_candidate")
        seen.add(cid)
        original = expected.get(cid)
        if not original:
            findings.append("unsupported_candidate_or_expanded_meaning")
            continue
        if candidate != original:
            findings.append("candidate_changed_or_expanded")
        if candidate.get("status") != "candidate" or candidate.get("eligible") is not False:
            findings.append("unauthorized_candidate_promotion")
    if seen != set(expected):
        findings.append("omitted_original_atom_or_condition")
    if proposal.get("original_limits") != {k: row["frame"][k] for k in FIELDS}:
        findings.append("omitted_or_changed_original_limits")
    # User-supplied interpretation branches are never part of an extractive proposal.
    if proposal.get("branches"):
        findings.append("unreviewed_branch_claims")
        directions = {b.get("direction") for b in proposal["branches"] if isinstance(b, dict)}
        if {"favorable", "adverse"} <= directions:
            findings.append("potential_contradiction_requires_scope_review")
    refs = _refs(row)
    if any(r["variant_present"] for r in refs.values()):
        findings.append("source_variant_requires_scope_review")
    if any("候选" in a["text"] for a in row["frame"]["core_claims"]):
        findings.append("process_meta_text_requires_scope_review")
    return {"findings": sorted(set(findings)), "eligible": False, "status": "candidate",
            "mechanically_complete": not any(f not in {"source_variant_requires_scope_review",
                 "process_meta_text_requires_scope_review"} for f in findings),
            "semantic_review_performed": False}


def make_proposal(row):
    return {"target": [row["hexagram_id"], row["position"]], "binding_sha256": row_binding(row),
            "candidates": generate_candidates(row), "original_limits": {k: row["frame"][k] for k in FIELDS}}


def validate_review_record(record, row):
    """Strict bindings; this checks a reviewed artifact, not authority to create one."""
    failures = row_failures(row)
    if record.get("state") not in STATES:
        failures.append("invalid_review_state")
    if record.get("binding_sha256") != row_binding(row):
        failures.append("review_binding_changed")
    if record.get("original_frame_snapshot") != row["frame"]:
        failures.append("original_frame_or_limits_changed")
    if record.get("production_approval") is not False or record.get("human_verified") is not False:
        failures.append("invalid_approval_scope")
    if record.get("eligible") and record.get("state") != "reviewed":
        failures.append("nonreviewed_eligibility_forbidden")
    covered = record.get("covered_atoms", [])
    expected = [f"{f}:{i}" for f in FIELDS for i, a in enumerate(row["frame"][f])]
    if covered != expected:
        failures.append("original_atom_review_omitted")
    refs = _refs(row)
    conditions = record.get("conditions", [])
    branches = record.get("branches", [])
    ids = [c["id"] for c in conditions]
    if len(ids) != len(set(ids)):
        failures.append("duplicate_condition_id")
    if record.get("eligible") and (not conditions or not branches):
        failures.append("review_scope_or_branch_missing")
    requirements = record.get("source_requirements", [])
    if {s["evidence_id"] for s in requirements} != set(refs):
        failures.append("review_source_requirements_incomplete")
    for source in requirements:
        ref = refs.get(source["evidence_id"])
        if not ref or source["reference_sha256"] != digest(ref):
            failures.append("review_source_inconsistent")
    for atom in conditions + branches + record.get("scope_limits", []):
        quotes = atom.get("source_quotes", [])
        if not quotes or not atom.get("source_evidence_ids"):
            failures.append("review_quote_missing")
        if set(atom.get("source_evidence_ids", [])) != {q["evidence_id"] for q in quotes}:
            failures.append("review_atom_sources_inconsistent")
        for q in quotes:
            ref = refs.get(q["evidence_id"])
            start, end = q.get("start"), q.get("end")
            if (not ref or type(start) is not int or type(end) is not int or not 0 <= start < end <= len(ref["text"])
                    or ref["text"][start:end] != q["quote"] or ref["section_type"] != atom["field"]):
                failures.append("review_exact_source_range_invalid")
        if "direction" in atom and (atom["direction"] not in {"favorable", "adverse", "undetermined"}
                or not set(atom.get("condition_ids", [])) <= set(ids) or not atom.get("condition_ids")):
            failures.append("invalid_branch_condition_binding")
    if record.get("condition_satisfaction") != "unknown":
        failures.append("real_world_conditions_must_remain_unknown")
    receipt = record.get("review_receipt", {})
    if (receipt.get("record_sha256") != digest({k: v for k, v in record.items() if k != "review_receipt"})
            or receipt.get("is_production_signature") is not False):
        failures.append("offline_receipt_invalid")
    return sorted(set(failures))


def load_catalog():
    value = json.loads((ROOT / "data/day6b_condition_reviews.json").read_bytes())
    if digest(value) != CATALOG_SHA256:
        raise ValueError("offline_review_catalog_changed")
    prior = json.loads((ROOT / "data/day6a_condition_reviews.json").read_bytes())
    inventory = json.loads((ROOT / "docs/day6b_signed_frame_inventory.json").read_bytes())
    if digest(prior) != value["prior_review_catalog_sha256"] or digest(inventory) != value["signed_inventory_sha256"]:
        raise ValueError("review_dependency_changed")
    return value


def lookup_review(request, catalog=None, book=None):
    """Fresh guarded input required; a candidate/dict cannot bypass fixed review scope."""
    from backend.traditional_judgement_v1 import TraditionalJudgementEngine
    from backend.traditional_judgement_v1.rulebook import Rulebook
    from backend.traditional_conditions_v1.catalog import ConditionReviewCatalog
    if type(request) is not ValidatedJudgementInput:
        return None, "guarded_signed_input_required"
    approved = load_catalog()
    if catalog is not None and digest(catalog) != digest(approved):
        return None, "untrusted_offline_catalog"
    book = book or Rulebook.load()
    if type(book) is not Rulebook:
        return None, "untrusted_rulebook"
    policy = ConditionReviewCatalog.load()
    if not policy.priority_source_available or any(not book.available(dep)
           for rule in policy.to_dict()["rules"] for dep in rule["dependencies"]):
        return None, "condition_rule_source_unavailable"
    payload = request.to_dict()
    before = TraditionalJudgementEngine(book).evaluate(request).to_dict()
    if before["traditional_tendency"]["baseline_tendency"] == "undetermined":
        return None, "condition_rule_source_unavailable"
    calc = payload["calculation"]
    key = [calc["original_hexagram"]["id"], calc["moving_line"]["position"]]
    record = next((r for r in approved["records"] if r["target"] == key), None)
    if not record:
        return None, "line_not_individually_reviewed"
    if not record["eligible"] or record["state"] != "reviewed":
        return None, record["failure_reason"]
    item = payload["frames"]["moving_line"]
    if item is None or before["key_moving_line"]["status"] != "approved_context":
        return None, "signed_frame_unavailable"
    refs = [r for r in calc["source_references"] if r["role"] == "moving_line"]
    row = {"hexagram_id": key[0], "position": key[1], "frame_id": item["frame_id"],
           "frame": item["frame"], "source_references": refs,
           "source_metadata": record["source_metadata"]}
    failures = validate_review_record(record, row)
    if failures:
        return None, ";".join(failures)
    return deepcopy(record), None
