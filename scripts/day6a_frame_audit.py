"""Read all 384 signed moving-line Frames using the unchanged guarded bridge."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def worker():
    from backend.app.meihua_worker import FrozenRuntime
    from backend.traditional_judgement_v1.trusted_input import digest
    runtime = FrozenRuntime()
    rows = []
    for profile in runtime.profiles:
        hid = profile["id"]
        for pos in range(1, 7):
            bundle = runtime.corpus.bundle(hid, pos, "primary_change")
            proof = runtime.proof(bundle)
            record = runtime.frame(bundle, proof)
            frame = runtime.issue_frame(record["frame"], bundle, proof).to_dict()
            _, references = runtime.meanings(
                [("moving_line", "primary_change", hid, pos)],
                [{"type": "primary_change", "statement": "仅保留结构。"}],
            )
            rows.append({"hexagram_id": hid, "hexagram_name": profile["name"],
                         "position": pos, "line_name": runtime.line_name(profile["lines"], pos),
                         "frame_id": digest(frame), "frame": frame, "source_references": references})
    return {"audit_version": "day6a_frame_audit_v1", "count": len(rows),
            "signed_approved_frames": sum(r["frame"]["semantic_status"] == "SEMANTIC_APPROVED" for r in rows),
            "nonempty_conditions": sum(bool(r["frame"]["conditions"]) for r in rows),
            "nonempty_cautions": sum(bool(r["frame"]["cautions"]) for r in rows),
            "core_claim_count": sum(len(r["frame"]["core_claims"]) for r in rows),
            "rows": rows, "real_ai_calls": 0, "production_writes": False}


def main():
    if sys.argv[1:] == ["--worker"]:
        try:
            print(json.dumps(worker(), ensure_ascii=True, allow_nan=False))
            return 0
        except Exception:
            print('{"error":"frame_audit_unavailable"}')
            return 1
    environment = {k: v for k, v in os.environ.items()
                   if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP"}}
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    run = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(Path(__file__).resolve()), "--worker"],
                         capture_output=True, timeout=300, env=environment, cwd=ROOT, **options)
    if run.returncode:
        print("frame_audit_unavailable")
        return 1
    result = json.loads(run.stdout)
    if result["count"] != 384 or result["signed_approved_frames"] != 384:
        raise ValueError("incomplete_audit")
    (ROOT / "docs/day6a_frame_audit.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
