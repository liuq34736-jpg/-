"""Evidence and reality separated; no new source, Frame, condition or verdict."""

from dataclasses import dataclass, field
import hmac
import json
from pathlib import Path
import re
import secrets
from typing import Literal
import unicodedata

from pydantic import BaseModel, ConfigDict, Field
from backend.traditional_judgement_v1.trusted_input import ValidatedJudgementInput, digest
from backend.traditional_preview_v1.engine import PreviewJudgementEngine

VERSION = "question_application_contract_v1"
ROLES = ("original_hexagram", "moving_line", "mutual_hexagram", "changed_hexagram")
_ISSUER = object()
_KEY = secrets.token_bytes(32)
_SCOPE_HOLDS = Path(__file__).resolve().parents[2] / "data/day8a_application_scope_holds.json"
_SCOPE_HOLDS_SHA256 = "6067ab257574049ff34df44631a815b3f9f1a24309e788d190a4905d4a4d207c"


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class QuestionSpan(ContractModel):
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str = Field(min_length=1, max_length=500)
    kind: Literal["reported", "reported_speech", "goal", "question", "time_window", "unknown"]


class QuestionIntent(ContractModel):
    category: Literal["general", "career", "business", "relationship", "decision", "travel", "other"]
    focus: QuestionSpan
    provided: list[QuestionSpan] = Field(max_length=12)
    missing: list[Literal["background", "options", "constraints", "time_window", "other_party_view"]] = Field(max_length=5)


class ApplicationClaim(ContractModel):
    claim_id: str = Field(pattern=r"^[a-z][a-z0-9_]{0,40}$")
    role: Literal["original_hexagram", "moving_line", "mutual_hexagram", "changed_hexagram"]
    frame_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    meaning_refs: list[int] = Field(min_length=1, max_length=8)
    source_evidence_ids: list[str] = Field(min_length=1, max_length=30)
    question_spans: list[QuestionSpan] = Field(min_length=1, max_length=12)
    preserved_limit_ids: list[str] = Field(max_length=32)
    analogy_text: str = Field(min_length=20, max_length=180)
    guidance: str = Field(min_length=6, max_length=80)
    source_layer: Literal["application_analogy"]


class ApplicationDraft(ContractModel):
    contract_version: Literal["question_application_contract_v1"]
    request_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    intent: QuestionIntent
    claims: list[ApplicationClaim] = Field(min_length=4, max_length=4)


class ClaimVerdict(ContractModel):
    claim_id: str
    reviewed_frame_id: str
    reviewed_evidence_ids: list[str]
    reviewed_limit_ids: list[str]
    supported: bool
    preserves_conditions: bool
    no_invented_facts: bool
    no_prediction: bool
    preserves_scope: bool
    question_relevant: bool
    score: int = Field(ge=0, le=4)
    reason: str = Field(min_length=8, max_length=400)


class IndependentVerdict(ContractModel):
    contract_version: Literal["question_application_contract_v1"]
    request_fingerprint: str
    draft_fingerprint: str
    claims: list[ClaimVerdict] = Field(min_length=4, max_length=4)


@dataclass(frozen=True)
class QualityRequest:
    # Internal only; contains source/Frame identifiers, never placed on the page.
    payload: dict = field(repr=False)
    fingerprint: str
    _issuer: object = field(repr=False, compare=False)
    _seal: bytes = field(repr=False, compare=False)

    def checked(self):
        if self._issuer is not _ISSUER or digest(self.payload) != self.fingerprint or not hmac.compare_digest(
            self._seal, hmac.digest(_KEY, self.fingerprint.encode(), "sha256")
        ):
            raise ValueError("invalid_quality_request")
        return self.payload


def build_request(trusted: ValidatedJudgementInput) -> QualityRequest:
    if type(trusted) is not ValidatedJudgementInput:
        raise ValueError("frozen_guarded_input_required")
    data = trusted.to_dict()
    # Compute the Day 7A qualification ourselves, not a caller/LLM's JSON.
    judgement = PreviewJudgementEngine().evaluate(trusted).model_dump()
    references = {r["evidence_id"]: r for r in data["calculation"]["source_references"]
                  if r["verification_status"] in {"verified", "machine_verified"}}
    frames = {}
    for role, item in data["frames"].items():
        if not item:
            continue
        frame = item["frame"]
        if (frame["semantic_status"] != "SEMANTIC_APPROVED" or item["frame_id"] != digest(frame)
                or frame["target_role"] != role or not set(frame["source_evidence_ids"]) <= references.keys()):
            continue
        frames[role] = item
    payload = {"version": VERSION, "question": data["calculation"]["question_text"],
               "calculation": data["calculation"], "frames": frames, "judgement": judgement,
               "evidence": references}
    fingerprint = digest(payload)
    return QualityRequest(payload, fingerprint, _ISSUER, hmac.digest(_KEY, fingerprint.encode(), "sha256"))


def normalize(text):
    text = unicodedata.normalize("NFKC", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    return re.sub(r"\s+", "", text).translate(str.maketrans({
        "體": "体", "變": "变", "實": "实", "際": "际", "無": "无", "會": "会", "敗": "败", "應": "应",
        "條": "条", "滿": "满", "證": "证", "絕": "绝", "賺": "赚", "虧": "亏", "結": "结", "擔": "担",
    }))


def validate_span(question, span):
    return span.start < span.end <= len(question) and question[span.start:span.end] == span.text


def span_type_errors(span):
    if span.kind != "reported":
        return []
    if re.search(r"吗|？|\?|想|希望|请|直接说|忽略|不知道|不清楚", span.text):
        return ["question_or_goal_as_fact"]
    if re.search(r"对方说|他说|她说|听说", span.text):
        return ["reported_speech_as_established_fact"]
    return []


def time_windows(question):
    # Report exact lexical windows; past duration is not a future window.
    return [m.group() for m in re.finditer(r"下周|下个月|本周|这个月|今年|年底|近期|明天|后天|[0-9]+(?:天|周|个月)内", question)]


def safety_flags(text, question):
    """Conservative known-pattern gate. NOT a proof of open-language correctness."""
    s, q = normalize(text), normalize(question)
    flags = []
    if re.search(r"一定|必然|注定|必成|必败|肯定成功|保证|至少不会|就能避免|不会失去|必不会|绝不会|十有八九|稳赚|确保|会成功|会失败|不会出事|不会亏|结果已定", s):
        flags.append("implicit_or_absolute_prediction")
    if re.search(r"(?:下周|下个月|年底|[0-9]+天内).{0,12}(?:会有结果|将会|成功|回来|赚|完成)", s):
        flags.append("time_prediction")
    if re.search(r"(?:前提|条件)(?:已经|已|都|也|尚|仍|并|不|未|全|为|是|满足|成立|不足|不成立|也不成立)", s):
        flags.append("source_condition_determination")
    if re.search(r"(?:本卦|变卦|互卦|体卦|用卦|体用|金旺|木衰|综合方向|综合倾向|审核资格|已(?:经)?审核|具备裁决资格|偏有利|偏不利|大吉|大凶)", s):
        flags.append("locked_fact_declaration")
    if re.search(r"你已经|你现在的.{0,6}(?:是|很|较|已经)|对方其实|对方已经|你的能力很|你的处境稳定|你心理稳定|你资金充足", s):
        flags.append("unprovided_reality_assertion")
    for word in ("备货", "推广", "租金", "已付出", "回款", "收回的款项", "对方的过失", "已欠债", "他还爱你", "她还爱你", "库存"):
        if word in s and word not in q:
            flags.append("unprovided_reality:" + word)
    if re.search(r"<[^>]*>|sk-[a-z0-9_-]{10,}|authorization|bearer|http[s]?://", s, re.I):
        flags.append("unsafe_output")
    return sorted(set(flags))


def limit_ids(payload, role):
    frame = payload["frames"][role]["frame"]
    ids = [f"{role}.{name}.{index}" for name in ("conditions", "cautions") for index in range(len(frame[name]))]
    if role == "moving_line":
        j = payload["judgement"]
        ids.extend(a["id"] for a in j["conditions"] + j["scope_limits"])
    return ids


def application_scope_errors(payload):
    """Pinned, rejection-only application audit; never edits/approves a Frame."""
    try:
        raw = _SCOPE_HOLDS.read_bytes()
        registry = json.loads(raw)
        # Canonical content hash survives Git's Windows line-ending conversion.
        if digest(registry) != _SCOPE_HOLDS_SHA256:
            return ["application_scope_registry_unavailable"]
        if registry["version"] != "application_scope_hold_v1" or registry["allows_approval"] is not False:
            return ["application_scope_registry_unavailable"]
        for item in payload["frames"].values():
            frame = item["frame"]
            for hold in registry["holds"]:
                if digest(frame["core_claims"]) != hold["core_claims_sha256"]:
                    continue
                # A known insufficient summary must not acquire application
                # authority via a permissive model receipt or a stale binding.
                if (frame["source_fingerprint"] != hold["source_fingerprint_at_audit"]
                        or set(frame["source_evidence_ids"]) != set(hold["source_evidence_ids"])
                        or not any(hold["source_excerpt"] in payload["evidence"][e]["text"]
                                   for e in hold["source_evidence_ids"])):
                    return ["application_scope_hold_binding_failure"]
                return ["known_source_scope_hold"]
        return []
    except (OSError, ValueError, KeyError, TypeError):
        return ["application_scope_registry_unavailable"]


def validate_draft(request, draft):
    p = request.checked()
    if type(draft) is not ApplicationDraft or draft.request_fingerprint != request.fingerprint:
        return ["draft_binding"]
    if set(p["frames"]) != set(ROLES):
        return ["missing_approved_frame"]
    scope_errors = application_scope_errors(p)
    if scope_errors:
        return scope_errors
    if {c.role for c in draft.claims} != set(ROLES) or len({c.claim_id for c in draft.claims}) != 4:
        return ["role_or_id_binding"]
    spans = [draft.intent.focus, *draft.intent.provided]
    errors = []
    if any(not validate_span(p["question"], s) for s in spans): errors.append("intent_exact_span")
    if "time_window" in draft.intent.missing and time_windows(p["question"]): errors.append("provided_time_marked_missing")
    # A question, goal, reported speech or a command is never an established fact.
    for span in spans:
        errors.extend(span_type_errors(span))
    texts = []
    for claim in draft.claims:
        item = p["frames"][claim.role]
        frame = item["frame"]
        if claim.frame_id != item["frame_id"]: errors.append("frame_binding")
        if len(set(claim.meaning_refs)) != len(claim.meaning_refs): errors.append("duplicate_meaning_refs")
        if any(i < 0 or i >= len(frame["core_claims"]) for i in claim.meaning_refs):
            errors.append("meaning_binding")
            continue
        expected = {e for i in claim.meaning_refs for e in frame["core_claims"][i]["supported_by"]}
        if set(claim.source_evidence_ids) != expected or not expected <= set(p["evidence"]): errors.append("evidence_binding")
        if set(claim.preserved_limit_ids) != set(limit_ids(p, claim.role)): errors.append("omitted_or_added_limits")
        if any(not validate_span(p["question"], s) for s in claim.question_spans): errors.append("application_exact_span")
        for span in claim.question_spans: errors.extend(span_type_errors(span))
        text = claim.analogy_text + claim.guidance
        errors.extend(safety_flags(text, p["question"]))
        if not re.search(r"可|如果|若|是否|先核对|先了解|不确定", text): errors.append("unscoped_analogy")
        if re.search(r"[。；]{2,}", text): errors.append("duplicated_punctuation")
        normalized = normalize(claim.analogy_text)
        if normalized in texts: errors.append("repetitive_application")
        texts.append(normalized)
        if re.match(r"(?:围绕这件|放在.{0,10}中)[，,：:]?" ,claim.analogy_text) and any(
                normalize(a["text"]) in normalized for a in frame["core_claims"]):
            errors.append("mechanical_prefix_only")
    return sorted(set(errors))


def validate_verdict(request, draft, verdict):
    if type(verdict) is not IndependentVerdict or verdict.request_fingerprint != request.fingerprint or verdict.draft_fingerprint != digest(draft.model_dump()):
        return ["verdict_binding"]
    by_id = {c.claim_id: c for c in draft.claims}
    if len({v.claim_id for v in verdict.claims}) != 4 or {v.claim_id for v in verdict.claims} != set(by_id):
        return ["verdict_claim_binding"]
    errors = []
    for v in verdict.claims:
        c = by_id[v.claim_id]
        if v.reviewed_frame_id != c.frame_id or set(v.reviewed_evidence_ids) != set(c.source_evidence_ids) or set(v.reviewed_limit_ids) != set(c.preserved_limit_ids):
            errors.append("verifier_evidence_or_limit_binding")
        if v.score < 3 or not all((v.supported, v.preserves_conditions, v.no_invented_facts, v.no_prediction, v.preserves_scope, v.question_relevant)):
            errors.append("independent_semantic_rejection")
    return sorted(set(errors))
