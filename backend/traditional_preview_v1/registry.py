"""Read-only registration of Day 6A/6B. Reuses their original binding checks.

No candidate file is read. A registry entry is not a production signature or
human verification. Every request checks pinned catalogs and current evidence.
"""

from backend.condition_review_tools_v1.pipeline import load_catalog, lookup_review
from backend.traditional_conditions_v1.catalog import ConditionReviewCatalog
from backend.traditional_judgement_v1.trusted_input import ValidatedJudgementInput

VERSION = "day6ab_readonly_registry_v1"


class FixedReviewRegistry:
    version = VERSION

    @staticmethod
    def load():
        prior = ConditionReviewCatalog.load()
        batch = load_catalog()
        old = prior.to_dict()["records"]
        old_keys = {(r["hexagram_id"], r["position"]) for r in old}
        new_keys = {tuple(r["target"]) for r in batch["records"]}
        if len(old_keys) != len(old) or len(new_keys) != len(batch["records"]) or old_keys & new_keys:
            raise ValueError("review_registration_invalid")
        return prior, batch, old_keys, new_keys

    @classmethod
    def coverage(cls):
        prior, batch, _, _ = cls.load()
        records = prior.to_dict()["records"] + batch["records"]
        return {"registered": len(records), "eligible": sum(r["eligible"] for r in records),
                "bounded": sum(r["eligible"] and r["effect"] != "alternative_scopes" for r in records),
                "branch_unresolved": sum(r["eligible"] and r["effect"] == "alternative_scopes" for r in records),
                "not_eligible": sum(not r["eligible"] for r in records), "unreviewed": 384 - len(records)}

    def lookup(self, request, before, book):
        if type(request) is not ValidatedJudgementInput:
            raise ValueError("guarded_input_required")
        prior, batch, old_keys, new_keys = self.load()
        calc = request.to_dict()["calculation"]
        key = (calc["original_hexagram"]["id"], calc["moving_line"]["position"])
        if key in old_keys:
            raw = next(r for r in prior.to_dict()["records"] if (r["hexagram_id"], r["position"]) == key)
            if not raw["eligible"]:
                return None, "not_eligible"
            record, reason = prior.lookup(request.to_dict(), before["key_moving_line"], book)
        elif key in new_keys:
            raw = next(r for r in batch["records"] if tuple(r["target"]) == key)
            if not raw["eligible"]:
                return None, "not_eligible"
            record, reason = lookup_review(request, book=book)
        else:
            return None, "unreviewed"
        # Detailed binding failures remain inside the server; never send raw errors.
        if record is None or reason is not None:
            return None, "evidence_unavailable"
        return record, "branch_unresolved" if record["effect"] == "alternative_scopes" else "bounded"
