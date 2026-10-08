"""Server-only Day 3 transport. Fixed diagnostic request; no reading generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
import re
import time
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


# Reuse the independently accepted production settings without importing or
# executing production code. See docs/day3_deepseek_config_provenance.md.
ENDPOINT = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-flash"
MAX_RESPONSE_BYTES = 64_000
RESULT_CODES = {"ok", "not_configured", "redirect_blocked", "http_failure", "response_too_large",
                "unsafe_response", "incomplete_response", "empty_content", "schema_failure",
                "network_failure", "internal_failure"}


def safe_http_status(value) -> int | None:
    return int(value) if isinstance(value, int) and not isinstance(value, bool) and 100 <= value <= 599 else None


@dataclass(frozen=True)
class DeepSeekConfig:
    api_key: str = field(default="", repr=False)
    provider_name: str = "deepseek"
    endpoint: str = ENDPOINT
    model_name: str = MODEL
    timeout_seconds: float = 20.0

    @property
    def configured(self) -> bool:
        return bool(re.fullmatch(r"[A-Za-z0-9_-]{8,256}", self.api_key))


def load_config(env: Mapping[str, str] | None = None) -> DeepSeekConfig:
    environment = os.environ if env is None else env
    value = environment.get("DEEPSEEK_API_KEY", "")
    if not value and env is None and os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as scope:
                value, _ = winreg.QueryValueEx(scope, "DEEPSEEK_API_KEY")
        except (ImportError, OSError):
            value = ""
    return DeepSeekConfig(api_key=value.strip() if isinstance(value, str) else "")


class NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HTTPError(req.full_url, code, "Redirect blocked", {}, None)


def open_https(request: Request, *, timeout: float):
    # Never forward credentials through an environment-supplied proxy/redirect.
    return build_opener(ProxyHandler({}), NoRedirectHandler()).open(request, timeout=timeout)


class ProviderFailure(Exception):
    def __init__(self, code: str, http_status: int | None = None):
        super().__init__(code)
        self.code = code
        self.http_status = http_status


def strict_json(text: str):
    def pairs(entries):
        result = {}
        for key, value in entries:
            if key in result:
                raise ValueError("duplicate_key")
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("invalid_number")))


@dataclass(frozen=True)
class ConnectivityResult:
    provider_name: str
    model_name: str
    success: bool
    http_status: int | None
    latency_seconds: float
    attempts: int
    retried: bool
    result_code: str
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    checked_at: str

    def public_record(self) -> dict:
        # Explicit whitelist. Never serialize arbitrary objects/config/request.
        return {
            "provider_name": self.provider_name, "model_name": self.model_name,
            "success": self.success, "http_status": self.http_status,
            "latency_seconds": self.latency_seconds, "attempts": self.attempts,
            "retried": self.retried, "result_code": self.result_code,
            "prompt_tokens": self.prompt_tokens, "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens, "checked_at": self.checked_at,
        }


class DeepSeekConnectivityProvider:
    """Only a fixed diagnostic is exposed. No arbitrary prompt/stream API."""

    def __init__(self, config: DeepSeekConfig, *, transport: Callable = open_https):
        if (config.endpoint != ENDPOINT or config.provider_name != "deepseek"
                or config.model_name != MODEL or not 0 < config.timeout_seconds <= 30):
            raise ProviderFailure("invalid_configuration")
        self._config = config
        self._transport = transport

    def check_connection(self) -> ConnectivityResult:
        started = time.monotonic()
        http_status = None
        attempts = 0
        usage: dict = {}
        success = False
        code = "not_configured"
        try:
            if not self._config.configured:
                raise ProviderFailure("not_configured")
            payload = {
                "model": self._config.model_name, "temperature": 0,
                "max_tokens": 32, "stream": False,
                "thinking": {"type": "disabled"},
                "response_format": {"type": "json_object"},
                "messages": [{"role": "user", "content": 'Connectivity diagnostic. Return only this JSON: {"status":"ok"}'}],
            }
            request = Request(ENDPOINT, method="POST", data=json.dumps(payload).encode("utf-8"),
                              headers={"Authorization": "Bearer " + self._config.api_key,
                                       "Content-Type": "application/json", "Accept": "application/json"})
            attempts = 1  # Exactly one attempt; no automatic retry for this stage.
            with self._transport(request, timeout=self._config.timeout_seconds) as response:
                http_status = safe_http_status(response.status)
                if http_status is None:
                    raise ProviderFailure("schema_failure")
                if http_status != 200:
                    raise ProviderFailure("redirect_blocked" if 300 <= http_status < 400 else "http_failure", http_status)
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ProviderFailure("response_too_large")
            text = raw.decode("utf-8")
            if self._config.api_key in text:
                raise ProviderFailure("unsafe_response")
            envelope = strict_json(text)
            choice = envelope["choices"][0]
            if choice.get("finish_reason") != "stop":
                raise ProviderFailure("incomplete_response")
            content = choice["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ProviderFailure("empty_content")
            if strict_json(content) != {"status": "ok"}:
                raise ProviderFailure("schema_failure")
            raw_usage = envelope.get("usage", {})
            if isinstance(raw_usage, dict):
                usage = {key: value for key, value in raw_usage.items()
                         if key in {"prompt_tokens", "completion_tokens", "total_tokens"}
                         and type(value) is int and 0 <= value <= 10_000_000}
            success, code = True, "ok"
        except HTTPError as error:
            http_status = safe_http_status(error.code)
            code = "redirect_blocked" if http_status is not None and 300 <= http_status < 400 else "http_failure"
            error.close()  # Do not read/record the upstream HTTP error body.
        except (TimeoutError, URLError, ConnectionError, OSError):
            code = "network_failure"
        except ProviderFailure as error:
            code = error.code if error.code in RESULT_CODES else "internal_failure"
        except (ValueError, UnicodeError, KeyError, IndexError, TypeError, AttributeError):
            code = "schema_failure"
        except Exception:
            code = "internal_failure"  # Never surface str(exception) or traceback.
        return ConnectivityResult(
            "deepseek", MODEL, success, http_status, round(time.monotonic() - started, 3),
            attempts, False, code, usage.get("prompt_tokens"), usage.get("completion_tokens"),
            usage.get("total_tokens"), datetime.now(timezone.utc).isoformat(),
        )


def public_status(config: DeepSeekConfig | None = None) -> dict:
    current = config if config is not None else load_config()
    return {"provider_name": "deepseek", "model_name": MODEL, "endpoint": ENDPOINT,
            "configured": current.configured, "configuration_status": "已配置" if current.configured else "未配置",
            "integration_status": "connectivity_only", "reading_enabled": False}
