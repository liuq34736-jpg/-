"""Bind explicitly reviewed definitions to existing signed Frames and exact evidence.

This is a local artifact build, not an automatic polarity classifier or a production
verification/signature issuer. All definitions are individually reviewed offline.
"""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.traditional_judgement_v1.trusted_input import digest


def build():
    audit = json.loads((ROOT / "docs/day6a_frame_audit.json").read_bytes())
    definitions = json.loads((ROOT / "data/day6a_condition_review_definitions.json").read_bytes())
    by_key = {(r["hexagram_id"], r["position"]): r for r in audit["rows"]}
    records = []
    for definition in definitions["records"]:
        row = by_key[(definition["hexagram_id"], definition["position"])]
        frame = row["frame"]
        refs = {s["evidence_id"]: s for s in row["source_references"]
                if s["evidence_id"] in frame["source_evidence_ids"]}
        assert refs and set(refs) == set(frame["source_evidence_ids"])
        for atom in definition["conditions"] + definition["branches"]:
            matches = [s for s in refs.values() if s["section_type"] == atom["field"] and atom["quote"] in s["text"]]
            if not matches:
                raise ValueError(f"review_quote_unbound:{definition['hexagram_id']}:{definition['position']}:{atom['id']}")
            atom["source_evidence_ids"] = [s["evidence_id"] for s in matches]
            atom["source_quotes"] = [{"evidence_id": s["evidence_id"], "quote": atom["quote"]} for s in matches]
            atom["basis"] = "SOURCE_BOUNDED_PROJECT_ENCODING"
        record = {**definition, "record_id": f"L{row['hexagram_id']:02d}-{row['position']}",
                  "hexagram_name": row["hexagram_name"], "line_name": row["line_name"],
                  "rule_version": definitions["version"], "frame_id": row["frame_id"],
                  "source_fingerprint": frame["source_fingerprint"],
                  "original_verification_record_id": frame["verification_record_id"],
                  "original_frame_snapshot": frame,
                  "source_requirements": [{"evidence_id": s["evidence_id"], "reference_sha256": digest(s),
                                            "reference": s} for s in refs.values()],
                  "review_status": definitions["review_status"],
                  "review_method": definitions["review_method"],
                  "condition_satisfaction": "not_assessed_from_question",
                  "production_approval": False,
                  "review_limits": ["仅供本次离线原型验收，不代表人工确认原文或重新批准 Frame。",
                                    "条件语义来自本条证据核对，不推广到未审核爻位。",
                                    "未使用新的古注、模型生成或现实事实推断。"]}
        record["review_receipt"] = {"version": "offline_condition_review_receipt_v1",
                                    "record_sha256": digest(record),
                                    "is_production_signature": False}
        records.append(record)
    import hashlib
    artifact = "docs/day6a_source_pages/page-57.png"
    catalog = {"version": definitions["version"], "policy_version": "traditional_condition_synthesis_v1",
               "review_status": definitions["review_status"], "production_approval": False,
               "frame_audit": {k: audit[k] for k in ("count", "signed_approved_frames", "nonempty_conditions", "nonempty_cautions", "core_claim_count")},
               "priority_source": {"source_id": "M1-PRIORITY-MODES", "title": "梅花易數",
                   "edition": "文明書局1925年本", "volume": "卷二", "section": "先天後天論",
                   "pdf_page": 57, "original_page": "三", "path": artifact,
                   "sha256": hashlib.sha256((ROOT / artifact).read_bytes()).hexdigest(),
                   "review_method": "direct_scan_visual_review", "status": "DISPUTED_PRIORITY_CONTEXT",
                   "excerpt": "先天卦斷吉凶止以卦論不甚用易之爻辭。後天則用爻辭兼用卦辭。",
                   "note": "短摘录作定位；横排句读不代替来源逐字全文，也不执行应期条文。"},
               "rules": [
                   {"rule_id":"TJ6-ELIGIBILITY","basis":"PROJECT_CONVENTION","summary":"只有固定审核目录、原 Frame 签名及对应证据仍有效的爻位可参与条件裁决。","dependencies":["TJ-SEMANTIC-BOUNDARY"]},
                   {"rule_id":"TJ6-CONDITION-UNKNOWN","basis":"PROJECT_CONVENTION","summary":"不从问题或卦象推定现实前提已满足，全部条件保持未评估。","dependencies":["TJ-SEMANTIC-BOUNDARY"]},
                   {"rule_id":"TJ6-LINE-SCOPE","basis":"PROJECT_CONVENTION","summary":"具体动作的利、免咎与行为提醒不能提升为整件事结果；保留原爻限制。","dependencies":["TJ-TRADITIONAL-ROLES","TJ-SEMANTIC-BOUNDARY"]},
                   {"rule_id":"TJ6-STRENGTH-QUALIFIER","basis":"PROJECT_CONVENTION","summary":"旺衰修饰原生克关系，不作为相反一票；克方衰不等于关系已消除。","dependencies":["TJ-STRENGTH","TJ-QUALIFIER"]},
                   {"rule_id":"TJ6-AUXILIARY-DIVERGENCE","basis":"PROJECT_CONVENTION","summary":"互中变终的不同阶段只作辅助分歧，不自动制造主要冲突。","dependencies":["TJ-AUXILIARY","TJ-TRADITIONAL-ROLES"]},
                   {"rule_id":"TJ6-PRIMARY-TENSION","basis":"PROJECT_CONVENTION","summary":"体用基础与已审核同范围动爻方向相反时保留条件性张力；不用评分选胜者。","dependencies":["TJ-PRIORITY","TJ-SEMANTIC-BOUNDARY"]},
                   {"rule_id":"TJ6-ALTERNATIVE-SCOPES","basis":"PROJECT_CONVENTION","summary":"不同条件分支未能选择时，不把它们当成同时成立的矛盾；总倾向保留不足。","dependencies":["TJ-SEMANTIC-BOUNDARY"]},
                   {"rule_id":"TJ6-PRIORITY-UNRESOLVED","basis":"DISPUTED","summary":"先看爻辞、先天后天区分与以体用为主不拘体用并存；本原型采用保守的并列约束而非宣称唯一传统优先级。","dependencies":["TJ-PRIORITY","TJ-TRADITIONAL-ROLES"]}
               ], "records": records}
    target = ROOT / "data/day6a_condition_reviews.json"
    target.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    return catalog


if __name__ == "__main__":
    value = build()
    print(json.dumps({"reviewed":len(value["records"]), "eligible":sum(r["eligible"] for r in value["records"]),
                      "catalog_sha256":digest(value)}, ensure_ascii=False))
