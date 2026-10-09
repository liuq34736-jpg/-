"""Fixed read-only Day 4 bridge; no public API accepts arbitrary calculation JSON."""

from dataclasses import dataclass, field
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

from backend.app.meihua_models import ManualInput, TimeInput, ReadingResponse

ROOT = Path(__file__).resolve().parents[2]
_ISSUER = object()
_INPUT_KEY = secrets.token_bytes(32)  # Ephemeral seal, never stored or exposed.
ROLES = ("original_hexagram", "moving_line", "mutual_hexagram", "changed_hexagram")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


class JudgementUnavailable(Exception):
    def __init__(self):
        super().__init__("离线判断所需的冻结输入暂不可用；未生成新的判断。")


@dataclass(frozen=True)
class ValidatedJudgementInput:
    payload_json: str = field(repr=False)
    _issuer: object = field(repr=False, compare=False)
    _seal: str = field(repr=False, compare=False)

    def to_dict(self):
        if self._issuer is not _ISSUER or not hmac.compare_digest(
            self._seal, hmac.new(_INPUT_KEY, self.payload_json.encode("utf-8"), hashlib.sha256).hexdigest()
        ):
            raise JudgementUnavailable()
        return json.loads(self.payload_json)


def _issue(payload):
    """Internal boundary, called only after the fixed guarded subprocess succeeds."""
    if set(payload) != {"calculation", "frames", "auxiliary_relations", "excluded_evidence"}:
        raise JudgementUnavailable()
    ReadingResponse.model_validate(payload["calculation"])
    if set(payload["frames"]) != set(ROLES) or set(payload["auxiliary_relations"]) != {"mutual", "changed"}:
        raise JudgementUnavailable()
    raw = canonical(payload)
    return ValidatedJudgementInput(raw, _ISSUER, hmac.new(_INPUT_KEY, raw.encode("utf-8"), hashlib.sha256).hexdigest())


class OfflineJudgementAdapter:
    """Local development only; no database, network, acquisition or model calls."""

    def calculate(self, request: ManualInput | TimeInput):
        return self.calculate_batch([request])[0]

    def calculate_batch(self, requests):
        if type(requests) is not list or not 1 <= len(requests) <= 96:
            raise JudgementUnavailable()
        if any(type(r) not in {ManualInput, TimeInput} for r in requests):
            raise JudgementUnavailable()
        data = [r.model_dump(exclude={"question_text"}) for r in requests]
        environment = {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP"}}
        options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
        try:
            run = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(ROOT / "backend/traditional_judgement_v1/worker.py")],
                input=canonical(data).encode("utf-8"), capture_output=True, timeout=180,
                cwd=ROOT, env=environment, check=False, **options)
            if run.returncode or len(run.stdout) > 32_000_000:
                raise JudgementUnavailable()
            results = json.loads(run.stdout)
            if type(results) is not list or len(results) != len(requests):
                raise JudgementUnavailable()
            trusted = []
            for result, request in zip(results, requests):
                result["calculation"]["question_text"] = request.question_text
                result["calculation"]["question_applied_to_calculation"] = False
                trusted.append(_issue(result))
            return trusted
        except (ValueError, TypeError, KeyError, OSError, subprocess.TimeoutExpired):
            raise JudgementUnavailable() from None
