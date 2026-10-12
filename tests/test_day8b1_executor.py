"""Full frozen/approved input + application-gate regression, never live API."""
from dataclasses import replace
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from backend.app.meihua_models import ManualInput
from backend.traditional_judgement_v1.trusted_input import OfflineJudgementAdapter
from backend.question_quality_v1.contract import (ApplicationDraft, build_request, limit_ids, validate_draft)
from backend.ai_acceptance_v1.executor import AcceptanceExecutor
from backend.ai_acceptance_v1.ledger import BudgetLedger
from backend.ai_acceptance_v1.policy import AcceptanceDenied, Usage, canonical, sha
from backend.ai_acceptance_v1.prompts import OfficialTokenCounter, messages_for, wire_for
from backend.ai_acceptance_v1.transport import ProcessTransport, TransportResult
from scripts.day8b_prepare import CASES, CAST_AT
from tests.day8b1_fixtures import draft_for, verdict_for, replies_for, reply

ROOT = Path(__file__).resolve().parents[1]


class FixedCounter:
    def reserve_input(self, messages): return 1000


class MemoryTransport:
    """In-process deterministic protocol double; no config/socket facility."""
    def __init__(self, ledger, replies): self.ledger,self.replies,self.calls=ledger,replies,[]
    def perform(self, permit, wire, cancel):
        self.ledger.claim_dispatch(permit,sha(wire)); self.calls.append((permit.case_id,permit.phase))
        value=self.replies[(permit.case_id,permit.phase)]
        try: usage=Usage.parse(value.get('usage'))
        except AcceptanceDenied: usage=None
        return TransportResult(value['code'],value.get('http_status'),value.get('content'),usage,.001)


class ExecutorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        inputs=OfflineJudgementAdapter().calculate_batch([ManualInput(input_mode='manual_hexagram',
            hexagram_id=c['hexagram_id'],moving_line=c['moving_line'],cast_at=CAST_AT,question_text=c['question']) for c in CASES])
        cls.requests={c['case_id']:build_request(x) for c,x in zip(CASES,inputs)}
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.ledger=BudgetLedger(self.root/'records',self.root/'anchors','mock'); self.ledger.initialize()
        self.ledger.authorize(1,'TEST_ONLY_MOCK_BATCH_ONE')
        self.replies=replies_for(self.requests); self.transport=MemoryTransport(self.ledger,self.replies)
        self.engine=AcceptanceExecutor(self.ledger,self.transport,FixedCounter())
    def tearDown(self): self.tmp.cleanup()
    def evaluate(self, case='B01'): return self.engine.run_case(case,self.requests[case])
    def mutate(self, fn, phase='candidate', case='B01'):
        d=draft_for(case,self.requests[case])
        if phase=='candidate': raw=d.model_dump()
        else: raw=verdict_for(self.requests[case],d).model_dump()
        fn(raw); self.replies[(case,phase)]=reply(canonical(raw))
    def second(self):
        self.engine.run_batch(1,{c:self.requests[c] for c in ('B01','B02')},self.root/'first.json')
        self.ledger.authorize(2,'TEST_ONLY_EXPLICIT_SECOND_BATCH')
    def test_six_fixtures_keep_current_gates(self):
        for c,r in self.requests.items():
            with self.subTest(case=c): self.assertEqual(validate_draft(r,draft_for(c,r)),['question_or_goal_as_fact'] if c=='B06' else [])
    def test_first_batch_report_two_questions_four_requests(self):
        report=self.engine.run_batch(1,{c:self.requests[c] for c in ('B01','B02')},self.root/'first.json')
        self.assertEqual(report['budget']['requests'],4); self.assertEqual(report['budget']['questions'],2)
        self.assertTrue(all(r['status']=='MOCK_CONTRACT_ACCEPTED' for r in report['cases']))
        self.assertEqual(report['real_ai_calls'],0); self.assertIn(1,self.ledger.snapshot()['reports'])
    def test_second_batch_not_authorized_by_first_report(self):
        self.engine.run_batch(1,{c:self.requests[c] for c in ('B01','B02')},self.root/'first.json')
        with self.assertRaises(AcceptanceDenied): self.engine.run_batch(2,{c:self.requests[c] for c in ('B03','B04','B05','B06')},self.root/'second.json')
        self.assertEqual(len(self.transport.calls),4)
    def test_simulated_second_shares_twelve_request_budget(self):
        self.second(); report=self.engine.run_batch(2,{c:self.requests[c] for c in ('B03','B04','B05','B06')},self.root/'second.json')
        self.assertEqual(report['budget']['requests'],11); self.assertEqual(report['budget']['questions'],6)
        self.assertEqual([r['status'] for r in report['cases']],['MOCK_CONTRACT_ACCEPTED']*3+['BASE_FALLBACK'])
    def test_live_default_no_call_or_config_lookup(self):
        live=BudgetLedger(self.root/'live-records',self.root/'live-anchors','live'); live.initialize()
        provider=ProcessTransport(live)
        engine=AcceptanceExecutor(live,provider,FixedCounter())
        with patch('backend.ai_acceptance_v1.transport.load_config',side_effect=AssertionError('no_key')):
            with self.assertRaises(AcceptanceDenied): engine.run_batch(1,{c:self.requests[c] for c in ('B01','B02')},self.root/'live.json')
        self.assertEqual(provider.starts,0)
    def test_blank_or_arbitrary_question_cannot_be_added(self):
        with self.assertRaises(AcceptanceDenied): self.engine.run_case('B07',self.requests['B01'])
        self.assertEqual(len(self.transport.calls),0)
    def test_wrong_case_binding(self):
        with self.assertRaises(AcceptanceDenied): self.engine.run_case('B01',self.requests['B02'])
    def test_arbitrary_dict_request_rejected(self):
        with self.assertRaises(AcceptanceDenied): self.engine.run_case('B01',self.requests['B01'].checked())
    def test_input_calculation_frames_qualifications_unchanged(self):
        before=sha(self.requests['B01'].checked()); result=self.evaluate()
        self.assertEqual(before,sha(self.requests['B01'].checked())); self.assertTrue(result.checks['facts_unchanged'])
    def test_accepted_is_not_production_or_history_approval(self):
        r=self.evaluate(); self.assertFalse(r.production_approved or r.history_written)
        self.assertEqual(r.checks['real_model_quality'],'unverified')
    def test_each_claim_retains_evidence_and_all_limits(self):
        r=self.evaluate(); self.assertEqual(len(r.checks['binding_evidence']),4)
        for e in r.checks['binding_evidence']:
            self.assertTrue(e['source_evidence_ids']); self.assertEqual(set(e['limit_ids']),set(limit_ids(self.requests['B01'].checked(),e['role'])))
    def test_reviewer_uses_full_source_and_actual_draft(self):
        request=self.requests['B01']; draft=draft_for('B01',request); msgs=messages_for(request,'reviewer',draft)
        from backend.app.deepseek import strict_json
        payload=strict_json(msgs[1]['content']); self.assertEqual(payload['draft'],draft.model_dump())
        self.assertNotIn('draft_for_sizing_only',payload)
        self.assertEqual(payload['context']['evidence'],request.checked()['evidence'])
    def test_wire_has_fixed_model_and_outputs(self):
        for phase in ('candidate','reviewer'):
            w=wire_for([{'role':'user','content':'synthetic'}],phase)
            self.assertEqual(w['model'],'deepseek-flash'); self.assertFalse(w['stream']); self.assertEqual(w['max_tokens'],4096 if phase=='candidate' else 3072)
    def test_prompt_defensive_copy(self):
        request=self.requests['B01']; before=sha(request.checked()); msgs=messages_for(request,'candidate'); msgs[1]['content']='changed'
        self.assertEqual(sha(request.checked()),before)
    def test_non_json_fallback_no_review_or_retry(self):
        self.replies[('B01','candidate')]=reply('not json'); r=self.evaluate()
        self.assertEqual(r.status,'BASE_FALLBACK'); self.assertEqual(len(self.transport.calls),1)
    def test_extra_fields_rejected(self):
        self.mutate(lambda x:x.update(prediction='extra')); r=self.evaluate()
        self.assertEqual(r.status,'BASE_FALLBACK'); self.assertEqual(len(self.transport.calls),1)
    def test_wrong_frame_rejected_stops_batch(self):
        self.mutate(lambda x:x['claims'][0].update(frame_id='0'*64)); r=self.evaluate()
        self.assertIn('frame_binding',r.errors); self.assertTrue(self.ledger.snapshot()['stopped'])
    def test_omitted_condition_rejected_stops_batch(self):
        self.mutate(lambda x:x['claims'][1].update(preserved_limit_ids=[])); r=self.evaluate()
        self.assertIn('omitted_or_added_limits',r.errors); self.assertTrue(self.ledger.snapshot()['stopped'])
    def test_unprovided_fact_rejected(self):
        self.mutate(lambda x:x['claims'][0].update(analogy_text='你已经备货完成，所以可以开始推广并安排库存和租金。'))
        r=self.evaluate(); self.assertEqual(r.status,'BASE_FALLBACK'); self.assertTrue(self.ledger.snapshot()['stopped'])
    def test_negative_guarantee_rejected(self):
        self.mutate(lambda x:x['claims'][0].update(analogy_text='如果照这个建议行动，至少不会亏损，近期可以直接开始。'))
        self.assertIn('implicit_or_absolute_prediction',self.evaluate().errors)
    def test_time_prediction_rejected(self):
        self.mutate(lambda x:x['claims'][0].update(analogy_text='如果现在开始准备，下周会有结果，之后就可以继续推进。'))
        self.assertEqual(self.evaluate().status,'BASE_FALLBACK')
    def test_source_condition_expansion_rejected(self):
        self.mutate(lambda x:x['claims'][0].update(analogy_text='条件已经满足，所以可将这段提醒用于任何经营方案。'))
        self.assertIn('source_condition_determination',self.evaluate().errors)
    def test_frozen_direction_change_rejected(self):
        self.mutate(lambda x:x['claims'][0].update(analogy_text='可以认定综合方向为偏有利，近期不需要再核对限制。'))
        self.assertIn('locked_fact_declaration',self.evaluate().errors)
    def test_repetitive_candidate_rejected(self):
        self.mutate(lambda x:x['claims'][1].update(analogy_text=x['claims'][0]['analogy_text']))
        self.assertIn('repetitive_application',self.evaluate().errors)
    def test_reviewer_false_cannot_be_overridden(self):
        self.mutate(lambda x:x['claims'][0].update(supported=False),phase='reviewer')
        self.assertIn('independent_semantic_rejection',self.evaluate().errors); self.assertEqual(len(self.transport.calls),2)
    def test_reviewer_safety_false_stops_following_cases(self):
        self.mutate(lambda x:x['claims'][0].update(no_invented_facts=False),phase='reviewer')
        report=self.engine.run_batch(1,{c:self.requests[c] for c in ('B01','B02')},self.root/'first.json')
        self.assertEqual(report['cases'][1]['status'],'NOT_RUN_STOPPED'); self.assertEqual(len(self.transport.calls),2)
    def test_low_score_not_relaxed(self):
        self.mutate(lambda x:x['claims'][0].update(score=2),phase='reviewer')
        self.assertEqual(self.evaluate().status,'BASE_FALLBACK')
    def test_verdict_wrong_digest_rejected(self):
        self.mutate(lambda x:x.update(draft_fingerprint='0'*64),phase='reviewer')
        self.assertIn('verdict_binding',self.evaluate().errors)
    def test_missing_usage_hold_and_stop(self):
        self.replies[('B01','candidate')]=reply('{}',usage=None); r=self.evaluate()
        self.assertIn('usage_unavailable',r.errors); self.assertEqual(len(self.transport.calls),1)
    def test_exception_no_error_text_saved(self):
        with patch.object(self.transport,'perform',side_effect=RuntimeError('SYNTHETIC_SECRET_ONLY Authorization')):
            r=self.evaluate()
        self.assertEqual(r.errors,('worker_failure',)); self.assertNotIn('Authorization',canonical(r.calls))
    def test_403_fallback_no_review(self):
        self.replies[('B01','candidate')]=reply(None,code='http_failure',http_status=403,usage=None)
        self.assertEqual(self.evaluate().status,'BASE_FALLBACK'); self.assertEqual(self.ledger.snapshot()['requests'],1)
    def test_cancel_before_start_does_not_send(self):
        cancel=threading.Event(); cancel.set(); r=self.engine.run_case('B01',self.requests['B01'],cancel)
        self.assertEqual(r.status,'BASE_FALLBACK'); self.assertEqual(self.ledger.snapshot()['requests'],0)
    def test_rejected_text_never_persisted(self):
        self.mutate(lambda x:x['claims'][0].update(analogy_text='如果继续，注定赚到100万元，之后可以直接扩大计划。'))
        report=self.engine.run_batch(1,{c:self.requests[c] for c in ('B01','B02')},self.root/'first.json')
        self.assertNotIn('注定赚到',canonical(report)); self.assertNotIn('注定赚到',self.ledger.db.read_bytes().decode('utf-8','ignore'))
    def test_unreviewed_keeps_status(self):
        self.second(); r=self.evaluate('B03'); self.assertEqual(r.status,'MOCK_CONTRACT_ACCEPTED')
        self.assertEqual(self.requests['B03'].checked()['judgement']['review_status'],'unreviewed')
    def test_unresolved_keeps_both_branches(self):
        self.second(); r=self.evaluate('B04'); self.assertEqual(r.status,'MOCK_CONTRACT_ACCEPTED')
        self.assertEqual(self.requests['B04'].checked()['judgement']['review_status'],'branch_unresolved')
        self.assertTrue(self.requests['B04'].checked()['judgement']['branches'])
    def test_no_new_public_route(self):
        from backend.app.main import app
        paths=[r.path for r in app.routes]; self.assertFalse(any('acceptance' in p or 'question-quality' in p for p in paths))
    def test_exact_four_request_cap_under_repeat_refresh(self):
        self.engine.run_batch(1,{c:self.requests[c] for c in ('B01','B02')},self.root/'first.json')
        r=self.evaluate(); self.assertEqual(r.status,'BASE_FALLBACK'); self.assertEqual(self.ledger.snapshot()['requests'],4)
    def test_official_tokenizer_measures_actual_review(self):
        counter=OfficialTokenCounter(ROOT); d=draft_for('B01',self.requests['B01'])
        n=counter.reserve_input(messages_for(self.requests['B01'],'reviewer',d)); self.assertTrue(1000<n<=30000)
    def test_no_raw_prompt_or_model_object_in_report(self):
        report=self.engine.run_batch(1,{c:self.requests[c] for c in ('B01','B02')},self.root/'first.json')
        text=canonical(report)
        for term in ('Authorization','api_key','raw_response','"draft"','"messages"','"prompt"'):
            self.assertNotIn(term,text)
    def test_process_full_batch_reaps_every_mock_request(self):
        provider=ProcessTransport(self.ledger,mock_replies=self.replies)
        result=AcceptanceExecutor(self.ledger,provider,FixedCounter()).run_batch(1,{c:self.requests[c] for c in ('B01','B02')},self.root/'first.json')
        self.assertTrue(all(r['status']=='MOCK_CONTRACT_ACCEPTED' for r in result['cases']))
        self.assertEqual((provider.starts,provider.reaped),(4,4))

    def test_wrong_question_category_safe_fallback(self):
        self.mutate(lambda x:x['intent'].update(category='relationship'))
        self.assertIn('intent_category_mismatch',self.evaluate().errors)

    def test_mutated_sealed_input_returns_original_base_and_stops(self):
        from copy import deepcopy
        from backend.question_quality_v1.contract import QualityRequest
        original=self.requests['B01']
        req=replace(original,payload=deepcopy(original.payload))
        before=tuple((m['role'],m['text']) for m in req.checked()['calculation']['standard_meanings'])
        real=self.transport.perform
        def changed(*args):
            r=real(*args); req.payload['judgement']['direction']='other'; return r
        with patch.object(self.transport,'perform',side_effect=changed):
            result=self.engine.run_case('B01',req)
        self.assertEqual(result.status,'BASE_FALLBACK'); self.assertEqual(result.sections,before)
        self.assertTrue(self.ledger.snapshot()['stopped']); self.assertFalse(result.checks['facts_unchanged'])

    def test_production_report_destination_rejected(self):
        with self.assertRaises(AcceptanceDenied): self.engine.run_batch(1,{c:self.requests[c] for c in ('B01','B02')},ROOT.parent/'streamlit_mvp'/'forbidden.json')
        self.assertEqual(len(self.transport.calls),0)

    def test_content_repr_redacted(self):
        r=TransportResult('ok',content='SYNTHETIC_SECRET_ONLY')
        self.assertNotIn('SYNTHETIC_SECRET_ONLY',repr(r))

    def test_cleanup_failure_never_releases_slot(self):
        with patch.object(self.transport,'perform',return_value=TransportResult('worker_failure',reaped=False)):
            result=self.evaluate()
        self.assertIn('cleanup_failed',result.errors); self.assertTrue(self.ledger.snapshot()['active'])
        self.assertTrue(self.ledger.snapshot()['stopped'])

    def test_budget_rejection_creates_partial_report_without_call(self):
        with patch('backend.ai_acceptance_v1.ledger.MAX_FEE_NANO_USD',100):
            report=self.engine.run_batch(1,{c:self.requests[c] for c in ('B01','B02')},self.root/'first.json')
        self.assertEqual(report['cases'][1]['status'],'NOT_RUN_STOPPED'); self.assertEqual(len(self.transport.calls),0)
        self.assertTrue(self.ledger.snapshot()['stopped']); self.assertIn(1,self.ledger.snapshot()['reports'])
