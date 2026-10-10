"""Offline only. Independent request, fail closed; no networking/cache/history."""

from dataclasses import dataclass
from typing import Protocol
from backend.traditional_judgement_v1.trusted_input import digest
from .contract import ApplicationDraft, IndependentVerdict, QualityRequest, validate_draft, validate_verdict


class CandidateProvider(Protocol):
    def generate(self, request: QualityRequest) -> ApplicationDraft: ...


class IndependentReviewer(Protocol):
    def review(self, request: QualityRequest, draft: ApplicationDraft) -> IndependentVerdict: ...


@dataclass(frozen=True)
class OfflineResult:
    status: str
    errors: tuple[str, ...]
    sections: tuple[tuple[str, str], ...]
    draft_fingerprint: str | None
    production_approved: bool = False
    history_written: bool = False


def fallback(request, errors):
    p = request.checked()
    # Approved basic meaning verbatim, NOT a new contextual extrapolation.
    return OfflineResult("BASE_FALLBACK", tuple(errors), tuple(
        (m["role"], m["text"]) for m in p["calculation"]["standard_meanings"]), None)


def run_offline(request, candidate, reviewer):
    if type(request) is not QualityRequest: raise ValueError("controlled_quality_request_required")
    request.checked()
    if candidate is reviewer:
        return fallback(request, ["independent_reviewer_required"])
    if not request.payload["question"]:
        return fallback(request, ["empty_question"])
    try:
        draft = candidate.generate(request)
        errors = validate_draft(request, draft)
        if errors: return fallback(request, errors)
        verdict = reviewer.review(request, draft)  # No generator conversation/reasoning is passed.
        errors = validate_verdict(request, draft, verdict)
        if errors: return fallback(request, errors)
        # Final clauses are rendered by the program. Locked facts/judgment are NEVER model output.
        p = request.checked()
        sections = []
        for c in draft.claims:
            frame = p["frames"][c.role]["frame"]
            atoms = frame["core_claims"]
            text = "传统卦义：" + "；".join(atoms[i]["text"] for i in c.meaning_refs)
            text += "\n现实应用类比（未认定现实条件）：" + c.analogy_text + "\n可以核对：" + c.guidance
            limits = [a["text"] for name in ("conditions", "cautions") for a in frame[name]]
            if c.role == "moving_line":
                limits.extend(a["text"] for a in p["judgement"]["conditions"] + p["judgement"]["scope_limits"])
            if limits:
                text += "\n适用前提与限制（现实是否满足未核实）：" + "；".join(limits)
            if c.role == "mutual_hexagram": text += "\n仅作内部过程的辅助观察。"
            if c.role == "changed_hexagram": text += "\n这是变化后的结构方向，不是事情必然发生的结果。"
            sections.append((c.role, text))
        return OfflineResult("OFFLINE_ACCEPTED", (), tuple(sections), digest(draft.model_dump()))
    except Exception:
        return fallback(request, ["offline_provider_or_contract_failure"])
