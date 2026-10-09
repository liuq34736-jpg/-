"""Fixed imports of frozen production modules, under a read-only/no-network guard.

Run with Python -I -B. No migrations, providers, source acquisition or history.
"""

import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PRODUCTION = ROOT.parent / "streamlit_mvp"
BASELINE_HASH = "9b0687faa2f4e31a58765371f2a79f7a3270dff9bd41a49419e31e32e11b9f57"


def read_only_guard(event, args):
    if event == "open":
        mode, flags = args[1], args[2]
        if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
            isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)):
            raise PermissionError("worker_write_blocked")
    if event in {"os.mkdir", "os.remove", "os.rmdir", "os.rename", "os.link", "os.symlink",
                 "os.chmod", "os.utime", "os.truncate", "subprocess.Popen", "os.system", "sqlite3.connect"}:
        raise PermissionError("worker_side_effect_blocked")
    if event in {"socket.connect", "socket.connect_ex", "socket.getaddrinfo", "socket.bind", "http.client.connect"}:
        raise PermissionError("worker_network_blocked")


class FrozenRuntime:
    def __init__(self):
        sys.dont_write_bytecode = True
        sys.addaudithook(read_only_guard)
        raw = (ROOT / "docs/production_baseline.json").read_bytes()
        if hashlib.sha256(raw).hexdigest() != BASELINE_HASH:
            raise ValueError("baseline_changed")
        baseline = json.loads(raw)
        if baseline["production_root"] != str(PRODUCTION) or baseline["version"] != "1.2.0":
            raise ValueError("invalid_production")
        for relative, expected in baseline["files_sha256"].items():
            path = Path(relative) if Path(relative).is_absolute() else PRODUCTION / relative
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError("frozen_file_changed")
        sys.path.insert(0, str(PRODUCTION))
        sys.path.insert(0, str(ROOT))
        from iching.algorithm import MeihuaTimeAlgorithm
        from iching.hexagrams import calculate_hexagram, load_hexagrams
        from iching.manual_hexagram import manual_hexagram, moving_line_name
        from iching.analysis import analyze_cast_result
        from iching.interpretation import build_interpretation_result
        from iching.texts import TraditionalTextRepository
        from iching.canonical_corpus_v1 import CanonicalCorpus
        from iching.narration.semantic_corpus_v1 import find_corpus_frame, find_corpus_proof
        from iching.narration.semantic_frame_v1 import issue_frame, render_frame
        from backend.app.meihua_models import CHINA
        self.china = CHINA
        self.algorithm = MeihuaTimeAlgorithm(local_timezone=CHINA, day_boundary_mode="midnight")
        self.calculate_hexagram = calculate_hexagram
        self.manual_hexagram = manual_hexagram
        self.line_name = moving_line_name
        self.analyze = analyze_cast_result
        self.interpret = build_interpretation_result
        self.profiles = load_hexagrams()
        self.repo = TraditionalTextRepository()
        self.proof = find_corpus_proof
        self.frame = find_corpus_frame
        self.issue_frame = issue_frame
        self.render_frame = render_frame
        try:
            self.corpus = CanonicalCorpus()
        except (ValueError, OSError):
            self.corpus = None  # Frozen structural analysis still works.

    @staticmethod
    def profile(item):
        return {key: item[key] for key in (
            "id", "name", "full_name", "lines", "binary", "upper_trigram", "lower_trigram")}

    def catalog(self):
        return {"api_version": "meihua_service_adapter_v1", "timezone": "Asia/Shanghai",
                "entries": [{**self.profile(p), "line_names": [self.line_name(p["lines"], i) for i in range(1, 7)]}
                            for p in self.profiles]}

    def meanings(self, objects, units):
        meanings, references = [], []
        for role, internal_role, hid, pos in objects:
            fallback = next(unit["statement"] for unit in units if unit["type"] == internal_role)
            item = {"role": role, "text": fallback, "status": "structure_fallback", "source_evidence_ids": []}
            if self.corpus is not None:
                bundle = self.corpus.bundle(hid, pos, internal_role)
                if bundle:
                    try:
                        proof = self.proof(bundle)
                        record = self.frame(bundle, proof) if proof else None
                        if record:
                            frame = self.issue_frame(record["frame"], bundle, proof)
                            item.update(text=self.render_frame(frame), status="SEMANTIC_APPROVED",
                                        source_evidence_ids=frame.to_dict()["source_evidence_ids"])
                    except (ValueError, OSError, KeyError, TypeError):
                        pass  # No generation, re-signing on disk or lowered gate.
                    for row in bundle["evidence"]:
                        source_row = self.corpus.by_key[(hid, pos, row["field"])]
                        witness = next(w for w in source_row["source_witnesses"] if w["source_id"] == row["source_id"])
                        references.append({"evidence_id": row["evidence_id"], "role": role,
                            "section_type": row["field"], "text": row["text"],
                            "source_title": row["source_title"], "edition": row["edition"],
                            "url": witness["canonical_url"], "volume": witness["volume"],
                            "location": witness["content_location"], "original_pages": None,
                            "verification_status": row["verification_status"],
                            "variant_present": bool(source_row["textual_variants"])})
            meanings.append(item)
        return meanings, references

    def calculate(self, data):
        from backend.app.meihua_models import ManualInput, TimeInput, china_moment, CalculationResult
        if set(data) - {"input_mode", "hexagram_id", "moving_line", "cast_at"}:
            raise ValueError("unexpected_worker_input")
        request = (ManualInput if data.get("input_mode") == "manual_hexagram" else TimeInput).model_validate(data)
        moment = china_moment(request.cast_at)
        if isinstance(request, ManualInput):
            cast = self.manual_hexagram(request.hexagram_id, request.moving_line, moment)
        else:
            cast = self.calculate_hexagram(moment, self.algorithm)
        analysis = self.analyze(cast, moment)
        interpretation = self.interpret(cast, analysis, repository=self.repo)
        units = [{"type": u["type"], "statement": u["statement"],
                  "evidence": [{"type": e["type"], "rule_version": e["rule"]} for e in u["evidence"]]}
                 for u in interpretation["interpretation_units"]]
        original, changed = cast["primary"], cast["changed"]
        mutual = next(p for p in self.profiles if p["id"] == analysis["mutual_hexagram"]["id"])
        meanings, references = self.meanings([
            ("original_hexagram", "current_state", original["id"], None),
            ("moving_line", "primary_change", original["id"], cast["moving_line"]),
            ("mutual_hexagram", "internal_process", mutual["id"], None),
            ("changed_hexagram", "change_direction", changed["id"], None)], units)
        strength = analysis["strength"]
        from datetime import datetime
        time_fields = {name: datetime.fromisoformat(strength[name]).astimezone(self.china).isoformat(timespec="seconds")
                       for name in ("active_solar_term_time", "next_solar_term_time", "strength_boundary_time", "next_month_boundary_time")}
        elements = interpretation["five_elements"]
        body_use = analysis["body_use"]
        from backend.app.meihua_models import TimeCalculation
        time_calculation = ({key: cast["calculation"][key] for key in TimeCalculation.model_fields}
                            if isinstance(request, TimeInput) else None)
        output = {"api_version": "meihua_service_adapter_v1", "input_mode": request.input_mode,
            "cast_at": moment.isoformat(timespec="seconds"), "timezone": "Asia/Shanghai", "line_order": "bottom_up",
            "original_hexagram": self.profile(original), "mutual_hexagram": self.profile(mutual),
            "changed_hexagram": self.profile(changed),
            "moving_line": {"position": cast["moving_line"], "name": interpretation["moving_line"]["position_name"],
                            "polarity": original["lines"][cast["moving_line"] - 1]},
            "body_use": {"rule_version": body_use["rule_version"], "body_trigram": body_use["body_trigram"],
                         "yong_trigram": body_use["yong_trigram"], "body_element": elements["body"],
                         "yong_element": elements["yong"], "relation": elements["relation"], "relation_text": elements["relation_text"]},
            "strength": {"rule_version": strength["strength_rule_version"], "timezone": "Asia/Shanghai",
                **{key: strength[key] for key in ("solar_term_month_branch", "ruling_element", "active_solar_term", "next_solar_term", "solar_term_source")},
                **time_fields, "body": strength["body_use_strength"]["body"], "yong": strength["body_use_strength"]["yong"],
                "mutual": strength["auxiliary_strength"]["mutual_hexagram"], "changed": strength["auxiliary_strength"]["changed_hexagram"],
                "auxiliary_weight": "auxiliary_strength"},
            "time_calculation": time_calculation,
            "versions": {"production_version": "1.2.0", "casting_version": cast["algorithm_version"],
                         "analysis_version": analysis["analysis_version"], "interpretation_version": interpretation["interpretation_version"],
                         "body_use_version": body_use["rule_version"], "strength_version": strength["strength_rule_version"],
                         "source_corpus_version": "canonical_meihua_corpus_v1", "semantic_frame_version": "verified_semantic_frame_v1"},
            "interpretation_units": units, "standard_meanings": meanings, "source_references": references,
            "ai_used": False, "history_saved": False}
        return CalculationResult.model_validate(output).model_dump()


def main():
    try:
        value = json.loads(sys.stdin.buffer.read(8193))
        if not isinstance(value, dict) or set(value) - {"operation", "data"}:
            raise ValueError("invalid_worker_request")
        runtime = FrozenRuntime()
        if value["operation"] == "catalog" and set(value) == {"operation"}:
            result = runtime.catalog()
        elif value["operation"] == "calculate" and set(value) == {"operation", "data"}:
            result = runtime.calculate(value["data"])
        else:
            raise ValueError("invalid_operation")
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
    except Exception:
        print('{"error":"frozen_service_unavailable"}')
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
