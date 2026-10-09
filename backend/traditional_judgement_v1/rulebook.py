"""Pinned source review; damaged/unavailable source images cannot support a rule."""

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULEBOOK_SHA256 = "c50d9c4d61e8e519f8599ca14638623b42ac8cd2ea6d4920b7e6481b829288ba"
_ISSUER = object()


@dataclass(frozen=True)
class Rulebook:
    _json: str = field(repr=False)
    unavailable_sources: tuple[str, ...]
    _issuer: object = field(repr=False, compare=False)

    @classmethod
    def load(cls, *, excluded_sources=()):
        raw = (ROOT / "data/day5_judgement_rulebook.json").read_bytes()
        if hashlib.sha256(raw).hexdigest() != RULEBOOK_SHA256:
            raise ValueError("rulebook_changed")
        book = json.loads(raw)
        source_ids = {s["id"] for s in book["sources"]}
        if type(excluded_sources) is not tuple or not set(excluded_sources) <= source_ids:
            raise ValueError("invalid_source_restriction")
        unavailable = set(excluded_sources)
        for source in book["sources"]:
            for artifact in source["page_artifacts"]:
                path = (ROOT / artifact["path"]).resolve()
                if not path.is_relative_to(ROOT / "docs/day5_source_pages"):
                    raise ValueError("invalid_source_artifact")
                if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != artifact["sha256"]:
                    unavailable.add(source["id"])
        return cls(raw.decode("utf-8"), tuple(sorted(unavailable)), _ISSUER)

    def to_dict(self):
        if self._issuer is not _ISSUER or hashlib.sha256(self._json.encode("utf-8")).hexdigest() != RULEBOOK_SHA256:
            raise ValueError("untrusted_rulebook")
        return json.loads(self._json)

    def rule(self, rule_id):
        return next(r for r in self.to_dict()["rules"] if r["id"] == rule_id)

    def available(self, rule_id):
        rule = self.rule(rule_id)
        return rule["status"] == "EXECUTABLE" and not set(rule["sources"]) & set(self.unavailable_sources)

    def references(self, rule_id):
        value = self.to_dict()
        ids = self.rule(rule_id)["sources"]
        return [{**source, "title": value["edition"]["title"], "edition": "文明書局1925年本",
                 "catalog_url": value["edition"]["catalog_url"],
                 "review_method": value["edition"]["review_method"]}
                for source in value["sources"] if source["id"] in ids]
