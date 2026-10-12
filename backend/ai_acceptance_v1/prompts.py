"""Existing Day8B projection, deep copied and re-sealed; no arbitrary prompt API."""

from copy import deepcopy
import hashlib
import math
from pathlib import Path
import sys

from backend.question_quality_v1.contract import (ApplicationDraft, IndependentVerdict,
    QualityRequest, ROLES, application_scope_errors, limit_ids, validate_draft)
from scripts.day8b_prepare import CANDIDATE_SYSTEM, REVIEW_SYSTEM, safe_context
from .policy import AcceptanceDenied, MODEL, MAX_OUTPUT, TOKENIZER_SHA, canonical, sha


def messages_for(request, phase, draft=None):
    if type(request) is not QualityRequest:
        raise AcceptanceDenied("controlled_quality_request_required")
    payload = deepcopy(request.checked())
    if set(payload["frames"]) != set(ROLES) or application_scope_errors(payload):
        raise AcceptanceDenied("source_or_scope_unavailable")
    context = safe_context(payload, request.fingerprint, limit_ids)
    if phase == "candidate" and draft is None:
        system = CANDIDATE_SYSTEM
        body = {"context": context, "output_schema": ApplicationDraft.model_json_schema()}
    elif phase == "reviewer" and type(draft) is ApplicationDraft and not validate_draft(request, draft):
        system = REVIEW_SYSTEM
        body = {"context": context, "draft": draft.model_dump(),
                "draft_fingerprint": sha(draft.model_dump()), "output_schema": IndependentVerdict.model_json_schema()}
    else:
        raise AcceptanceDenied("invalid_phase_or_draft")
    request.checked()  # Never hand the mutable sealed source to a provider.
    return [{"role": "system", "content": system}, {"role": "user", "content": canonical(body)}]


def wire_for(messages, phase):
    return {"model": MODEL, "messages": deepcopy(messages), "temperature": 0,
            "max_tokens": MAX_OUTPUT[phase], "stream": False,
            "thinking": {"type": "disabled"}, "response_format": {"type": "json_object"}}


class OfficialTokenCounter:
    def __init__(self, root: Path):
        folder = Path(root) / "runtime/day8b-budget"
        tokenizer = folder / "deepseek_v4_tokenizer/tokenizer.json"
        if not tokenizer.is_file() or hashlib.sha256(tokenizer.read_bytes()).hexdigest() != TOKENIZER_SHA:
            raise AcceptanceDenied("pinned_tokenizer_unavailable")
        sys.path.insert(0, str(folder / "lib"))
        from tokenizers import Tokenizer
        self._tokenizer = Tokenizer.from_file(str(tokenizer))

    def reserve_input(self, messages):
        tokens = sum(len(self._tokenizer.encode(m["content"], add_special_tokens=False).ids) for m in messages)
        # Day8B margin, now measuring the ACTUAL review draft, not a placeholder.
        return math.ceil((tokens * 1.15 + 256) / 256) * 256
