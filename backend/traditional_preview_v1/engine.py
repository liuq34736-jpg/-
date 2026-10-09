"""Public projection of the Day 6A policy over fixed Day 6A/6B registrations.

This does not compute a hexagram or infer condition satisfaction. Explicitly
reviewed enums select the policy, never keywords in Chinese text. Existing
engines, Frames, review records and receipts remain unchanged.
"""

from backend.traditional_conditions_v1.catalog import ConditionReviewCatalog
from backend.traditional_judgement_v1.engine import TraditionalJudgementEngine
from backend.traditional_judgement_v1.rulebook import Rulebook
from backend.traditional_judgement_v1.trusted_input import ValidatedJudgementInput
from .models import JudgementView
from .registry import FixedReviewRegistry

VERSION = "traditional_judgement_web_preview_v1"
DISCLAIMER = "未确认现实前提已满足；以上是有范围限制的传统规则分析，不是事情必然成功或失败的预测。"
FALLBACK = "该爻的扩展综合判断尚未完成来源审核"
LABELS = {"favorable": "偏有利（有条件）", "adverse": "偏不利（有范围限制）", "mixed": "主要依据存在未决张力"}


def atom_view(atom):
    # Whitelist, not dict unpacking: excludes offsets, original Frame, receipt.
    return {"id": atom["id"], "kind": atom["kind"], "text": atom["text"],
            "source_evidence_ids": list(atom["source_evidence_ids"]),
            "source_quotes": [{"evidence_id": q["evidence_id"], "quote": q["quote"]} for q in atom["source_quotes"]],
            "satisfaction": "unknown"}


def factor_view(factor, scope):
    return {"id": factor["factor_id"], "text": factor["statement"], "layer": factor["layer"], "scope": scope,
            "rule_ids": list(factor["rule_ids"]), "condition_ids": list(factor.get("condition_ids", [])),
            "source_evidence_ids": list(factor.get("source_evidence_ids", []))}


def empty_view(status="evidence_unavailable"):
    unavailable = status == "evidence_unavailable"
    return {"preview_version": VERSION, "policy_version": "traditional_condition_synthesis_v1",
            "registry_version": FixedReviewRegistry.version, "review_status": status,
            "eligible_for_condition_review": False, "finite_synthesis_available": False,
            "direction": None, "label": "仅展示已验证结构",
            "summary": ("扩展判断依据暂不可用，本次未采用。" if unavailable else FALLBACK + "。") + DISCLAIMER,
            "scope": "structure_only", "body_use_baseline": None,
            "conditions": [], "branches": [], "branch_relationship": None, "scope_limits": [],
            "favorable_factors": [], "adverse_factors": [], "strength_modifiers": [], "auxiliary_analysis": [],
            "conflicts": [], "auxiliary_divergences": [],
            "uncertainties": [{"type": status, "text": "扩展判断未参与，保留原始卦象及可靠基础解释。", "rule_id": "TJ6-ELIGIBILITY"}],
            "rules": [], "rule_sources": [], "classical_sources": [], "review_provenance": None,
            "real_world_conditions": "unknown", "question_used_to_satisfy_conditions": False,
            "is_final_event_outcome": False, "ai_used": False, "history_written": False}


class PreviewJudgementEngine:
    def evaluate(self, request):
        if type(request) is not ValidatedJudgementInput:
            raise ValueError("guarded_input_required")
        request.to_dict()  # Reject forged seals before any fallback.
        try:
            return self._evaluate(request)
        except Exception:
            # Never return exception/review/cache paths, and never fabricate a verdict.
            return JudgementView.model_validate(empty_view())

    def _evaluate(self, request):
        book = Rulebook.load()
        before = TraditionalJudgementEngine(book).evaluate(request).to_dict()
        record, status = FixedReviewRegistry().lookup(request, before, book)
        calc = before["calculation"]
        base = before["traditional_tendency"]["baseline_tendency"]
        if base == "undetermined":
            return JudgementView.model_validate(empty_view())
        view = empty_view(status)
        reviewed = record is not None
        view["body_use_baseline"] = base
        view["eligible_for_condition_review"] = reviewed
        view["finite_synthesis_available"] = reviewed and status == "bounded"
        view["scope"] = ("bounded_reviewed_synthesis" if status == "bounded" else
                         "conditional_branches_only" if status == "branch_unresolved" else "structure_only")
        factors = []
        all_factors = before["favorable_factors"] + before["adverse_factors"]
        primary = next((f for f in all_factors if f["factor_id"] == "primary.body_use"), None)
        if primary:
            factors.append((primary["polarity"], factor_view(primary, "仅体用结构，不是整件事结果")))
        if reviewed:
            view["conditions"] = [atom_view(c) for c in record["conditions"]]
            view["branches"] = [{**atom_view(b), "direction": b["direction"], "condition_ids": list(b["condition_ids"])}
                                for b in record["branches"]]
            view["scope_limits"] = [atom_view(c) for c in record.get("scope_limits", [])]
            view["branch_relationship"] = record.get("branch_relationship", "alternative_not_simultaneous"
                if record["effect"] == "alternative_scopes" else "joint_source_constraints")
            view["review_provenance"] = {"rule_version": record["rule_version"],
                "review_scope": "offline_individual_condition_review", "human_verified": False, "is_production_signature": False}
            view["uncertainties"] = [{"type": "real_world_prerequisites_not_assessed",
                "text": "下列成立条件尚未在现实中核实；输入问题不会使条件自动成立。", "rule_id": "TJ6-CONDITION-UNKNOWN"},
                {"type": "traditional_priority_variants_retained", "text": "传统优先顺序存在不同解释，保留体用为主及爻辞为先的依据，未裁定唯一顺序。",
                 "rule_id": "TJ6-PRIORITY-UNRESOLVED"}]
            for branch in record["branches"]:
                if branch["direction"] in {"favorable", "adverse"}:
                    factors.append((branch["direction"], {"id": "line." + branch["id"], "text": branch["text"],
                        "layer": "reviewed_line", "scope": "仅具体行为" if record["effect"] == "bounded_opportunity" else "仅原文条件范围",
                        "rule_ids": ["TJ6-LINE-SCOPE", "TJ6-CONDITION-UNKNOWN"],
                        "condition_ids": list(branch["condition_ids"]), "source_evidence_ids": list(branch["source_evidence_ids"])}))
            if status == "branch_unresolved":
                view["label"] = "条件分支未决"
                view["summary"] = "原爻存在不同适用条件分支，现有输入不能选择分支；综合倾向暂不能确定。" + DISCLAIMER
                view["uncertainties"].append({"type": "alternative_conditions_not_selected", "text": "不同分支不代表同时成立；本次未自动选择任何分支。",
                                              "rule_id": "TJ6-ALTERNATIVE-SCOPES"})
            else:
                direction = base
                opposite = "adverse" if base == "favorable" else "favorable"
                if record["effect"] in {"adverse_warning", "conditional_support"} and any(b["direction"] == opposite for b in record["branches"]):
                    direction = "mixed"
                    view["conflicts"] = [{"type": "primary_conditional_tension", "rule_id": "TJ6-PRIMARY-TENSION",
                        "text": "体用基础与已审核动爻存在条件性张力；可分别按体用为主加爻辞限制，或按爻辞为先加体用背景理解。现实条件未核实，不评分、不选定胜者。"}]
                elif record["effect"] == "bounded_opportunity":
                    view["auxiliary_divergences"].append({"type": "different_scope_line_opportunity", "rule_id": "TJ6-LINE-SCOPE",
                        "text": "动爻中的具体行为机会不等于整件事方向；不据此翻转体用基础倾向。"})
                view["direction"], view["label"] = direction, LABELS[direction]
                # Review summary is an internal audit note (may mention Frames).
                # Public prose uses only reviewed branch text, with its conditions below.
                summary = "体用基础" + ("偏有利" if base == "favorable" else "偏不利") + "；动爻提示：" + "；".join(b["text"] for b in record["branches"]) + "。"
                if "strength.controlling_side_weak" in before["body_use_and_strength"]["qualifier_ids"]:
                    summary += "克体一方衰，其作用受限，但用克体仍在，不能当成不利已消除。"
                if view["conflicts"]:
                    summary += "主要依据存在条件性张力，暂不选定单一结果。"
                view["summary"] = summary + DISCLAIMER
        view["favorable_factors"] = [f for p, f in factors if p == "favorable"]
        view["adverse_factors"] = [f for p, f in factors if p == "adverse"]
        view["strength_modifiers"] = [factor_view(f, "修饰同一关系，不作相反一票") for f in all_factors if f["layer"] == "qualifier"]
        auxiliary_factors = [f for f in all_factors if f["layer"] == "auxiliary"]
        for aux in before["auxiliary_analysis"]:
            name = "mutual" if aux["role"] == "mutual_hexagram" else "changed"
            view["auxiliary_analysis"].append({"role": aux["role"], "name": aux["hexagram"]["full_name"],
                "items": [{k: item[k] for k in ("side", "trigram", "element", "state_label", "relation_to_original_body", "status")} for item in aux["items"]],
                "note": "仅作内部过程辅助；乾坤无互存在争议，保留计算互卦但相关生克不参与裁决。" if any(i["status"] == "reference_only" for i in aux["items"]) else
                        "仅作内部过程辅助，不代表结果。" if name == "mutual" else "仅作变化方向辅助，不代表必然未来；不重复计算未变化的体卦。"})
            directional = [f for f in auxiliary_factors if f["factor_id"].startswith(name + ".")
                           and not f["factor_id"].endswith((".weak_controller", ".weak_support"))]
            if any(f["polarity"] != base for f in directional):
                view["auxiliary_divergences"].append({"type": "auxiliary_phase_divergence", "rule_id": "TJ6-AUXILIARY-DIVERGENCE",
                    "text": ("互卦" if name == "mutual" else "变卦") + "辅助关系与体用基础方向不同，属于阶段线索，不单独改判混合。"})
        phase_directions = {name: {f["polarity"] for f in auxiliary_factors if f["factor_id"].startswith(name + ".")
            and not f["factor_id"].endswith((".weak_controller", ".weak_support"))} for name in ("mutual", "changed")}
        if phase_directions["mutual"] and phase_directions["changed"] and phase_directions["mutual"] != phase_directions["changed"]:
            view["auxiliary_divergences"].append({"type": "between_auxiliary_phases", "rule_id": "TJ6-AUXILIARY-DIVERGENCE",
                "text": "互卦与变卦的阶段方向不同，不把两个阶段当作同时成立的主要冲突。"})
        if calc["original_hexagram"]["id"] in {1, 2}:
            view["uncertainties"].append({"type": "qian_kun_mutual_conflict_unresolved", "rule_id": "TJ-QIAN-KUN",
                "text": "原典有乾坤无互的不同规则；冻结算法仍统一计算互卦。此处保留争议，互卦生克仅供参校。"})
        used_rules = list(before["rule_trace"])
        if calc["original_hexagram"]["id"] in {1, 2}:
            r = book.rule("TJ-QIAN-KUN")
            used_rules.append({"rule_id": "TJ-QIAN-KUN", "basis": r["basis"], "summary": r["summary"],
                               "sources": book.references("TJ-QIAN-KUN")})
        prior = ConditionReviewCatalog.load()
        if reviewed:
            for r in prior.to_dict()["rules"]:
                used_rules.append({"rule_id": r["rule_id"], "basis": r["basis"], "summary": r["summary"],
                    "sources": [s for dep in r["dependencies"] for s in book.references(dep)]})
        source_map = {}
        for rule in used_rules:
            view["rules"].append({"rule_id": rule["rule_id"], "basis": rule["basis"], "summary": rule["summary"],
                                  "source_ids": sorted({s["id"] for s in rule["sources"]})})
            for s in rule["sources"]:
                # Source integrity already checked by rulebook; no artifact path/sha is sent.
                if s["id"] not in book.unavailable_sources:
                    source_map[s["id"]] = {"source_id": s["id"], "title": s["title"], "edition": s["edition"], "volume": s["volume"],
                        "location": s["chapter"], "pdf_pages": list(s["pdf_pages"]), "printed_pages": list(s["printed_pages"]),
                        "url": s["catalog_url"], "excerpt": s["excerpt"], "limits": s["limits"], "review_method": s["review_method"]}
        if reviewed:
            s = prior.to_dict()["priority_source"]
            source_map[s["source_id"]] = {"source_id": s["source_id"], "title": s["title"], "edition": s["edition"], "volume": s["volume"],
                "location": s["section"], "pdf_pages": [s["pdf_page"]], "printed_pages": [s["original_page"]],
                "url": book.to_dict()["edition"]["catalog_url"], "excerpt": s["excerpt"], "limits": s["note"], "review_method": s["review_method"]}
            next(r for r in view["rules"] if r["rule_id"] == "TJ6-PRIORITY-UNRESOLVED")["source_ids"].append(s["source_id"])
        view["rule_sources"] = list(source_map.values())
        view["classical_sources"] = before["semantic_source_references"]
        return JudgementView.model_validate(view)
