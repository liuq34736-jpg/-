"""Bounded conditional synthesis, without AI, keyword polarity, scores or storage."""

from dataclasses import dataclass, field
import json

from backend.traditional_judgement_v1.engine import TraditionalJudgementEngine
from backend.traditional_judgement_v1.rulebook import Rulebook
from backend.traditional_judgement_v1.trusted_input import ValidatedJudgementInput, JudgementUnavailable, canonical, digest
from .catalog import ConditionReviewCatalog

VERSION = "traditional_condition_synthesis_v1"
LABELS = {"favorable": "偏有利（有条件）", "adverse": "偏不利（有范围限制）",
          "mixed": "主要依据存在未决张力", "insufficient_evidence": "综合裁决证据不足"}


@dataclass(frozen=True)
class ConditionalJudgementResult:
    payload_json: str = field(repr=False)

    def to_dict(self):
        return json.loads(self.payload_json)


class ConditionalJudgementEngine:
    version = VERSION

    def __init__(self, *, rulebook=None, reviews=None):
        self.book = rulebook or Rulebook.load()
        self.reviews = reviews or ConditionReviewCatalog.load()
        if type(self.book) is not Rulebook or type(self.reviews) is not ConditionReviewCatalog:
            raise ValueError("untrusted_condition_configuration")
        self.book.to_dict()
        self.reviews.to_dict()
        self.structure = TraditionalJudgementEngine(self.book)

    def evaluate(self, request: ValidatedJudgementInput):
        if type(request) is not ValidatedJudgementInput:
            raise JudgementUnavailable()
        payload = request.to_dict()
        before = self.structure.evaluate(request).to_dict()
        calc = before["calculation"]
        base = before["traditional_tendency"]["baseline_tendency"]
        record, excluded_reason = self.reviews.lookup(payload, before["key_moving_line"], self.book)
        catalog = self.reviews.to_dict()
        direction = base if base in {"favorable", "adverse"} else "insufficient_evidence"
        reviewed = record is not None and base != "undetermined"
        conflicts, divergences, unresolved, factors = [], [], [], []
        qualifiers = before["body_use_and_strength"]["qualifier_ids"]
        primary = next((f for f in before["favorable_factors"] + before["adverse_factors"]
                        if f["factor_id"] == "primary.body_use"), None)
        if primary:
            factors.append({**primary, "scope": "body_use_base_only", "not_an_event_outcome": True})
        if not reviewed:
            direction = "insufficient_evidence"
            unresolved.append({"reason": excluded_reason or "body_use_rule_source_unavailable",
                               "structural_baseline_retained": base})
        elif record["effect"] == "alternative_scopes":
            direction = "insufficient_evidence"
            unresolved.append({"reason": "alternative_conditions_not_selected",
                "branches": [b["id"] for b in record["branches"]],
                "not_simultaneously_true": True, "rule_id": "TJ6-ALTERNATIVE-SCOPES"})
        else:
            # Explicitly reviewed branch enums determine scope; no text sentiment parsing.
            opposite = "adverse" if base == "favorable" else "favorable"
            if (record["effect"] in {"adverse_warning", "conditional_support"}
                    and any(b["direction"] == opposite for b in record["branches"])):
                direction = "mixed"
                conflicts.append({"type": "primary_conditional_tension", "rule_id": "TJ6-PRIMARY-TENSION",
                    "body_use_direction": base,
                    "line_branch_ids": [b["id"] for b in record["branches"] if b["direction"] == opposite],
                    "condition_ids": [c["id"] for c in record["conditions"]],
                    "condition_status": "unknown", "observed_real_world_conflict": False,
                    "resolution": "unresolved_priority_no_scoring",
                    "priority_options": ["body_use_primary_with_line_constraints", "line_first_with_body_use_context"],
                    "note": "两层规则有条件性张力；未证明现实条件同时成立，也不裁定哪层必然胜出。"})
            elif record["effect"] == "bounded_opportunity":
                divergences.append({"type": "different_scope_line_opportunity", "rule_id": "TJ6-LINE-SCOPE",
                    "line_branch_ids": [b["id"] for b in record["branches"]],
                    "reason": "specific_action_benefit_not_same_as_whole_event_direction",
                    "is_primary_conflict": False})
        if record:
            for branch in record["branches"]:
                if branch["direction"] in {"favorable", "adverse"}:
                    factors.append({"factor_id": "line." + branch["id"], "polarity": branch["direction"],
                        "statement": branch["text"], "layer": "reviewed_line",
                        "scope": "specific_action_only" if record["effect"] == "bounded_opportunity" else "source_conditional_scope",
                        "condition_ids": branch["condition_ids"], "condition_status": "unknown",
                        "source_evidence_ids": branch["source_evidence_ids"], "source_quotes": branch["source_quotes"],
                        "rule_ids": ["TJ6-LINE-SCOPE", "TJ6-CONDITION-UNKNOWN"], "not_an_event_outcome": True})
            unresolved.append({"reason": "real_world_prerequisites_not_assessed",
                "condition_ids": [c["id"] for c in record["conditions"]],
                "question_used_to_satisfy_conditions": False})
        # Keep Day 5 qualifiers; they constrain the same relation instead of voting
        # for an opposite direction. Likewise auxiliary phases cannot win by count.
        modifiers = [{**f, "effect": "limits_or_supports_same_relation", "used_as_opposite_vote": False}
                     for f in before["favorable_factors"] + before["adverse_factors"] if f["layer"] == "qualifier"]
        aux_factors = [f for f in before["favorable_factors"] + before["adverse_factors"] if f["layer"] == "auxiliary"]
        for aux in before["auxiliary_analysis"]:
            name = "mutual" if aux["role"] == "mutual_hexagram" else "changed"
            directional = [f for f in aux_factors if f["factor_id"].startswith(name + ".")
                           and not f["factor_id"].endswith((".weak_controller", ".weak_support"))]
            if base in {"favorable", "adverse"} and any(f["polarity"] != base for f in directional):
                divergences.append({"type": "auxiliary_phase_divergence", "role": aux["role"],
                    "factor_ids": [f["factor_id"] for f in directional if f["polarity"] != base],
                    "is_primary_conflict": False, "changes_main_label": False,
                    "rule_id": "TJ6-AUXILIARY-DIVERGENCE"})
        phase_directions = {name: {f["polarity"] for f in aux_factors
                            if f["factor_id"].startswith(name + ".")
                            and not f["factor_id"].endswith((".weak_controller", ".weak_support"))}
                            for name in ("mutual", "changed")}
        if phase_directions["mutual"] and phase_directions["changed"] and phase_directions["mutual"] != phase_directions["changed"]:
            divergences.append({"type": "between_auxiliary_phases", "is_primary_conflict": False,
                "changes_main_label": False, "rule_id": "TJ6-AUXILIARY-DIVERGENCE"})
        unresolved += [u for u in before["uncertainties"]
                       if u["reason"] != "moving_line_polarity_and_conditions_not_structurally_adjudicated"]
        if reviewed:
            unresolved.append({"reason": "traditional_priority_variants_retained",
                "rule_id": "TJ6-PRIORITY-UNRESOLVED", "project_policy_not_unique_traditional_truth": True})
        if not reviewed:
            summary = "仅保留体用结构层依据，尚无足够的逐爻条件审核支持综合裁决。"
        elif direction == "insufficient_evidence":
            summary = "原爻存在不同适用条件分支，现有输入不能选择分支；综合倾向暂不能确定。" + record["summary"]
        else:
            summary = "体用基础" + ("偏有利" if base == "favorable" else "偏不利") + "；" + record["summary"]
            if "strength.controlling_side_weak" in qualifiers:
                summary += "克体一方衰，其作用受限，但用克体仍在，不能当成不利已消除。"
            if conflicts:
                summary += "主要依据存在条件性张力，保留两种优先解释，暂不选定单一结果。"
            if any(d["type"] in {"auxiliary_phase_divergence", "between_auxiliary_phases"} for d in divergences):
                summary += "互变的不同方向仅作阶段辅助分歧，不单独改判混合。"
        summary += "未确认现实前提已满足；以上是有范围限制的传统规则分析，不是事情必然成功或失败的预测。"
        rules = [{**r, "source_references": [ref for dep in r["dependencies"] for ref in self.book.references(dep)],
                  "available": self.reviews.priority_source_available and all(self.book.available(dep) for dep in r["dependencies"])}
                 for r in catalog["rules"]]
        result = {"engine_version": VERSION, "condition_rule_version": catalog["version"],
            "prototype_status": "offline_pending_acceptance", "calculation": calc,
            "calculation_fingerprint": digest(calc), "input_fingerprint": digest(payload),
            "traditional_tendency": {"direction": direction, "label": LABELS[direction], "summary": summary,
                "body_use_baseline": base, "baseline_relation": calc["body_use"]["relation"],
                "scope": "bounded_reviewed_synthesis" if reviewed else "structure_only",
                "line_condition_review_included": reviewed, "is_final_outcome": False,
                "unqualified_favorable_allowed": False, "real_world_condition_status": "unknown"},
            "line_adjudication": {"status": "reviewed_for_offline_prototype" if reviewed else "not_eligible",
                "record": record, "reason": excluded_reason, "rule_id": "TJ6-ELIGIBILITY"},
            "primary_evidence": {"body_use": primary, "moving_line": before["key_moving_line"]},
            "body_use_and_strength": before["body_use_and_strength"], "strength_modifiers": modifiers,
            "auxiliary_evidence": {"analysis": before["auxiliary_analysis"], "factors": aux_factors,
                                   "scope": "internal_process_and_change_direction_only"},
            "favorable_factors": [f for f in factors if f["polarity"] == "favorable"],
            "adverse_factors": [f for f in factors if f["polarity"] == "adverse"],
            "conflicts": conflicts, "auxiliary_and_scope_divergences": divergences,
            "uncertainties": unresolved, "semantic_context": before["semantic_context"],
            "semantic_source_references": before["semantic_source_references"],
            "rule_trace": before["rule_trace"], "condition_rule_trace": rules,
            "priority_source_context": catalog["priority_source"],
            "day5_comparison": before["traditional_tendency"],
            "question_used_for_calculation_or_judgement": False,
            "unimplemented": ["real_world_condition_satisfaction", "unreviewed_361_line_adjudications",
                              "unique_traditional_priority_resolution", "timing", "specialized_question_rules"],
            "ai_used": False, "history_written": False, "scores_or_probabilities_used": False}
        return ConditionalJudgementResult(canonical(result))
