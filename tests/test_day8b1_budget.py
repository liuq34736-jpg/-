"""All private test state uses temporary directories; no real HTTP or key reads."""
from dataclasses import replace
from contextlib import closing
from datetime import date
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch

from backend.ai_acceptance_v1.policy import (AcceptanceDenied, Usage, PEAK, OFF_PEAK,
    MAX_OUTPUT, require_fresh_price, sha, canonical)
from backend.ai_acceptance_v1.ledger import BudgetLedger, Reservation
from backend.ai_acceptance_v1.transport import ProcessTransport, http_once
from backend.ai_acceptance_v1.prompts import wire_for
from backend.app.deepseek import DeepSeekConfig
from tests.day8b1_fixtures import reply


class LedgerBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.ledger = BudgetLedger(self.root/'records', self.root/'anchors', 'mock')
        self.ledger.initialize(); self.ledger.authorize(1, 'TEST_ONLY_MOCK_AUTHORIZATION')
    def tearDown(self): self.tmp.cleanup()
    def reserve(self, case='B01', phase='candidate', n=1000):
        return self.ledger.reserve(case, phase, n, 'a'*64)
    def finish(self, p, usage=Usage(100, 50, 50)):
        self.ledger.finish(p, usage, 'ok')
    def second(self):
        for case in ('B01','B02'):
            p=self.reserve(case); self.finish(p)
        self.ledger.record_batch_report(1, 'b'*64)
        self.ledger.authorize(2, 'TEST_ONLY_SECOND_BATCH_APPROVAL')


class LedgerTests(LedgerBase):
    def test_fixed_caps(self):
        from backend.ai_acceptance_v1.policy import policy_record
        p=policy_record(); self.assertEqual((p['questions'],p['requests'],p['tokens'],p['fee_nano_usd']), (6,12,250000,150000000))
    def test_prices_peak_and_off_peak(self):
        self.assertEqual(PEAK, {'input_miss':300,'input_hit':6,'output':1200})
        self.assertEqual(OFF_PEAK, {'input_miss':150,'input_hit':3,'output':600})
    def test_price_reconfirmation(self):
        require_fresh_price(date(2026,10,12))
        with self.assertRaisesRegex(AcceptanceDenied,'price_reconfirmation'): require_fresh_price(date(2026,10,13))
    def test_usage_split_and_fee(self):
        u=Usage.parse(reply('x')['usage']); self.assertEqual(u.record(), {'input_miss':100,'input_hit':50,'output':50,'tokens':200,'fee_nano_usd':90300})
    def test_usage_unknown_missing_cache_count(self):
        raw=reply('x')['usage']; del raw['prompt_cache_hit_tokens']
        with self.assertRaises(AcceptanceDenied): Usage.parse(raw)
    def test_usage_inconsistent(self):
        raw=reply('x')['usage']; raw['total_tokens']=1
        with self.assertRaises(AcceptanceDenied): Usage.parse(raw)
    def test_usage_bool_not_integer(self):
        with self.assertRaises(AcceptanceDenied): Usage(True,0,0)
    def test_usage_negative(self):
        with self.assertRaises(AcceptanceDenied): Usage(-1,0,0)
    def test_input_maximum(self):
        for n in (True,0,30001,-1):
            with self.subTest(n=n), self.assertRaises(AcceptanceDenied): self.reserve(n=n)
    def test_output_fixed(self):
        p=self.reserve(); self.assertEqual(p.max_output,4096)
        self.finish(p); p=self.reserve(phase='reviewer'); self.assertEqual(p.max_output,3072)
    def test_conservative_reservation(self):
        p=self.reserve(); s=self.ledger.snapshot()
        self.assertEqual(s['tokens_committed'],5096); self.assertEqual(s['fee_committed_nano_usd'],1000*300+4096*1200)
    def test_known_usage_releases_only_difference(self):
        p=self.reserve(); self.finish(p); s=self.ledger.snapshot()
        self.assertEqual(s['tokens_committed'],200); self.assertEqual(s['fee_committed_nano_usd'],90300)
        self.assertEqual(s['measured_usage'], {'input_miss':100,'input_hit':50,'output':50})
    def test_unknown_usage_keeps_full_reservation_and_stops(self):
        p=self.reserve(); self.finish(p,None); s=self.ledger.snapshot()
        self.assertEqual(s['tokens_committed'],5096); self.assertTrue(s['stopped']); self.assertEqual(s['requests'],1)
        with self.assertRaisesRegex(AcceptanceDenied,'run_stopped'): self.reserve('B02')
    def test_over_reservation_stops(self):
        p=self.reserve(); self.finish(p,Usage(1001,0,50)); self.assertTrue(self.ledger.snapshot()['stopped'])
    def test_duplicate_attempt_rejected(self):
        p=self.reserve(); self.finish(p)
        with self.assertRaisesRegex(AcceptanceDenied,'duplicate'): self.reserve()
    def test_reviewer_requires_candidate(self):
        with self.assertRaisesRegex(AcceptanceDenied,'candidate_required'): self.reserve(phase='reviewer')
    def test_active_slot_blocks_second_caller(self):
        self.reserve()
        with self.assertRaisesRegex(AcceptanceDenied,'request_in_progress'): self.reserve('B02')
    def test_atomic_race(self):
        results=[]
        def run(case):
            try: self.reserve(case); results.append('reserved')
            except AcceptanceDenied as e: results.append(str(e))
        threads=[threading.Thread(target=run,args=(c,)) for c in ('B01','B02')]
        [t.start() for t in threads]; [t.join() for t in threads]
        self.assertEqual(results.count('reserved'),1); self.assertEqual(self.ledger.snapshot()['requests'],1)
    def test_restart_retains_usage(self):
        p=self.reserve(); self.finish(p)
        other=BudgetLedger(self.root/'records',self.root/'anchors','mock')
        self.assertEqual(other.snapshot(),self.ledger.snapshot())
    def test_crash_active_reservation_is_not_free(self):
        self.reserve(); other=BudgetLedger(self.root/'records',self.root/'anchors','mock')
        self.assertEqual(other.snapshot()['tokens_committed'],5096)
        with self.assertRaisesRegex(AcceptanceDenied,'request_in_progress'): other.reserve('B02','candidate',1000,'a'*64)
    def test_no_auto_bootstrap(self):
        other=BudgetLedger(self.root/'other',self.root/'other-anchor','mock')
        with self.assertRaises(AcceptanceDenied): other.snapshot()
    def test_delete_database_no_reset(self):
        self.ledger.db.unlink()
        with self.assertRaises(AcceptanceDenied): self.ledger.snapshot()
        with self.assertRaisesRegex(AcceptanceDenied,'registered'): self.ledger.initialize()
    def test_delete_anchor_no_reset(self):
        self.ledger.anchor.unlink()
        with self.assertRaises(AcceptanceDenied): self.ledger.snapshot()
        with self.assertRaises(AcceptanceDenied): self.ledger.initialize()
    def test_delete_records_and_anchor_marker_retains_tombstone(self):
        self.ledger.db.unlink(); self.ledger.anchor.unlink()
        with self.assertRaises(AcceptanceDenied): self.ledger.initialize()
    def test_append_only_sql(self):
        with closing(sqlite3.connect(self.ledger.db)) as c:
            for sql in ('DELETE FROM events','UPDATE events SET data=\'{}\''):
                with self.assertRaises(sqlite3.IntegrityError): c.execute(sql)
    def test_tamper_appended_row_fails_anchor(self):
        with closing(sqlite3.connect(self.ledger.db)) as c:
            c.execute("INSERT INTO events VALUES(999,'{}')"); c.commit()
        with self.assertRaisesRegex(AcceptanceDenied,'integrity'): self.ledger.snapshot()
    def test_stale_anchor_detected(self):
        old=self.ledger.anchor.read_bytes(); p=self.reserve(); self.finish(p); self.ledger.anchor.write_bytes(old)
        with self.assertRaises(AcceptanceDenied): self.ledger.snapshot()
    def test_marker_tamper(self):
        self.ledger.marker.write_text('{}')
        with self.assertRaises(AcceptanceDenied): self.ledger.snapshot()
    def test_second_batch_requires_report(self):
        with self.assertRaises(AcceptanceDenied): self.ledger.authorize(2,'TEST_ONLY_AUTHORIZED_SECOND')
    def test_report_not_automatic_approval(self):
        for c in ('B01','B02'): self.finish(self.reserve(c))
        self.ledger.record_batch_report(1,'b'*64)
        with self.assertRaisesRegex(AcceptanceDenied,'batch_not_authorized'): self.reserve('B03')
    def test_second_batch_explicit_approval(self):
        self.second(); self.finish(self.reserve('B03')); self.assertEqual(self.ledger.snapshot()['questions'],3)
    def test_unknown_case_rejected(self):
        with self.assertRaises(AcceptanceDenied): self.reserve('USER_REAL_CASE')
    def test_early_report_rejected(self):
        with self.assertRaises(AcceptanceDenied): self.ledger.record_batch_report(1,'b'*64)
    def test_token_cap_rejection(self):
        self.second()
        for c in ('B03','B04','B05'):
            for phase in MAX_OUTPUT:
                p=self.reserve(c,phase,30000); self.finish(p,Usage(30000,0,MAX_OUTPUT[phase]))
        p=self.reserve('B06','candidate',30000); self.finish(p,Usage(30000,0,4096))
        with self.assertRaisesRegex(AcceptanceDenied,'token_budget'): self.reserve('B06','reviewer',30000)
    def test_fee_cap_rejection(self):
        with patch('backend.ai_acceptance_v1.ledger.MAX_FEE_NANO_USD',100):
            with self.assertRaisesRegex(AcceptanceDenied,'fee_budget'): self.reserve()
    def test_request_cap_rejection(self):
        with patch('backend.ai_acceptance_v1.ledger.MAX_REQUESTS',0):
            with self.assertRaisesRegex(AcceptanceDenied,'request_budget'): self.reserve()
    def test_question_cap_rejection(self):
        with patch('backend.ai_acceptance_v1.ledger.MAX_QUESTIONS',0):
            with self.assertRaisesRegex(AcceptanceDenied,'question_budget'): self.reserve()
    def test_per_batch_request_cap(self):
        with patch.dict('backend.ai_acceptance_v1.ledger.BATCH_REQUESTS',{1:0}):
            with self.assertRaisesRegex(AcceptanceDenied,'request_budget'): self.reserve()
    def test_no_double_settlement(self):
        p=self.reserve(); self.finish(p)
        with self.assertRaises(AcceptanceDenied): self.finish(p)
    def test_changed_permit_rejected(self):
        p=self.reserve()
        with self.assertRaises(AcceptanceDenied): self.ledger.check_permit(replace(p,max_output=100000),'a'*64)
    def test_duplicate_dispatch_rejected(self):
        p=self.reserve(); self.ledger.claim_dispatch(p,'a'*64)
        with self.assertRaises(AcceptanceDenied): self.ledger.claim_dispatch(p,'a'*64)
    def test_worker_cannot_skip_dispatch(self):
        p=self.reserve()
        with self.assertRaises(AcceptanceDenied): self.ledger.claim_worker(p,'a'*64)
    def test_worker_cannot_repeat(self):
        p=self.reserve(); self.ledger.claim_dispatch(p,'a'*64); self.ledger.claim_worker(p,'a'*64)
        with self.assertRaises(AcceptanceDenied): self.ledger.claim_worker(p,'a'*64)
    def test_live_mock_ledger_isolation(self):
        live=BudgetLedger(self.root/'records',self.root/'anchors','live'); live.initialize()
        with self.assertRaisesRegex(AcceptanceDenied,'batch_not_authorized'): live.reserve('B01','candidate',1000,'a'*64)
    def test_separate_anchor_required(self):
        with self.assertRaises(AcceptanceDenied): BudgetLedger(self.root,self.root/'sub','mock')

    def test_stale_price_blocks_without_budget_reset(self):
        self.finish(self.reserve()); before=self.ledger.snapshot()
        with self.assertRaises(AcceptanceDenied): self.ledger.ensure_price_current(date(2026,10,13))
        self.assertEqual(self.ledger.snapshot(),before)
    def test_price_reattestation_preserves_both_batch_counters(self):
        self.second(); self.finish(self.reserve('B03')); before=self.ledger.snapshot()
        self.ledger.confirm_unchanged_prices(date.today().isoformat(),PEAK,OFF_PEAK,'c'*64)
        self.ledger.ensure_price_current(); self.assertEqual(self.ledger.snapshot(),before)
    def test_changed_price_is_not_silently_accepted(self):
        with self.assertRaises(AcceptanceDenied): self.ledger.confirm_unchanged_prices(date.today().isoformat(),{'input_miss':1},OFF_PEAK,'c'*64)


class TransportTests(LedgerBase):
    def make(self, response, deadline=22):
        wire=wire_for([{'role':'user','content':'SYNTHETIC'}],'candidate')
        p=self.ledger.reserve('B01','candidate',1000,sha(wire))
        transport=ProcessTransport(self.ledger,mock_replies={('B01','candidate'):response},deadline=deadline)
        return p,wire,transport
    def test_process_timeout_reaped_and_charged(self):
        p,w,t=self.make(reply('{}',delay=5),.2); r=t.perform(p,w,threading.Event())
        self.assertEqual(r.code,'timeout'); self.assertEqual((t.starts,t.reaped),(1,1))
        self.ledger.finish(p,r.usage,r.code); self.assertTrue(self.ledger.snapshot()['stopped']); self.assertEqual(self.ledger.snapshot()['active'],[])
    def test_process_cancel_reaped_and_charged(self):
        p,w,t=self.make(reply('{}',delay=5)); cancel=threading.Event(); timer=threading.Timer(.2,cancel.set); timer.start()
        r=t.perform(p,w,cancel); timer.join(); self.assertEqual(r.code,'cancelled'); self.assertEqual((t.starts,t.reaped),(1,1))
        self.ledger.finish(p,r.usage,r.code); self.assertEqual(self.ledger.snapshot()['requests'],1)
    def test_pre_cancel_counts_conservatively(self):
        p,w,t=self.make(reply('{}')); cancel=threading.Event(); cancel.set(); r=t.perform(p,w,cancel)
        self.assertEqual(r.code,'cancelled'); self.assertEqual(t.starts,0); self.ledger.finish(p,r.usage,r.code)
        self.assertEqual(self.ledger.snapshot()['requests'],1)
    def test_worker_exception_no_retry(self):
        p,w,t=self.make(reply('{}',raise_error=True)); r=t.perform(p,w,threading.Event())
        self.assertEqual(r.code,'worker_failure'); self.assertEqual((t.starts,t.reaped),(1,1))
    def test_mock_no_credential_lookup(self):
        p,w,t=self.make(reply('{}'))
        with patch('backend.ai_acceptance_v1.transport.load_config',side_effect=AssertionError('key_lookup_forbidden')):
            r=t.perform(p,w,threading.Event())
        self.assertEqual(r.code,'ok'); self.assertEqual(r.usage.tokens,200)
    def test_wire_tamper_before_transport_rejected(self):
        p,w,t=self.make(reply('{}')); w['max_tokens']=9999
        with self.assertRaises(AcceptanceDenied): t.perform(p,w,threading.Event())
        self.assertEqual(t.starts,0)


class HttpTests(unittest.TestCase):
    def config(self): return DeepSeekConfig(api_key='SYNTHETIC_SECRET_ONLY')
    def wire(self): return wire_for([{'role':'user','content':'synthetic'}],'candidate')
    def response(self, body, status=200):
        class Response:
            def __enter__(self): return self
            def __exit__(self,*a): pass
            def read(self,n): return body.encode()[:n]
        r=Response(); r.status=status; return r
    def envelope(self, content='{}', **changes):
        x={'choices':[{'finish_reason':'stop','message':{'content':content}}], 'usage':reply('x')['usage']}; x.update(changes); return canonical(x)
    def test_success_fixed_https_config(self):
        seen=[]
        def opener(req,timeout): seen.append((req.full_url,json.loads(req.data),timeout)); return self.response(self.envelope())
        r=http_once(self.wire(),self.config(),opener); self.assertEqual(r['code'],'ok')
        self.assertEqual(seen[0][0],'https://api.deepseek.com/chat/completions'); self.assertEqual(seen[0][1]['max_tokens'],4096)
    def test_302_rejected_once(self):
        calls=[]; r=http_once(self.wire(),self.config(),lambda *a,**k:(calls.append(1) or self.response('',302)))
        self.assertEqual(r['code'],'redirect_blocked'); self.assertEqual(len(calls),1)
    def test_307_rejected(self): self.assertEqual(http_once(self.wire(),self.config(),lambda *a,**k:self.response('',307))['code'],'redirect_blocked')
    def test_308_rejected(self): self.assertEqual(http_once(self.wire(),self.config(),lambda *a,**k:self.response('',308))['code'],'redirect_blocked')
    def test_403(self): self.assertEqual(http_once(self.wire(),self.config(),lambda *a,**k:self.response('',403))['code'],'http_failure')
    def test_500(self): self.assertEqual(http_once(self.wire(),self.config(),lambda *a,**k:self.response('',500))['code'],'http_failure')
    def test_502(self): self.assertEqual(http_once(self.wire(),self.config(),lambda *a,**k:self.response('',502))['code'],'http_failure')
    def test_empty_content(self): self.assertEqual(http_once(self.wire(),self.config(),lambda *a,**k:self.response(self.envelope('')))['code'],'empty_content')
    def test_non_json(self): self.assertEqual(http_once(self.wire(),self.config(),lambda *a,**k:self.response('not json'))['code'],'schema_failure')
    def test_no_key_in_failure_result(self):
        def opener(*a,**k): raise RuntimeError('SYNTHETIC_SECRET_ONLY Authorization')
        r=http_once(self.wire(),self.config(),opener); self.assertNotIn('SECRET',canonical(r)); self.assertNotIn('Authorization',canonical(r))
    def test_key_echo_not_returned(self):
        r=http_once(self.wire(),self.config(),lambda *a,**k:self.response(self.envelope('SYNTHETIC_SECRET_ONLY')))
        self.assertEqual(r['code'],'unsafe_response'); self.assertNotIn('content',r)
    def test_finish_reason_length(self):
        body=self.envelope(); body=body.replace('"stop"','"length"')
        self.assertEqual(http_once(self.wire(),self.config(),lambda *a,**k:self.response(body))['code'],'incomplete_response')
    def test_duplicate_json(self):
        self.assertEqual(http_once(self.wire(),self.config(),lambda *a,**k:self.response('{"choices":[],"choices":[]}'))['code'],'schema_failure')
    def test_timeout_once(self):
        calls=[]
        def opener(*a,**k): calls.append(1); raise TimeoutError('sensitive')
        self.assertEqual(http_once(self.wire(),self.config(),opener)['code'],'network_failure'); self.assertEqual(len(calls),1)
    def test_nonfixed_model_rejected_without_http(self):
        r=http_once(self.wire(),replace(self.config(),model_name='other'),lambda *a,**k:self.fail('HTTP forbidden')); self.assertEqual(r['code'],'internal_failure')
