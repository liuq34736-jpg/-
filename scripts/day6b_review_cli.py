"""Fixed local worksheet exports; no promotion command, arbitrary paths or model input."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.condition_review_tools_v1.pipeline import load_catalog, make_proposal
from backend.traditional_judgement_v1.trusted_input import digest


def inventory():
    catalog = load_catalog()
    value = json.loads((ROOT / "docs/day6b_signed_frame_inventory.json").read_bytes())
    if digest(value) != catalog["signed_inventory_sha256"]:
        raise ValueError("signed_inventory_changed")
    return value


def review_table():
    prior = json.loads((ROOT / "data/day6a_condition_reviews.json").read_bytes())
    old = {(r["hexagram_id"], r["position"]): r for r in prior["records"]}
    new = {tuple(r["target"]): r for r in load_catalog()["records"]}
    rows = []
    for item in inventory()["rows"]:
        key = (item["hexagram_id"], item["position"])
        if key in new:
            record = new[key]
            state, eligible, phase = record["state"], record["eligible"], "day6b"
            reason, rid = record["failure_reason"], record["record_id"]
        elif key in old:
            record = old[key]
            eligible, phase = record["eligible"], "day6a_preserved"
            state = "reviewed" if eligible else "insufficient_evidence"
            reason, rid = record.get("unresolved_reason"), record["record_id"]
        else:
            state, eligible, phase, reason, rid = "candidate", False, "unreviewed", "not_individually_reviewed", None
        rows.append({"target": list(key), "hexagram": item["hexagram_name"], "line": item["line_name"],
                     "state": state, "eligible": eligible, "review_phase": phase,
                     "record_id": rid, "reason": reason, "production_approval": False})
    return {"version": "condition_review_table_v1", "rows": rows,
            "state_counts": dict(Counter(r["state"] for r in rows)), "web_enabled": False}


def parse_targets(values):
    if not 1 <= len(values) <= 48:
        raise ValueError("worksheet_size_1_to_48_required")
    targets = []
    for value in values:
        parts = value.split(":")
        if len(parts) != 2 or not all(p.isascii() and p.isdigit() for p in parts):
            raise ValueError("target_must_be_hexagram_id_and_position")
        hid, pos = map(int, parts)
        if not 1 <= hid <= 64 or not 1 <= pos <= 6:
            raise ValueError("target_out_of_range")
        if (hid, pos) in targets:
            raise ValueError("duplicate_target")
        targets.append((hid, pos))
    return targets


def worksheet(values):
    targets = parse_targets(values)
    table = {tuple(r["target"]): r for r in review_table()["rows"]}
    if any(table[k]["review_phase"] != "unreviewed" for k in targets):
        raise ValueError("existing_review_replacement_forbidden")
    by_key = {(r["hexagram_id"], r["position"]): r for r in inventory()["rows"]}
    return {"version": "condition_review_worksheet_v1", "status": "candidate",
            "rows": [{**make_proposal(by_key[k]), "review_notes": "", "review_findings": [],
                      "state": "candidate", "eligible": False} for k in targets],
            "production_approval": False, "promotion_supported": False}


def main():
    parser = argparse.ArgumentParser(description="离线条件审核清单；不会自动批准候选。")
    parser.add_argument("mode", choices=("table", "worksheet"))
    parser.add_argument("--targets", nargs="*", default=[])
    args = parser.parse_args()
    try:
        if args.mode == "table":
            value, output = review_table(), "docs/day6b_review_table.json"
        else:
            value, output = worksheet(args.targets), "docs/day6b_review_worksheet.json"
        (ROOT / output).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"output": output, "rows": len(value["rows"]), "automatic_promotions": 0}, ensure_ascii=False))
        return 0
    except ValueError as exc:
        # Fixed validation messages contain no user text or secrets.
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
