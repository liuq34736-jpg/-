"""Deterministic offline synthesis. No AI, scoring, storage, web route or divination."""

from dataclasses import dataclass, field
import json

from .rulebook import Rulebook
from .trusted_input import ValidatedJudgementInput, JudgementUnavailable, canonical, digest, ROLES

VERSION = "traditional_judgement_v1"
RELATION_RULE = {
    "yong_generates_body": "TJ-REL-YGB", "body_generates_yong": "TJ-REL-BGY",
    "body_controls_yong": "TJ-REL-BCY", "yong_controls_body": "TJ-REL-YCB",
    "same_element": "TJ-REL-SAME",
}
ROLE_FUNCTION = {
    "original_hexagram": "current_state", "moving_line": "primary_change",
    "mutual_hexagram": "internal_process", "changed_hexagram": "change_direction",
}
QUALIFIERS = {
    "body_wang": ("favorable", "体方处于旺势，是主体时令方面的有利条件；不单独推出事情结果。"),
    "body_shuai": ("adverse", "体方处于衰势，是主体时令方面的不利条件。"),
    "controlling_side_weak": ("favorable", "克体一方处于衰势，克制作用受到其自身时令状态限制；基础用克体关系仍保留。"),
    "weak_body_under_control": ("adverse", "体衰同时受克，传统规则要求加强谨慎；未据此断言现实事件发生。"),
    "supporting_side_wang": ("favorable", "生体一方处于旺势，生助具备较有利的时令条件。"),
    "supporting_side_weak": ("adverse", "生体一方处于衰势，生助条件受限；并不自动取消生助关系。"),
    "weak_body_receives_support": ("favorable", "体衰而得生，原书称衰可稍解；不解释为已经恢复或保证无事。"),
    "weak_subject_control_limited": ("adverse", "体方处于衰势，体克用的制约能力需作受限理解；不把关系翻转。"),
    "weak_subject_outflow": ("adverse", "体衰同时体生用，保留主体向外耗用的提醒；不将耗用推定为金钱损失。"),
}


@dataclass(frozen=True)
class JudgementResult:
    payload_json: str = field(repr=False)

    def to_dict(self):
        return json.loads(self.payload_json)


class TraditionalJudgementEngine:
    version = VERSION

    def __init__(self, rulebook=None):
        self.book = rulebook or Rulebook.load()
        if type(self.book) is not Rulebook:
            raise ValueError("untrusted_rulebook")

    def evaluate(self, request: ValidatedJudgementInput):
        if type(request) is not ValidatedJudgementInput:
            raise JudgementUnavailable()
        payload = request.to_dict()
        calc = payload["calculation"]
        book = self.book
        factors, trace, uncertainties, excluded, semantic = [], [], [], list(payload["excluded_evidence"]), []

        def apply_rule(rule_id):
            if not book.available(rule_id):
                entry = {"reason": "rule_source_unavailable", "rule_id": rule_id}
                if entry not in uncertainties:
                    uncertainties.append(entry)
                return False
            if rule_id not in {r["rule_id"] for r in trace}:
                rule = book.rule(rule_id)
                trace.append({"rule_id": rule_id, "basis": rule["basis"], "summary": rule["summary"],
                              "sources": book.references(rule_id)})
            return True

        def add_factor(factor_id, polarity, statement, rule_ids, input_evidence, layer="primary"):
            # Missing source support cannot be laundered through an available project rule.
            allowed = [apply_rule(rule) for rule in rule_ids]
            if not all(allowed):
                return
            factors.append({"factor_id": factor_id, "polarity": polarity, "statement": statement,
                            "layer": layer, "rule_ids": rule_ids, "input_evidence": input_evidence})

        body, strength = calc["body_use"], calc["strength"]
        relation = body["relation"]
        rule_id = RELATION_RULE[relation]
        rule = book.rule(rule_id)
        add_factor("primary.body_use", rule["polarity"], rule["summary"], [rule_id, "TJ-DISPLAY"],
                   {"body_use": body, "rule_version": body["rule_version"]})
        baseline = rule["polarity"] if any(f["factor_id"] == "primary.body_use" for f in factors) else "undetermined"

        qualifiers = []
        bs, ys = strength["body"]["state"], strength["yong"]["state"]
        if bs in {"wang", "shuai"}:
            qualifiers.append("body_" + bs)
        if relation == "yong_controls_body":
            if ys == "shuai":
                qualifiers.append("controlling_side_weak")
            if bs == "shuai":
                qualifiers.append("weak_body_under_control")
        elif relation == "yong_generates_body":
            if ys == "wang":
                qualifiers.append("supporting_side_wang")
            elif ys == "shuai":
                qualifiers.append("supporting_side_weak")
            if bs == "shuai":
                qualifiers.append("weak_body_receives_support")
        elif relation == "body_controls_yong" and bs == "shuai":
            qualifiers.append("weak_subject_control_limited")
        elif relation == "body_generates_yong" and bs == "shuai":
            qualifiers.append("weak_subject_outflow")
        for qualifier in qualifiers:
            polarity, statement = QUALIFIERS[qualifier]
            add_factor("strength." + qualifier, polarity, statement, ["TJ-STRENGTH", "TJ-QUALIFIER"],
                       {"strength_rule_version": strength["rule_version"],
                        "month_branch": strength["solar_term_month_branch"],
                        "body": strength["body"], "yong": strength["yong"]}, "qualifier")

        # Atom-level approval and evidence stay intact. No substring sentiment classifier.
        for role in ROLES:
            item = payload["frames"][role]
            missing_reason = "approved_frame_unavailable"
            if item is not None:
                try:
                    frame = item["frame"]
                    hid = calc["original_hexagram" if role == "moving_line" else role]["id"]
                    pos = calc["moving_line"]["position"] if role == "moving_line" else None
                    available_ids = {s["evidence_id"] for s in calc["source_references"]
                                     if s["role"] == role and s["verification_status"] in {"verified", "machine_verified"}}
                    if (item["frame_id"] != digest(frame) or item["hexagram_id"] != hid or item["yao_position"] != pos
                            or frame["semantic_status"] != "SEMANTIC_APPROVED" or frame["target_role"] != role
                            or frame["version"] != "verified_semantic_frame_v1"
                            or not frame["source_evidence_ids"] or not set(frame["source_evidence_ids"]) <= available_ids):
                        raise ValueError("invalid_frame_binding")
                    for field_name in ("core_claims", "conditions", "cautions"):
                        for claim in frame[field_name]:
                            if (not claim["supported_by"] or not set(claim["supported_by"]) <= set(frame["source_evidence_ids"])
                                    or type(claim["text"]) is not str or not claim["text"].strip()):
                                raise ValueError("invalid_claim_evidence")
                    if not frame["core_claims"]:
                        raise ValueError("empty_core")
                    if (not apply_rule("TJ-SEMANTIC-BOUNDARY") or not apply_rule("TJ-ROLE-CONTEXT")
                            or not apply_rule("TJ-TRADITIONAL-ROLES")):
                        raise ValueError("semantic_rule_unavailable")
                    semantic.append({"role": role, "function": ROLE_FUNCTION[role], "status": "approved_context",
                        "frame_id": item["frame_id"], "source_fingerprint": frame["source_fingerprint"],
                        "verification_record_id": frame["verification_record_id"],
                        "core_claims": frame["core_claims"], "conditions": frame["conditions"], "cautions": frame["cautions"],
                        "source_evidence_ids": frame["source_evidence_ids"], "source_layer": "APPROVED_SEMANTIC_FRAME",
                        "role_limit": ("只作内部过程的辅助线索。" if role == "mutual_hexagram" else
                                       "只作变化方向，不代表事情必然发生。" if role == "changed_hexagram" else
                                       "用于所问事情的阅读条件，不推定用户未提供的现实事实。"),
                        "rule_ids": ["TJ-TRADITIONAL-ROLES", "TJ-ROLE-CONTEXT", "TJ-SEMANTIC-BOUNDARY"]})
                    continue
                except (KeyError, TypeError, ValueError):
                    missing_reason = "unreliable_frame_or_evidence_excluded"
            semantic.append({"role": role, "function": ROLE_FUNCTION[role], "status": "structure_fallback",
                             "core_claims": [], "conditions": [], "cautions": [], "source_evidence_ids": []})
            uncertainties.append({"role": role, "reason": missing_reason})
            excluded.append({"role": role, "reason": missing_reason})

        # No new body/use assignment: the frozen body remains the comparison subject.
        auxiliary = []
        for name, role in (("mutual", "mutual_hexagram"), ("changed", "changed_hexagram")):
            aux = {"role": role, "hexagram": calc[role], "weight": "auxiliary", "items": []}
            qian_kun_disputed = name == "mutual" and calc["original_hexagram"]["id"] in {1, 2}
            seen = set()
            for side in ("lower", "upper"):
                state = strength[name][side]
                rel = payload["auxiliary_relations"][name][side]
                entry = {"side": side, **state, "relation_to_original_body": rel}
                if qian_kun_disputed:
                    entry.update(status="reference_only", reason="qian_kun_mutual_conflict", rule_id="TJ-QIAN-KUN")
                elif name == "changed" and state["trigram"] == body["body_trigram"] and side == (
                        "upper" if calc["moving_line"]["position"] <= 3 else "lower"):
                    entry.update(status="context_only", reason="unchanged_body_not_independent_evidence")
                elif state["trigram"] in seen:
                    entry.update(status="context_only", reason="duplicate_auxiliary_trigram")
                else:
                    entry.update(status="auxiliary_factor")
                    auxiliary_rule = RELATION_RULE[rel]
                    desc = book.rule(auxiliary_rule)
                    add_factor(f"{name}.{side}", desc["polarity"], "辅助关系：" + desc["summary"],
                        ["TJ-AUXILIARY", auxiliary_rule, "TJ-DISPLAY"],
                        {"original_body_element": body["body_element"], "auxiliary": state, "relation": rel}, "auxiliary")
                    # Strength does not turn a weak controller into support or cancel a base relation.
                    if rel == "yong_controls_body" and state["state"] == "shuai":
                        add_factor(f"{name}.{side}.weak_controller", "favorable", "辅助克体一方处于衰势，作用受限，克制关系仍保留。",
                            ["TJ-AUXILIARY", "TJ-STRENGTH", "TJ-QUALIFIER"],
                            {"auxiliary": state, "relation": rel}, "auxiliary")
                    if rel == "yong_generates_body" and state["state"] == "shuai":
                        add_factor(f"{name}.{side}.weak_support", "adverse", "辅助生体一方处于衰势，生助条件受限。",
                            ["TJ-AUXILIARY", "TJ-STRENGTH", "TJ-QUALIFIER"],
                            {"auxiliary": state, "relation": rel}, "auxiliary")
                seen.add(state["trigram"])
                aux["items"].append(entry)
            auxiliary.append(aux)
            if qian_kun_disputed:
                uncertainties.append({"reason": "qian_kun_mutual_conflict_unresolved", "rule_id": "TJ-QIAN-KUN",
                                      "computed_mutual_retained": True, "source_references": book.references("TJ-QIAN-KUN")})

        apply_rule("TJ-PRIORITY")
        favorable = [f for f in factors if f["polarity"] == "favorable"]
        adverse = [f for f in factors if f["polarity"] == "adverse"]
        conflicts = []
        if favorable and adverse:
            # Directional conflict deliberately cannot be resolved by factor counts.
            apply_rule("TJ-CONFLICT")
            conflicts.append({"type": "opposing_factors", "resolution": "unresolved_no_scoring",
                "favorable_factor_ids": [f["factor_id"] for f in favorable],
                "adverse_factor_ids": [f["factor_id"] for f in adverse], "rule_id": "TJ-CONFLICT"})
        uncertainties.append({"reason": "moving_line_polarity_and_conditions_not_structurally_adjudicated",
                              "rule_id": "TJ-PENDING-LINE-POLARITY"})
        if book.unavailable_sources:
            uncertainties.append({"reason": "unavailable_rule_sources", "sources": list(book.unavailable_sources)})
        # Even favorable auxiliary factors cannot create an overall judgment without a supported base rule.
        tendency = ("undetermined" if baseline == "undetermined" else "mixed" if conflicts else baseline)
        labels = {"favorable": "传统结构偏有利", "adverse": "传统结构偏不利",
                  "mixed": "有利与不利条件并存", "undetermined": "可靠规则依据不足，无法形成传统倾向"}
        status = "limited_rule_synthesis" if baseline != "undetermined" else "insufficient_rule_support"
        summary = "就体用、时令和辅助生克层而言，" + labels[tendency] + "。"
        if baseline != "undetermined":
            summary += "本卦体用的基础倾向为" + ("有利" if baseline == "favorable" else "不利") + "，需连同动爻条件与时令限制阅读。"
        summary += "动爻爻义尚未参与定向裁决，因此这不是全卦最终结论。当前原型保留冲突，不裁定现实成败。"
        used_ids = {eid for item in semantic for eid in item["source_evidence_ids"]}
        result = {
            "engine_version": VERSION, "prototype_status": "offline_pending_acceptance", "status": status,
            "input_fingerprint": digest(payload), "calculation_fingerprint": digest(calc),
            "calculation": calc, "question_used_for_calculation_or_judgement": False,
            "traditional_tendency": {"baseline_relation": relation, "baseline_tendency": baseline,
                                     "combined_tendency": tendency, "label": labels[tendency], "summary": summary,
                                     "scope": "body_use_strength_auxiliary_only", "semantic_polarity_included": False,
                                     "is_final_outcome": False},
            "body_use_and_strength": {"body_use": body, "strength": strength,
                "qualifier_ids": [f["factor_id"] for f in factors if f["layer"] == "qualifier"],
                "strength_does_not_change_relation": True},
            "key_moving_line": next(item for item in semantic if item["role"] == "moving_line"),
            "semantic_context": semantic, "auxiliary_analysis": auxiliary,
            "favorable_factors": favorable, "adverse_factors": adverse,
            "conflicts": conflicts, "uncertainties": uncertainties, "excluded_evidence": excluded,
            "rule_trace": trace,
            "semantic_source_references": [r for r in calc["source_references"] if r["evidence_id"] in used_ids],
            "unimplemented": ["conditional_line_polarity_adjudication", "specialized_question_rules", "external_omens", "timing"],
            "ai_used": False, "history_written": False, "scores_or_probabilities_used": False,
        }
        return JudgementResult(canonical(result))
