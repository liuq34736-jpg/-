"""Batch1 authorization extension: all budgets/dispatched calls are synthetic."""
from pathlib import Path
import json
import tempfile
import threading
import unittest
from unittest.mock import patch

from backend.ai_acceptance_v1.ledger import BudgetLedger
from backend.ai_acceptance_v1.policy import AcceptanceDenied, Usage, policy_record
from backend.ai_acceptance_v1.transport import TransportResult
from scripts.day8b2_batch1 import ConservativeCounter, AuditTransport


class BatchOneTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.ledger=BudgetLedger(self.root/'records',self.root/'anchors','mock')
        self.ledger.initialize(); self.ledger.restrict_first_batch()
        self.ledger.authorize(1,'SYNTHETIC_DAY8B2_BATCH1_AUTH')
    def tearDown(self): self.tmp.cleanup()
    def reserve(self,case='B01',phase='candidate',n=30000):
        return self.ledger.reserve(case,phase,n,'a'*64)
    def settle(self,permit,usage=None):
        self.ledger.finish(permit,usage if usage is not None else Usage(permit.input_tokens,0,permit.max_output),'ok')

    def test_caps_exact(self):
        self.assertEqual(self.ledger.snapshot()['batch_limits'][1],{'questions':2,'requests':4,'tokens':80000,'fee_nano_usd':60000000})
    def test_original_policy_not_replaced(self):
        self.assertEqual((policy_record()['tokens'],policy_record()['fee_nano_usd']),(250000,150000000))
    def test_existing_usage_not_reset(self):
        p=self.reserve(); self.settle(p); before=self.ledger.snapshot()
        self.ledger.restrict_first_batch(); self.assertEqual(before,self.ledger.snapshot())
    def test_restart_retains_batch_caps_and_usage(self):
        p=self.reserve(); self.settle(p)
        other=BudgetLedger(self.root/'records',self.root/'anchors','mock')
        self.assertEqual(other.snapshot(),self.ledger.snapshot())
    def test_batch_token_limit_before_third_dispatch(self):
        self.settle(self.reserve()); self.settle(self.reserve(phase='reviewer'))
        with self.assertRaisesRegex(AcceptanceDenied,'token_budget_exceeded'): self.reserve('B02')
        self.assertEqual(self.ledger.snapshot()['requests'],2)
    def test_fee_limit_before_reserve(self):
        original=self.ledger._state
        def near_limit(events):
            s=original(events); s['batch_usage'][1]['fee_nano_usd']=59_000_000
            return s
        with patch.object(self.ledger,'_state',near_limit):
            with self.assertRaisesRegex(AcceptanceDenied,'fee_budget_exceeded'): self.reserve(n=1000)
        self.assertEqual(self.ledger.snapshot()['requests'],0)
    def test_global_token_limit_is_also_applied(self):
        with patch('backend.ai_acceptance_v1.ledger.MAX_TOKENS',1000):
            with self.assertRaisesRegex(AcceptanceDenied,'token_budget_exceeded'): self.reserve()
    def test_global_fee_limit_is_also_applied(self):
        with patch('backend.ai_acceptance_v1.ledger.MAX_FEE_NANO_USD',1000):
            with self.assertRaisesRegex(AcceptanceDenied,'fee_budget_exceeded'): self.reserve()
    def test_unknown_usage_stays_charged_and_stops(self):
        p=self.reserve(); self.ledger.finish(p,None,'timeout')
        s=self.ledger.snapshot(); self.assertEqual(s['batch_usage'][1]['tokens'],34096)
        self.assertTrue(s['stopped']); self.assertEqual(s['usage_unknown_requests'],1)
    def test_unknown_usage_never_zero_fee(self):
        p=self.reserve(); self.ledger.finish(p,None,'network_failure')
        self.assertEqual(self.ledger.snapshot()['batch_usage'][1]['fee_nano_usd'],13915200)
    def test_single_atomic_active_request(self):
        successes=[]
        def reserve(case):
            try: self.reserve(case); successes.append(case)
            except AcceptanceDenied: pass
        threads=[threading.Thread(target=reserve,args=(c,)) for c in ('B01','B02')]
        [t.start() for t in threads]; [t.join() for t in threads]
        self.assertEqual(len(successes),1); self.assertEqual(self.ledger.snapshot()['requests'],1)
    def test_closure_no_refund(self):
        p=self.reserve(); self.settle(p); s=self.ledger.snapshot()
        self.ledger.close_batch(1); after=self.ledger.snapshot()
        self.assertEqual(after['batch_usage'],s['batch_usage']); self.assertEqual(after['authorized_batches'],[])
    def test_closure_persists_after_restart(self):
        self.ledger.close_batch(1)
        other=BudgetLedger(self.root/'records',self.root/'anchors','mock')
        with self.assertRaisesRegex(AcceptanceDenied,'batch_closed'): other.reserve('B01','candidate',1000,'a'*64)
    def test_closure_refuses_reauthorization(self):
        self.ledger.close_batch(1)
        with self.assertRaisesRegex(AcceptanceDenied,'batch_closed'): self.ledger.authorize(1,'SYNTHETIC_NEW_AUTH_NOT_ALLOWED')
    def test_closed_reserved_permit_cannot_dispatch(self):
        p=self.reserve(); self.ledger.close_batch(1)
        with self.assertRaises(AcceptanceDenied): self.ledger.claim_dispatch(p,'a'*64)
        self.assertEqual(self.ledger.snapshot()['active'],[1])
    def test_closed_dispatched_permit_cannot_start_http_worker(self):
        p=self.reserve(); self.ledger.claim_dispatch(p,'a'*64); self.ledger.close_batch(1)
        with self.assertRaises(AcceptanceDenied): self.ledger.claim_worker(p,'a'*64)
    def test_closure_does_not_authorize_batch_two(self):
        self.ledger.close_batch(1)
        with self.assertRaises(AcceptanceDenied): self.reserve('B03')
    def test_live_authorization_requires_cap_event(self):
        live=BudgetLedger(self.root/'live',self.root/'live-anchor','live'); live.initialize()
        with self.assertRaisesRegex(AcceptanceDenied,'batch_limits_required'): live.authorize(1,'SYNTHETIC_LIVE_TEST_NO_HTTP')
    def test_cap_registration_preserves_marker_policy(self):
        marker=self.ledger.marker.read_bytes(); self.ledger.restrict_first_batch()
        self.assertEqual(marker,self.ledger.marker.read_bytes())
    def test_deleted_budget_is_not_reinitialized(self):
        self.ledger.db.unlink()
        with self.assertRaises(AcceptanceDenied): self.ledger.initialize()
        with self.assertRaises(AcceptanceDenied): self.ledger.restrict_first_batch()
    def test_full_envelope_reserved(self):
        with patch('scripts.day8b2_batch1.OfficialTokenCounter') as official:
            official.return_value.reserve_input.return_value=14592
            self.assertEqual(ConservativeCounter().reserve_input([]),30000)
    def test_oversized_source_is_rejected_not_truncated(self):
        with patch('scripts.day8b2_batch1.OfficialTokenCounter') as official:
            official.return_value.reserve_input.return_value=30001
            with self.assertRaises(AcceptanceDenied): ConservativeCounter().reserve_input([])
    def test_redacted_audit_excludes_unknown_keys(self):
        class Inner:
            ledger=self.ledger
            def perform(inner,p,w,c): return TransportResult('ok',200,json.dumps({'raw_secret':'SYNTHETIC',
                'claims':[{'role':'moving_line','analogy_text':'合成有限解释','raw_headers':'SYNTHETIC'}]}))
        p=self.reserve(); wrapper=AuditTransport(Inner(),self.root/'audit')
        wrapper.perform(p,{},threading.Event())
        data=(self.root/'audit/B01_candidate_fragments.json').read_text(encoding='utf-8')
        self.assertNotIn('raw_secret',data); self.assertNotIn('raw_headers',data)
    def test_unsafe_fragment_not_persisted(self):
        class Inner:
            ledger=self.ledger
            def perform(inner,p,w,c): return TransportResult('ok',200,json.dumps({'claims':[{'analogy_text':'Bearer synthetic-text'}]}))
        AuditTransport(Inner(),self.root/'audit').perform(self.reserve(),{},threading.Event())
        value=json.loads((self.root/'audit/B01_candidate_fragments.json').read_bytes())
        self.assertEqual(value['code'],'unsafe_fragment_excluded'); self.assertNotIn('claims',value)
    def test_no_connectivity_diagnostic_or_retry_in_operator(self):
        import inspect
        import scripts.day8b2_batch1 as module
        code=inspect.getsource(module.run_one)
        self.assertNotIn('check_connection',code); self.assertNotIn('run_batch',code)
        self.assertEqual(code.count('.run_case('),1)
