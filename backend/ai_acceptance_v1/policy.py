"""Pinned price snapshot and integer USD-nanodollar accounting; no credentials."""

from dataclasses import dataclass
from datetime import date
import hashlib
import json

VERSION = "day8b1_acceptance_budget_v1"
RUN_ID = "day8b_first_real_acceptance_v1"
PROVIDER = "deepseek"
MODEL = "deepseek-flash"
ENDPOINT = "https://api.deepseek.com/chat/completions"
PRICE_VERSION = "deepseek_flash_official_2026_10_12"
PRICE_URL = "https://api-docs.deepseek.com/quick_start/pricing/"
PRICE_CHECKED_ON = "2026-10-12"
# Integer nanodollars per token: $0.30/1M = 300 nano-USD/token.
PEAK = {"input_miss": 300, "input_hit": 6, "output": 1200}
OFF_PEAK = {"input_miss": 150, "input_hit": 3, "output": 600}
MAX_QUESTIONS = 6
MAX_REQUESTS = 12
MAX_TOKENS = 250_000
MAX_FEE_NANO_USD = 150_000_000
MAX_OUTPUT = {"candidate": 4096, "reviewer": 3072}
BATCHES = {1: ("B01", "B02"), 2: ("B03", "B04", "B05", "B06")}
BATCH_REQUESTS = {1: 4, 2: 8}
MAX_INPUT = 30_000
TOKENIZER_SHA = "89085f12ef79460ac5f66d1119325ddfc694b4ab209d80bbd81d35f081dc9614"


class AcceptanceDenied(Exception):
    """Only a fixed internal code; never upstream exception text."""


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def sha(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def policy_record():
    return {"version": VERSION, "run_id": RUN_ID, "provider": PROVIDER,
            "model": MODEL, "endpoint": ENDPOINT, "price_version": PRICE_VERSION,
            "price_url": PRICE_URL, "checked_on": PRICE_CHECKED_ON,
            "peak_nano_usd_per_token": PEAK, "off_peak_nano_usd_per_token": OFF_PEAK,
            "questions": MAX_QUESTIONS, "requests": MAX_REQUESTS,
            "tokens": MAX_TOKENS, "fee_nano_usd": MAX_FEE_NANO_USD,
            "outputs": MAX_OUTPUT, "max_input": MAX_INPUT, "automatic_retries": 0}


def require_fresh_price(today=None):
    # Future paid runs cannot silently reuse this dated snapshot.
    if (today or date.today()).isoformat() != PRICE_CHECKED_ON:
        raise AcceptanceDenied("price_reconfirmation_required")


@dataclass(frozen=True)
class Usage:
    input_miss: int
    input_hit: int
    output: int

    def __post_init__(self):
        if any(type(x) is not int or x < 0 for x in
               (self.input_miss, self.input_hit, self.output)):
            raise AcceptanceDenied("usage_invalid")

    @property
    def tokens(self):
        return self.input_miss + self.input_hit + self.output

    @property
    def fee(self):
        # Always peak, even if the vendor charged the off-peak price.
        return self.input_miss * PEAK["input_miss"] + self.input_hit * PEAK["input_hit"] + self.output * PEAK["output"]

    def record(self):
        return {"input_miss": self.input_miss, "input_hit": self.input_hit,
                "output": self.output, "tokens": self.tokens, "fee_nano_usd": self.fee}

    @classmethod
    def parse(cls, raw):
        if not isinstance(raw, dict):
            raise AcceptanceDenied("usage_unavailable")
        keys = ("prompt_tokens", "completion_tokens", "total_tokens",
                "prompt_cache_hit_tokens", "prompt_cache_miss_tokens")
        if any(type(raw.get(k)) is not int or raw[k] < 0 for k in keys):
            raise AcceptanceDenied("usage_unavailable")
        p, o, t, hit, miss = (raw[k] for k in keys)
        if p != hit + miss or t != p + o:
            raise AcceptanceDenied("usage_inconsistent")
        return cls(miss, hit, o)
