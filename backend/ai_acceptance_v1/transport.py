"""One owned worker/request; killed and joined before releasing global slot.

Mock executes the same process supervision; it cannot read a real credential.
Live worker uses the existing HTTPS/redirect-disabled transport exactly once.
Neither process writes logs or persists prompts/upstream response bodies.
"""

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request

ROOT = Path(__file__).resolve().parents[2]
if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
from backend.app.deepseek import load_config, open_https, safe_http_status, strict_json
from backend.ai_acceptance_v1.ledger import BudgetLedger, Reservation
from backend.ai_acceptance_v1.policy import AcceptanceDenied, ENDPOINT, MODEL, Usage, canonical, sha

MAX_RESPONSE = 128_000
CODES = {"ok", "cancelled", "timeout", "http_failure", "redirect_blocked", "network_failure",
         "schema_failure", "empty_content", "incomplete_response", "unsafe_response", "internal_failure",
         "usage_unavailable", "worker_failure", "response_too_large", "not_configured"}


@dataclass(frozen=True)
class TransportResult:
    code: str
    http_status: int | None = None
    content: str | None = field(default=None, repr=False)
    usage: Usage | None = None
    latency: float = 0
    reaped: bool = True


def http_once(wire, config, opener=open_https):
    # This helper is private to the subprocess. Unit tests inject synthetic config.
    if config.endpoint != ENDPOINT or config.model_name != MODEL or config.provider_name != "deepseek" or not 0 < config.timeout_seconds <= 20:
        return {"code": "internal_failure"}
    if not config.configured: return {"code": "not_configured"}
    if wire.get("model") != MODEL or wire.get("stream") is not False or wire.get("max_tokens") not in {4096, 3072}:
        return {"code": "schema_failure"}
    try:
        req = Request(ENDPOINT, method="POST", data=canonical(wire).encode(),
                      headers={"Authorization": "Bearer " + config.api_key,
                               "Content-Type": "application/json", "Accept": "application/json"})
        with opener(req, timeout=config.timeout_seconds) as response:
            status = safe_http_status(response.status)
            if status != 200:
                return {"code": "redirect_blocked" if status and 300 <= status < 400 else "http_failure", "http_status": status}
            raw = response.read(MAX_RESPONSE + 1)
        if len(raw) > MAX_RESPONSE: return {"code": "response_too_large", "http_status": status}
        text = raw.decode("utf-8")
        if config.api_key in text: return {"code": "unsafe_response", "http_status": status}
        value = strict_json(text)
        raw_usage = value.get("usage")
        usage = {k: raw_usage[k] for k in ("prompt_tokens", "completion_tokens", "total_tokens",
                 "prompt_cache_hit_tokens", "prompt_cache_miss_tokens") if k in raw_usage} if isinstance(raw_usage, dict) else None
        base = {"http_status": status, "usage": usage}
        if not isinstance(value.get("choices"), list) or len(value["choices"]) != 1:
            return {**base, "code": "schema_failure"}
        choice = value["choices"][0]
        if choice.get("finish_reason") != "stop": return {**base, "code": "incomplete_response"}
        message = choice["message"]
        if message.get("tool_calls") or message.get("reasoning_content"):
            return {**base, "code": "schema_failure"}
        content = message.get("content")
        if type(content) is not str or not content.strip(): return {**base, "code": "empty_content"}
        return {**base, "code": "ok", "content": content}
    except HTTPError as error:
        status = safe_http_status(error.code); error.close()
        return {"code": "redirect_blocked" if status and 300 <= status < 400 else "http_failure", "http_status": status}
    except (TimeoutError, URLError, ConnectionError, OSError):
        return {"code": "network_failure"}
    except Exception:
        return {"code": "schema_failure"}


class ProcessTransport:
    def __init__(self, ledger, *, mock_replies=None, deadline=22.0):
        if not 0 < deadline <= 22: raise AcceptanceDenied("invalid_deadline")
        if ledger.mode == "mock" and mock_replies is None: raise AcceptanceDenied("mock_transport_required")
        if ledger.mode == "live" and mock_replies is not None: raise AcceptanceDenied("mode_mismatch")
        self.ledger, self.mock_replies, self.deadline = ledger, mock_replies, deadline
        self.starts = self.reaped = 0

    def perform(self, permit: Reservation, wire: dict, cancel: threading.Event):
        self.ledger.check_permit(permit, sha(wire))
        if self.ledger.mode == "live": self.ledger.ensure_price_current()
        self.ledger.claim_dispatch(permit, sha(wire))
        started = time.monotonic()
        if cancel.is_set(): return TransportResult("cancelled")
        env = {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP"}}
        # Both modes exclude API keys inherited from the parent environment.
        # The live child alone may consult the Windows server credential registry.
        packet = {"mode": self.ledger.mode, "wire": wire}
        if self.ledger.mode == "mock":
            packet["mock_reply"] = self.mock_replies[(permit.case_id, permit.phase)]
        else:
            if self.ledger.records != (ROOT / "private/day8b1/records").resolve() or self.ledger.anchors != (ROOT / "private/day8b1-anchors").resolve():
                raise AcceptanceDenied("fixed_live_storage_required")
            packet["permit"] = {k: getattr(permit, k) for k in ("case_id", "phase", "input_tokens", "max_output", "wire_hash", "number")}
            if "DEEPSEEK_API_KEY" in os.environ:
                env["DEEPSEEK_API_KEY"] = os.environ["DEEPSEEK_API_KEY"]
        child = None
        try:
            child = subprocess.Popen([sys.executable, "-I", "-B", "-X", "utf8", str(Path(__file__).resolve()), "--worker"],
                cwd=ROOT, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            self.starts += 1
            data = canonical(packet).encode()
            while True:
                if cancel.is_set(): return TransportResult("cancelled", latency=time.monotonic() - started)
                if time.monotonic() - started >= self.deadline:
                    return TransportResult("timeout", latency=time.monotonic() - started)
                try:
                    out, _ = child.communicate(input=data, timeout=.025)
                    break
                except subprocess.TimeoutExpired:
                    data = None  # Exactly one input and one child. Never retry.
            if child.returncode or len(out) > MAX_RESPONSE + 4096:
                return TransportResult("worker_failure", latency=time.monotonic() - started)
            value = strict_json(out.decode())
            if not isinstance(value, dict) or not set(value) <= {"code", "http_status", "content", "usage"} or value.get("code") not in CODES:
                return TransportResult("worker_failure", latency=time.monotonic() - started)
            try: usage = Usage.parse(value.get("usage"))
            except AcceptanceDenied: usage = None
            content = value.get("content")
            if content is not None and (type(content) is not str or len(content.encode()) > MAX_RESPONSE):
                return TransportResult("schema_failure", usage=usage, latency=time.monotonic() - started)
            return TransportResult(value["code"], safe_http_status(value.get("http_status")),
                                   content, usage, time.monotonic() - started)
        except Exception:
            return TransportResult("worker_failure", latency=time.monotonic() - started)
        finally:
            if child is not None:
                try:
                    if child.poll() is None: child.kill()
                    child.communicate(timeout=2)
                    self.reaped += 1
                except Exception:
                    # Keep the reservation ACTIVE. A leaked worker must never
                    # allow another request through the global slot.
                    return TransportResult("worker_failure", reaped=False, latency=time.monotonic()-started)


def worker():
    # If the supervising caller dies unexpectedly, this worker still has an
    # independent wall-clock ceiling. Its unknown bill remains reserved.
    def watchdog():
        time.sleep(22)
        os._exit(2)
    threading.Thread(target=watchdog,daemon=True).start()
    try:
        packet = strict_json(sys.stdin.buffer.read().decode())
        if packet["mode"] == "mock":
            # No config loading, sockets, HTTP calls or credential lookup here.
            reply = packet["mock_reply"]
            time.sleep(reply.get("delay", 0))
            if reply.get("raise_error"): raise RuntimeError("synthetic_error")
            result = {k: v for k, v in reply.items() if k in {"code", "http_status", "content", "usage"}}
        elif packet["mode"] == "live":
            ledger = BudgetLedger(ROOT / "private/day8b1/records", ROOT / "private/day8b1-anchors", "live")
            ledger.ensure_price_current()
            permit = Reservation(**packet["permit"], _ledger=ledger)
            ledger.claim_worker(permit, sha(packet["wire"]))
            result = http_once(packet["wire"], load_config())
        else: result = {"code": "worker_failure"}
        sys.stdout.write(canonical(result))
        return 0
    except Exception:
        sys.stdout.write('{"code":"worker_failure"}')
        return 1


if __name__ == "__main__":
    # -I direct file needs package root. No alternative public server endpoint.
    sys.path.insert(0, str(ROOT))
    raise SystemExit(worker())
