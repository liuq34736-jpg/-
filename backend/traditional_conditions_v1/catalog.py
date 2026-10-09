"""Pinned, per-line source-bound review layer, independent of frozen Frames."""

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path

from backend.traditional_judgement_v1.trusted_input import canonical, digest

ROOT = Path(__file__).resolve().parents[2]
CATALOG_SHA256 = "328dfe9a943c5e4fd9ea69ab9329edbb3ebb7bfc9e8d4f9a3e2f305d29800566"
_ISSUER = object()


@dataclass(frozen=True)
class ConditionReviewCatalog:
    _json: str = field(repr=False)
    excluded_records: tuple[str, ...]
    priority_source_available: bool
    _issuer: object = field(repr=False, compare=False)

    @classmethod
    def load(cls, *, excluded_records=()):
        value = json.loads((ROOT / "data/day6a_condition_reviews.json").read_bytes())
        if digest(value) != CATALOG_SHA256:
            raise ValueError("condition_review_catalog_changed")
        ids = {r["record_id"] for r in value["records"]}
        if type(excluded_records) is not tuple or not set(excluded_records) <= ids:
            raise ValueError("invalid_condition_review_restriction")
        source = value["priority_source"]
        path = (ROOT / source["path"]).resolve()
        if path != (ROOT / "docs/day6a_source_pages/page-57.png").resolve():
            raise ValueError("invalid_priority_source")
        available = path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]
        return cls(canonical(value), excluded_records, available, _ISSUER)

    def to_dict(self):
        if self._issuer is not _ISSUER:
            raise ValueError("untrusted_condition_catalog")
        value = json.loads(self._json)
        if digest(value) != CATALOG_SHA256:
            raise ValueError("untrusted_condition_catalog")
        return value

    def lookup(self, payload, validated_line, book):
        value = self.to_dict()
        calc = payload["calculation"]
        key = (calc["original_hexagram"]["id"], calc["moving_line"]["position"])
        record = next((r for r in value["records"] if (r["hexagram_id"], r["position"]) == key), None)
        if record is None:
            return None, "line_not_individually_reviewed"
        if record["record_id"] in self.excluded_records:
            return None, "line_review_explicitly_excluded"
        if not record["eligible"]:
            return None, record["unresolved_reason"]
        if not self.priority_source_available or any(not book.available(dep)
                for rule in value["rules"] for dep in rule["dependencies"]):
            return None, "condition_rule_source_unavailable"
        if validated_line["status"] != "approved_context":
            return None, "signed_line_frame_unavailable"
        item = payload["frames"]["moving_line"]
        frame = item["frame"]
        if (item["frame_id"] != record["frame_id"] or digest(frame) != record["frame_id"]
                or frame != record["original_frame_snapshot"]
                or validated_line["frame_id"] != record["frame_id"]
                or frame["source_fingerprint"] != record["source_fingerprint"]
                or frame["verification_record_id"] != record["original_verification_record_id"]):
            return None, "review_binding_to_original_frame_changed"
        refs = {s["evidence_id"]: s for s in calc["source_references"] if s["role"] == "moving_line"}
        for source in record["source_requirements"]:
            ref = refs.get(source["evidence_id"])
            if (not ref or ref["verification_status"] not in {"verified", "machine_verified"}
                    or digest(ref) != source["reference_sha256"]):
                return None, "review_source_evidence_changed_or_missing"
        for atom in record["conditions"] + record["branches"]:
            if not atom["source_evidence_ids"] or not atom["source_quotes"]:
                return None, "review_atom_evidence_missing"
            for quote in atom["source_quotes"]:
                ref = refs.get(quote["evidence_id"])
                if (not ref or quote["evidence_id"] not in frame["source_evidence_ids"]
                        or quote["quote"] not in ref["text"] or ref["section_type"] != atom["field"]):
                    return None, "review_quote_not_supported"
        receipt = record["review_receipt"]
        if receipt["record_sha256"] != digest({k: v for k, v in record.items() if k != "review_receipt"}):
            return None, "review_receipt_changed"
        return record, None
