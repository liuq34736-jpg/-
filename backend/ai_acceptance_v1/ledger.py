"""Append-only private ledger, external high-water anchor, fail-closed reopen.

No constructor auto-initializes a missing database. Locks cover verification,
reservation and settlement across threads/processes. A committed DB with a
missing/stale anchor is deliberately unusable, rather than recovering credit.
"""

from contextlib import closing, contextmanager
from dataclasses import dataclass, field
from datetime import date
import json
import os
from pathlib import Path
import sqlite3
import time

from .policy import (AcceptanceDenied, BATCHES, BATCH_REQUESTS, MAX_FEE_NANO_USD,
                     MAX_INPUT, MAX_OUTPUT, MAX_QUESTIONS, MAX_REQUESTS,
                     MAX_TOKENS, PEAK, OFF_PEAK, PRICE_CHECKED_ON, RUN_ID, Usage, canonical, policy_record, sha)

_ISSUER = object()


@dataclass(frozen=True)
class Reservation:
    case_id: str
    phase: str
    input_tokens: int
    max_output: int
    wire_hash: str
    number: int
    _ledger: object = field(repr=False)
    _issuer: object = field(default=_ISSUER, repr=False)


class BudgetLedger:
    def __init__(self, records: Path, anchors: Path, mode: str):
        if mode not in {"mock", "live"}:
            raise AcceptanceDenied("invalid_mode")
        self.mode = mode
        self.records, self.anchors = Path(records).resolve(), Path(anchors).resolve()
        if self.anchors == self.records or self.anchors.is_relative_to(self.records):
            raise AcceptanceDenied("separate_anchor_required")
        self.name = RUN_ID + "_" + mode
        self.db = self.records / (self.name + ".sqlite3")
        self.anchor = self.anchors / (self.name + ".anchor")
        self.marker = self.anchors / (self.name + ".registered")
        self.lock = self.anchors / (self.name + ".lock")

    @contextmanager
    def _lock(self):
        if not self.anchors.is_dir():
            raise AcceptanceDenied("ledger_not_initialized")
        with self.lock.open("a+b") as stream:
            if stream.tell() == 0:
                stream.write(b"0"); stream.flush()
            until = time.monotonic() + 3
            while True:
                try:
                    stream.seek(0)
                    if os.name == "nt":
                        import msvcrt
                        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.monotonic() > until:
                        raise AcceptanceDenied("ledger_busy") from None
                    time.sleep(.01)
            try:
                yield
            finally:
                stream.seek(0)
                if os.name == "nt":
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(stream, fcntl.LOCK_UN)

    def initialize(self):
        """Operator bootstrap only. Never called by run(), website or reopen."""
        self.records.mkdir(parents=True, exist_ok=True)
        self.anchors.mkdir(parents=True, exist_ok=True)
        with self._lock():
            if any(p.exists() for p in (self.marker, self.anchor, self.db)):
                raise AcceptanceDenied("run_already_registered")
            # Tombstone first: a crash at any later point requires review, not reset.
            with self.marker.open("xb") as stream:
                stream.write(canonical({"mode": self.mode, "policy": sha(policy_record())}).encode())
                stream.flush(); os.fsync(stream.fileno())
            with closing(sqlite3.connect(self.db)) as db:
                db.execute("PRAGMA synchronous=FULL")
                db.execute("CREATE TABLE events(seq INTEGER PRIMARY KEY, data TEXT NOT NULL)")
                db.execute("CREATE TRIGGER no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'append_only'); END")
                db.execute("CREATE TRIGGER no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'append_only'); END")
                db.execute("INSERT INTO events VALUES(1,?)", (canonical({"type": "init", "mode": self.mode, "policy": policy_record()}),))
                db.commit()
                self._write_anchor(self._events(db))

    @staticmethod
    def _events(db):
        return [json.loads(row[0]) for row in db.execute("SELECT data FROM events ORDER BY seq")]

    def _write_anchor(self, events):
        temp = self.anchor.with_suffix(".pending")
        with temp.open("wb") as stream:
            stream.write(canonical({"count": len(events), "sha256": sha(events)}).encode())
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temp, self.anchor)

    @contextmanager
    def _transaction(self):
        with self._lock():
            if not all(p.is_file() for p in (self.marker, self.anchor, self.db)):
                raise AcceptanceDenied("budget_state_missing")
            try:
                marker = json.loads(self.marker.read_bytes())
                if marker != {"mode": self.mode, "policy": sha(policy_record())}:
                    raise AcceptanceDenied("budget_policy_changed")
                # mode=rw never creates a missing DB.
                with closing(sqlite3.connect(self.db.as_uri() + "?mode=rw", uri=True)) as db:
                    db.execute("PRAGMA synchronous=FULL")
                    db.execute("BEGIN IMMEDIATE")
                    events = self._events(db)
                    if json.loads(self.anchor.read_bytes()) != {"count": len(events), "sha256": sha(events)}:
                        raise AcceptanceDenied("budget_integrity_failure")
                    before = len(events)
                    yield db, events
                    if len(events) != before:
                        for n in range(before, len(events)):
                            db.execute("INSERT INTO events VALUES(?,?)", (n + 1, canonical(events[n])))
                        db.commit()
                        self._write_anchor(events)
            except AcceptanceDenied:
                raise
            except Exception:
                raise AcceptanceDenied("budget_integrity_failure") from None

    @staticmethod
    def _state(events):
        reserves = {e["number"]: e for e in events if e["type"] == "reserve"}
        finishes = {e["number"]: e for e in events if e["type"] == "finish"}
        tokens = fees = 0
        usage = {"input_miss": 0, "input_hit": 0, "output": 0}
        for number, r in reserves.items():
            f = finishes.get(number)
            tokens += f["charged_tokens"] if f else r["reserved_tokens"]
            fees += f["charged_fee"] if f else r["reserved_fee"]
            if f and f["usage"]:
                for k in usage: usage[k] += f["usage"][k]
        closed = {e['batch'] for e in events if e['type'] == 'close_batch'}
        batch_usage = {}
        for batch in BATCHES:
            selected = [r for r in reserves.values() if r['batch'] == batch]
            batch_usage[batch] = {
                'requests': len(selected), 'questions': len({r['case_id'] for r in selected}),
                'tokens': sum(finishes[r['number']]['charged_tokens'] if r['number'] in finishes else r['reserved_tokens'] for r in selected),
                'fee_nano_usd': sum(finishes[r['number']]['charged_fee'] if r['number'] in finishes else r['reserved_fee'] for r in selected)}
        return {"requests": len(reserves), "questions": len({e["case_id"] for e in reserves.values()}),
                "tokens_committed": tokens, "fee_committed_nano_usd": fees,
                "measured_usage": usage, "active": sorted(set(reserves) - set(finishes)),
                "stopped": any(e["type"] == "stop" for e in events),
                "authorized_batches": [e["batch"] for e in events if e["type"] == "authorize" and e['batch'] not in closed],
                'closed_batches': sorted(closed), 'batch_usage': batch_usage,
                'batch_limits': {e['batch']: e['limits'] for e in events if e['type'] == 'batch_limits'},
                "reports": {e["batch"]: e["report_sha256"] for e in events if e["type"] == "report"},
                "usage_unknown_requests": sum(e["usage"] is None for e in finishes.values())}

    def snapshot(self):
        with self._transaction() as (_, events):
            return self._state(events)

    def restrict_first_batch(self):
        """Append the new authorization cap; never rewrite the original policy/events."""
        limits = {'questions': 2, 'requests': 4, 'tokens': 80_000, 'fee_nano_usd': 60_000_000}
        with self._transaction() as (_, events):
            state = self._state(events)
            existing = state['batch_limits'].get(1)
            if existing is not None:
                if existing != limits: raise AcceptanceDenied('batch_policy_changed')
                return
            used = state['batch_usage'][1]
            if any(used[k] > v for k, v in limits.items()):
                raise AcceptanceDenied('existing_batch_budget_exceeded')
            events.append({'type': 'batch_limits', 'batch': 1, 'limits': limits})

    def close_batch(self, batch):
        """Revoke dispatch authority persistently, without refunding any reservation."""
        if type(batch) is not int or batch not in BATCHES:
            raise AcceptanceDenied('invalid_batch')
        with self._transaction() as (_, events):
            if batch not in self._state(events)['closed_batches']:
                events.append({'type': 'close_batch', 'batch': batch})

    def confirm_unchanged_prices(self, checked_on, peak, off_peak, reference_hash):
        """Private operator records a fresh official lookup, without budget reset.

        A rate change needs explicit review/migration, not an automatic cheaper
        tariff. This method is not exposed by CLI or web in this Mock stage.
        """
        if (checked_on != date.today().isoformat() or peak != PEAK or off_peak != OFF_PEAK
                or not isinstance(reference_hash,str) or len(reference_hash)!=64):
            raise AcceptanceDenied('price_reconfirmation_required')
        with self._transaction() as (_, events):
            events.append({'type':'price_confirmation','checked_on':checked_on,
                           'reference_sha256':reference_hash,'peak':peak,'off_peak':off_peak})

    def ensure_price_current(self, today=None):
        with self._transaction() as (_, events):
            confirmations=[e['checked_on'] for e in events if e['type']=='price_confirmation']
            if (confirmations[-1] if confirmations else PRICE_CHECKED_ON)!=(today or date.today()).isoformat():
                raise AcceptanceDenied('price_reconfirmation_required')

    def authorize(self, batch, approval_reference):
        """Private operator action. Hash only; never inferred from a test pass.

        This is an authorization record, not proof a human has approved. A live
        CLI is intentionally absent this stage. Future operator must verify the
        actual user instruction before invoking this method.
        """
        if type(batch) is not int or batch not in BATCHES or not isinstance(approval_reference, str) or len(approval_reference) < 12:
            raise AcceptanceDenied("explicit_batch_approval_required")
        with self._transaction() as (_, events):
            s = self._state(events)
            if batch in s['closed_batches']:
                raise AcceptanceDenied('batch_closed')
            if self.mode == 'live' and batch == 1 and batch not in s['batch_limits']:
                raise AcceptanceDenied('batch_limits_required')
            if batch in s["authorized_batches"]:
                raise AcceptanceDenied("batch_already_authorized")
            if s["stopped"] or (batch == 2 and 1 not in s["reports"]):
                raise AcceptanceDenied("first_batch_report_and_approval_required")
            events.append({"type": "authorize", "batch": batch, "reference_sha256": sha(approval_reference)})

    def reserve(self, case_id, phase, input_tokens, wire_hash):
        if case_id not in sum(BATCHES.values(), ()) or phase not in MAX_OUTPUT or type(input_tokens) is not int or not 0 < input_tokens <= MAX_INPUT:
            raise AcceptanceDenied("invalid_reservation")
        if not isinstance(wire_hash, str) or len(wire_hash) != 64 or any(c not in "0123456789abcdef" for c in wire_hash):
            raise AcceptanceDenied("invalid_wire_binding")
        batch = 1 if case_id in BATCHES[1] else 2
        output = MAX_OUTPUT[phase]
        with self._transaction() as (_, events):
            s = self._state(events)
            if s["stopped"]: raise AcceptanceDenied("run_stopped")
            if batch in s['closed_batches']: raise AcceptanceDenied('batch_closed')
            if batch not in s["authorized_batches"]: raise AcceptanceDenied("batch_not_authorized")
            if self.mode == 'live' and batch == 1 and batch not in s['batch_limits']:
                raise AcceptanceDenied('batch_limits_required')
            if s["active"]: raise AcceptanceDenied("request_in_progress")
            previous = [e for e in events if e["type"] == "reserve"]
            if any(e["case_id"] == case_id and e["phase"] == phase for e in previous):
                raise AcceptanceDenied("duplicate_attempt_no_retry")
            if phase == "reviewer" and not any(e["case_id"] == case_id and e["phase"] == "candidate" for e in previous):
                raise AcceptanceDenied("candidate_required")
            reserved_tokens, fee = input_tokens + output, input_tokens * PEAK['input_miss'] + output * PEAK['output']
            if s["requests"] >= MAX_REQUESTS or sum(e["batch"] == batch for e in previous) >= BATCH_REQUESTS[batch]:
                raise AcceptanceDenied("request_budget_exceeded")
            if len({e["case_id"] for e in previous} | {case_id}) > MAX_QUESTIONS:
                raise AcceptanceDenied("question_budget_exceeded")
            if s["tokens_committed"] + reserved_tokens > MAX_TOKENS:
                raise AcceptanceDenied("token_budget_exceeded")
            if s["fee_committed_nano_usd"] + fee > MAX_FEE_NANO_USD:
                raise AcceptanceDenied("fee_budget_exceeded")
            if batch in s['batch_limits']:
                used, cap = s['batch_usage'][batch], s['batch_limits'][batch]
                if used['requests'] + 1 > cap['requests'] or len({e['case_id'] for e in previous if e['batch'] == batch} | {case_id}) > cap['questions']:
                    raise AcceptanceDenied('request_budget_exceeded')
                if used['tokens'] + reserved_tokens > cap['tokens']:
                    raise AcceptanceDenied('token_budget_exceeded')
                if used['fee_nano_usd'] + fee > cap['fee_nano_usd']:
                    raise AcceptanceDenied('fee_budget_exceeded')
            number = s["requests"] + 1
            events.append({"type": "reserve", "number": number, "case_id": case_id, "batch": batch,
                           "phase": phase, "input": input_tokens, "output": output, "wire_hash": wire_hash,
                           "reserved_tokens": reserved_tokens, "reserved_fee": fee})
            return Reservation(case_id, phase, input_tokens, output, wire_hash, number, self)

    def check_permit(self, permit, wire_hash):
        if type(permit) is not Reservation or permit._issuer is not _ISSUER or permit._ledger is not self or permit.wire_hash != wire_hash:
            raise AcceptanceDenied("reserved_call_required")
        with self._transaction() as (_, events):
            matches = [e for e in events if e["type"] == "reserve" and e["number"] == permit.number]
            if (len(matches) != 1 or any(matches[0][k] != v for k, v in
                {"wire_hash": wire_hash, "case_id": permit.case_id, "phase": permit.phase,
                 "input": permit.input_tokens, "output": permit.max_output}.items())
                    or permit.number not in self._state(events)["active"]):
                raise AcceptanceDenied("invalid_or_consumed_permit")

    def claim_dispatch(self, permit, wire_hash):
        self.check_permit(permit, wire_hash)
        with self._transaction() as (_, events):
            self._check_send_authority(events, permit)
            if any(e["type"] == "dispatch" and e["number"] == permit.number for e in events):
                raise AcceptanceDenied("duplicate_dispatch_no_retry")
            events.append({"type": "dispatch", "number": permit.number})

    def claim_worker(self, permit, wire_hash):
        self.check_permit(permit, wire_hash)
        with self._transaction() as (_, events):
            self._check_send_authority(events, permit)
            if not any(e["type"] == "dispatch" and e["number"] == permit.number for e in events):
                raise AcceptanceDenied("dispatch_required")
            if any(e["type"] == "worker" and e["number"] == permit.number for e in events):
                raise AcceptanceDenied("duplicate_worker_no_retry")
            events.append({"type": "worker", "number": permit.number})

    def _check_send_authority(self, events, permit):
        state = self._state(events)
        batch = 1 if permit.case_id in BATCHES[1] else 2
        if state['stopped'] or batch not in state['authorized_batches']:
            raise AcceptanceDenied('batch_not_authorized')
        if self.mode == 'live' and batch == 1 and batch not in state['batch_limits']:
            raise AcceptanceDenied('batch_limits_required')

    def finish(self, permit, usage, result_code, http_status=None, latency=0):
        self.check_permit(permit, permit.wire_hash)
        # Only fixed safe metadata, never error bodies/prompt/model raw text.
        allowed = {"ok", "cancelled", "timeout", "http_failure", "redirect_blocked", "network_failure",
                   "schema_failure", "empty_content", "incomplete_response", "unsafe_response",
                   "internal_failure", "usage_unavailable", "worker_failure", "response_too_large", "not_configured"}
        if result_code not in allowed: result_code = "internal_failure"
        if type(http_status) is not int or not 100 <= http_status <= 599: http_status = None
        with self._transaction() as (_, events):
            s = self._state(events)
            if permit.number not in s["active"]: raise AcceptanceDenied("invalid_or_consumed_permit")
            known = type(usage) is Usage and usage.input_hit + usage.input_miss <= permit.input_tokens and usage.output <= permit.max_output
            if known:
                tokens, fee, record = usage.tokens, usage.fee, usage.record()
            else:
                tokens = permit.input_tokens + permit.max_output
                fee = permit.input_tokens * PEAK['input_miss'] + permit.max_output * PEAK['output']
                # An over-bound but internally consistent bill is real evidence,
                # not zero usage. Retain at least the reserve AND the reported bill.
                if type(usage) is Usage:
                    tokens, fee = max(tokens, usage.tokens), max(fee, usage.fee)
                    record = usage.record()
                else:
                    record = None
            events.append({"type": "finish", "number": permit.number, "usage": record,
                           "charged_tokens": tokens, "charged_fee": fee, "code": result_code,
                           "http_status": http_status, "latency_ms": max(0, min(int(latency * 1000), 3600000))})
            if not known:
                events.append({"type": "stop", "reason": "billing_unknown_or_exceeds_reservation"})

    def stop(self, reason):
        # Human/model text is never logged as the stop reason.
        allowed = {"safety_rejection", "billing_unknown_or_exceeds_reservation", "cancelled", "timeout", "input_changed", "transport_failure", "budget_exhausted"}
        with self._transaction() as (_, events):
            events.append({"type": "stop", "reason": reason if reason in allowed else "safety_rejection"})

    def record_batch_report(self, batch, report_hash):
        if batch not in BATCHES or not isinstance(report_hash, str) or len(report_hash) != 64:
            raise AcceptanceDenied("invalid_report")
        with self._transaction() as (_, events):
            s = self._state(events)
            if s["active"] or batch in s["reports"] or batch not in s["authorized_batches"]:
                raise AcceptanceDenied("report_not_allowed")
            attempted = {e["case_id"] for e in events if e["type"] == "reserve" and e["batch"] == batch}
            if attempted != set(BATCHES[batch]) and not s["stopped"]:
                raise AcceptanceDenied("batch_not_complete")
            events.append({"type": "report", "batch": batch, "report_sha256": report_hash})
