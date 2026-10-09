"""Only fixed frozen imports. The Day 4 audit guard blocks writes, SQLite and HTTP."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend.app.meihua_worker import FrozenRuntime


def collect(runtime, data):
    from iching.analysis.five_elements import relation_between
    from backend.traditional_judgement_v1.trusted_input import digest

    calculation = runtime.calculate(data)
    oid = calculation["original_hexagram"]["id"]
    objects = [("original_hexagram", "current_state", oid, None),
        ("moving_line", "primary_change", oid, calculation["moving_line"]["position"]),
        ("mutual_hexagram", "internal_process", calculation["mutual_hexagram"]["id"], None),
        ("changed_hexagram", "change_direction", calculation["changed_hexagram"]["id"], None)]
    frames, excluded = {}, []
    for role, internal, hid, pos in objects:
        frames[role] = None
        try:
            bundle = runtime.corpus.bundle(hid, pos, internal) if runtime.corpus is not None else None
            proof = runtime.proof(bundle) if bundle else None
            record = runtime.frame(bundle, proof) if proof else None
            if not record:
                raise ValueError("unavailable_frame")
            # Re-use the original proof/signature validation, never create a disk receipt.
            frame = runtime.issue_frame(record["frame"], bundle, proof).to_dict()
            if frame["target_role"] != role:
                raise ValueError("frame_role_changed")
            references = [r for r in calculation["source_references"] if r["role"] == role]
            available = {r["evidence_id"] for r in references if r["verification_status"] in {"verified", "machine_verified"}}
            if not set(frame["source_evidence_ids"]) <= available:
                raise ValueError("missing_frame_sources")
            frames[role] = {"frame_id": digest(frame), "hexagram_id": hid, "yao_position": pos, "frame": frame}
        except (ValueError, OSError, TypeError, KeyError):
            excluded.append({"role": role, "reason": "approved_frame_or_reliable_evidence_unavailable"})
    auxiliary = {}
    for role in ("mutual", "changed"):
        auxiliary[role] = {side: relation_between(calculation["body_use"]["body_element"], item["element"])
                           for side, item in calculation["strength"][role].items()}
    return {"calculation": calculation, "frames": frames, "auxiliary_relations": auxiliary, "excluded_evidence": excluded}


def main():
    try:
        raw = sys.stdin.buffer.read(64_001)
        if len(raw) > 64_000:
            raise ValueError("request_limit")
        requests = json.loads(raw)
        if type(requests) is not list or not 1 <= len(requests) <= 96:
            raise ValueError("request_limit")
        runtime = FrozenRuntime()
        result = [collect(runtime, request) for request in requests]
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
        return 0
    except Exception:
        # Never print traceback, question contents, secret material or provider exceptions.
        print('{"error":"offline_judgement_unavailable"}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
