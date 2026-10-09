"""Revalidate all original signatures in an isolated, read-only worker.

Writes new Day 6B artifacts only. It never changes states or issues production proofs.
"""

import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def worker():
    from scripts.day6a_frame_audit import worker as audit_worker
    from backend.app.meihua_worker import FrozenRuntime
    from backend.traditional_judgement_v1.trusted_input import digest
    audit = audit_worker()  # Original issuer verifies signature and evidence for every line.
    runtime = FrozenRuntime()
    old = json.loads((ROOT / "docs/day6a_frame_audit.json").read_bytes())
    if audit != old:
        raise ValueError("day6a_signed_frame_inventory_changed")
    for row in audit["rows"]:
        bundle = runtime.corpus.bundle(row["hexagram_id"], row["position"], "primary_change")
        metadata = {}
        for evidence in bundle["evidence"]:
            if evidence["evidence_id"] not in row["frame"]["source_evidence_ids"]:
                continue
            source_row = runtime.corpus.by_key[(row["hexagram_id"], row["position"], evidence["field"])]
            witness = next(w for w in source_row["source_witnesses"] if w["source_id"] == evidence["source_id"])
            metadata[evidence["evidence_id"]] = {
                "source_id": evidence["source_id"], "source_title": evidence["source_title"],
                "edition": evidence["edition"], "canonical_url": witness["canonical_url"],
                "volume": witness["volume"], "content_location": witness["content_location"],
                "textual_variants": source_row["textual_variants"],
                "original_pages": None,
            }
        row["source_metadata"] = metadata
        row["signature_check"] = "original_production_issuer_passed_read_only"
    return {**audit, "audit_version": "day6b_signed_frame_inventory_v1",
            "day6a_inventory_matches": True, "original_inventory_sha256": digest(old),
            "production_signature_issued": False}


def main():
    if sys.argv[1:] == ["--worker"]:
        try:
            print(json.dumps(worker(), ensure_ascii=True))
            return 0
        except Exception:
            print('{"failed":1,"reason":"signed_inventory_unavailable"}')
            return 1
    environment = {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP"}}
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    run = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(Path(__file__).resolve()), "--worker"],
                         cwd=ROOT, env=environment, capture_output=True, timeout=300, **options)
    if run.returncode:
        print("signed_inventory_unavailable")
        return 1
    inventory = json.loads(run.stdout)
    if inventory["count"] != 384 or inventory["signed_approved_frames"] != 384:
        raise ValueError("incomplete_inventory")
    from backend.condition_review_tools_v1.pipeline import make_proposal, inspect_proposal
    old_reviews = json.loads((ROOT / "data/day6a_condition_reviews.json").read_bytes())
    prior = {(r["hexagram_id"], r["position"]) for r in old_reviews["records"]}
    rows = []
    for row in inventory["rows"]:
        proposal = make_proposal(row)
        rows.append({**proposal, "hexagram": row["hexagram_name"], "line": row["line_name"],
                     "prior_review_preserved": (row["hexagram_id"], row["position"]) in prior,
                     "inspection": inspect_proposal(proposal, row)})
    (ROOT / "docs/day6b_signed_frame_inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "data/day6b_condition_candidates.json").write_text(json.dumps({
        "version": "condition_review_tools_v1", "status": "candidate", "rows": rows,
        "automatic_promotions": 0, "production_approval": False}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"signed_lines": inventory["count"], "candidate_atoms": sum(len(r["candidates"]) for r in rows),
                      "prior_reviews_preserved": len(prior), "automatic_promotions": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
