"""Offline golden + hostile examples. No API, approval, Frame/history writes."""

import asyncio
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import ValidationError
from backend.app.main import app, traditional_preview_service
from backend.app.meihua_models import ManualInput
from backend.traditional_judgement_v1.trusted_input import OfflineJudgementAdapter, digest
from backend.traditional_preview_v1.execution import (
    CancellableOfflineAdapter, ExecutionControl, EXECUTION, PreviewTimedOut,
    PreviewCancelled, run_cancellable_preview,
)
from backend.traditional_preview_v1.service import TraditionalPreviewService
from backend.question_quality_v1.contract import (
    VERSION, ROLES, ApplicationDraft, IndependentVerdict, build_request, limit_ids,
    safety_flags, validate_draft, validate_verdict, time_windows,
)
from backend.question_quality_v1.pipeline import run_offline

ROOT = Path(__file__).resolve().parents[1]
REAL_POPEN = subprocess.Popen


def manual(question="", h=22, p=1):
    return ManualInput(input_mode="manual_hexagram", hexagram_id=h, moving_line=p,
                       cast_at="2026-09-24T19:45:35+08:00", question_text=question)


def candidate(request, category="business"):
    payload = request.checked()
    question = payload["question"]
    span = {"start": 0, "end": len(question), "text": question, "kind": "question"}
    # Synthetic reviewed analogies; explicitly fixture, not new corpus/meaning.
    if category == "relationship":
        analogies = ["可把外在表达与实际相处区分开，先了解你说的这段关系，再考虑怎样交流，不替对方认定想法。",
                     "可先想清楚联系时哪些做法符合自己的原则，再决定怎样表达，不因为外在形式就勉强继续。",
                     "如果互动中有需要澄清的事，可先了解具体情况再决定何时联系，不预设过失归属于谁。",
                     "可先观察实际互动是否适合继续交流，再决定停或做，不把下一步理解为关系确定会怎样。"]
    else:
        analogies = ["可先区分女装生意的外在呈现和实际做法，了解你希望怎样推进，再考虑怎样安排，不推定已有经营成果。",
                     "可先想清楚推进女装生意时哪些做法符合自己的原则，再决定怎样开始，不把外在形式当成必须依赖的东西。",
                     "如果推进中有需要调整的环节，可先了解具体情况再决定何时做，不推定困难已经解除。",
                     "可先观察实际准备情况再决定推进或停下，不把行动节奏理解为生意确定会取得某个结果。"]
    claims = []
    for index, role in enumerate(ROLES):
        frame = payload["frames"][role]
        claims.append({"claim_id": f"claim_{index}", "role": role, "frame_id": frame["frame_id"], "meaning_refs": list(range(len(frame['frame']['core_claims']))),
                       "source_evidence_ids": sorted({e for atom in frame['frame']['core_claims'] for e in atom['supported_by']}),
                       "question_spans": [span], "preserved_limit_ids": limit_ids(payload, role),
                       "analogy_text": analogies[index], "guidance": "可先核对自己已提供的信息，不把没有说明的情况当成事实。",
                       "source_layer": "application_analogy"})
    return ApplicationDraft.model_validate({"contract_version": VERSION, "request_fingerprint": request.fingerprint,
        "intent": {"category": category, "focus": span, "provided": [], "missing": []}, "claims": claims})


def verdict(request, draft, supported=True):
    return IndependentVerdict.model_validate({"contract_version": VERSION, "request_fingerprint": request.fingerprint,
        "draft_fingerprint": digest(draft.model_dump()), "claims": [
            {"claim_id": c.claim_id, "reviewed_frame_id": c.frame_id, "reviewed_evidence_ids": c.source_evidence_ids,
             "reviewed_limit_ids": c.preserved_limit_ids, "supported": supported, "preserves_conditions": True,
             "no_invented_facts": True, "no_prediction": True, "preserves_scope": True, "question_relevant": True,
             "score": 3, "reason": "离线测试替身逐条读取所绑定原子与条件；不代表真实模型可靠性。"} for c in draft.claims]})


class CandidateMock:
    def __init__(self, draft): self.draft, self.calls = draft, 0
    def generate(self, request):
        self.calls += 1
        return self.draft


class ReviewerMock:
    def __init__(self, supported=True): self.calls, self.supported = 0, supported
    def review(self, request, draft):
        self.calls += 1
        return verdict(request, draft, self.supported)


class QualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = OfflineJudgementAdapter().calculate_batch([
            manual("我现在重新做女装生意，近期应该怎么推进？"),
            manual("我和这个人的关系，接下来应该注意什么？"),
            manual("下周出行时应该注意什么？",20,4), manual("",20,4),
            manual("我们认识一个月，对方说最近工作忙，我不知道怎么安排联系频率，应该留意什么？",31,3),
        ])
        cls.business, cls.relationship, cls.travel, cls.empty, cls.old_q14 = map(build_request, cls.inputs)
        cls.draft = candidate(cls.business)

    def mutated(self, edit):
        raw = self.draft.model_dump()
        edit(raw)
        return ApplicationDraft.model_validate(raw)

    def test_business_analogy_keeps_calculation_and_same_frames(self):
        a,b=self.business.checked(),self.relationship.checked()
        self.assertEqual({k:v for k,v in a['calculation'].items() if k!='question_text'}, {k:v for k,v in b['calculation'].items() if k!='question_text'})
        self.assertEqual(a['frames'],b['frames'])
        ra=run_offline(self.business,CandidateMock(self.draft),ReviewerMock())
        rb=run_offline(self.relationship,CandidateMock(candidate(self.relationship,'relationship')),ReviewerMock())
        self.assertEqual((ra.status,rb.status),('OFFLINE_ACCEPTED','OFFLINE_ACCEPTED'))
        self.assertNotEqual(ra.sections,rb.sections)
        self.assertFalse(ra.production_approved or ra.history_written)

    def test_all_claims_have_frame_sources_and_limits(self):
        self.assertEqual(validate_draft(self.business,self.draft),[])
        for c in self.draft.claims:
            self.assertTrue(c.source_evidence_ids)
            self.assertEqual(c.preserved_limit_ids,limit_ids(self.business.checked(),c.role))

    def test_independent_source_semantics_rejection_falls_back(self):
        self.assertEqual(run_offline(self.business,CandidateMock(self.draft),ReviewerMock(False)).status,'BASE_FALLBACK')

    def test_missing_frame_falls_back(self):
        from backend.traditional_judgement_v1.trusted_input import _issue
        p=self.inputs[0].to_dict();p['frames']['moving_line']=None
        r=build_request(_issue(p));result=run_offline(r,CandidateMock(self.draft),ReviewerMock())
        self.assertEqual(result.status,'BASE_FALLBACK')

    def test_plain_dict_input_rejected(self):
        with self.assertRaises(ValueError):build_request(self.inputs[0].to_dict())

    def test_context_tamper_breaks_seal(self):
        r=build_request(self.inputs[0]);r.payload['judgement']['direction']='adverse'
        with self.assertRaises(ValueError):r.checked()

    def test_model_extra_verdict_or_facts_rejected(self):
        for key in ('direction','hexagram','reality_facts','qualification','prompt','api_key'):
            with self.subTest(key=key):
                raw=self.draft.model_dump();raw[key]='SYNTHETIC'
                with self.assertRaises(ValidationError):ApplicationDraft.model_validate(raw)

    def test_wrong_frame_ref_rejected(self):
        d=self.mutated(lambda d:d['claims'][0].update(frame_id='0'*64))
        self.assertIn('frame_binding',validate_draft(self.business,d))

    def test_wrong_source_ref_rejected(self):
        d=self.mutated(lambda d:d['claims'][0].update(source_evidence_ids=['invented']))
        self.assertIn('evidence_binding',validate_draft(self.business,d))

    def test_source_meaning_index_out_of_range_rejected(self):
        d=self.mutated(lambda d:d['claims'][0].update(meaning_refs=[900]))
        self.assertIn('meaning_binding',validate_draft(self.business,d))

    def test_unknown_or_omitted_limits_rejected(self):
        for ids in ([],['invented_condition']):
            d=candidate(self.travel,'travel').model_dump();d['claims'][1]['preserved_limit_ids']=ids
            self.assertIn('omitted_or_added_limits',validate_draft(self.travel,ApplicationDraft.model_validate(d)))

    def test_duplicate_role_rejected(self):
        d=self.mutated(lambda d:d['claims'][3].update(role='moving_line'))
        self.assertIn('role_or_id_binding',validate_draft(self.business,d))

    def test_verifier_stale_receipt_rejected(self):
        v=verdict(self.business,self.draft).model_dump();v['draft_fingerprint']='0'*64
        self.assertIn('verdict_binding',validate_verdict(self.business,self.draft,IndependentVerdict.model_validate(v)))

    def test_verifier_wrong_evidence_rejected(self):
        v=verdict(self.business,self.draft).model_dump();v['claims'][0]['reviewed_evidence_ids']=['invented']
        self.assertIn('verifier_evidence_or_limit_binding',validate_verdict(self.business,self.draft,IndependentVerdict.model_validate(v)))

    def test_verifier_score_two_or_single_false_rejected(self):
        for key,value in [('score',2),('preserves_conditions',False),('no_prediction',False),('question_relevant',False)]:
            with self.subTest(key=key):
                v=verdict(self.business,self.draft).model_dump();v['claims'][0][key]=value
                self.assertIn('independent_semantic_rejection',validate_verdict(self.business,self.draft,IndependentVerdict.model_validate(v)))

    def test_generator_cannot_review_itself(self):
        provider=CandidateMock(self.draft)
        self.assertEqual(run_offline(self.business,provider,provider).errors,('independent_reviewer_required',))

    def test_empty_question_skips_provider(self):
        provider=CandidateMock(self.draft)
        self.assertEqual(run_offline(self.empty,provider,ReviewerMock()).status,'BASE_FALLBACK')
        self.assertEqual(provider.calls,0)

    def test_corrupt_span_rejected(self):
        d=self.mutated(lambda d:d['intent']['focus'].update(text='我已经盈利'))
        self.assertIn('intent_exact_span',validate_draft(self.business,d))

    def test_question_goal_not_reality_fact(self):
        d=self.mutated(lambda d:d['intent'].update(provided=[{**d['intent']['focus'],'kind':'reported'}]))
        self.assertIn('question_or_goal_as_fact',validate_draft(self.business,d))

    def test_future_window_not_missing_and_past_not_future(self):
        self.assertEqual(time_windows('我们认识一个月'),[])
        self.assertEqual(time_windows('我今年希望推进，下周先观察'),['今年','下周'])
        d=self.mutated(lambda d:d['intent'].update(missing=['time_window']))
        self.assertIn('provided_time_marked_missing',validate_draft(self.business,d))

    def test_repeated_prose_rejected(self):
        d=self.mutated(lambda d:d['claims'][1].update(analogy_text=d['claims'][0]['analogy_text']))
        self.assertIn('repetitive_application',validate_draft(self.business,d))

    def test_duplicate_punctuation_rejected(self):
        d=self.mutated(lambda d:d['claims'][0].update(guidance='可先了解自己说明的情况。。'))
        self.assertIn('duplicated_punctuation',validate_draft(self.business,d))

    def test_legacy_seven_real_failure_excerpts(self):
        rows=json.loads((ROOT/'tests/fixtures/day8a_old_failure_examples.json').read_bytes())['cases']
        self.assertEqual(len(rows),7)
        for row in rows:
            with self.subTest(case=row['case_id']):
                flags=safety_flags(row['analogy']+row['guidance'],row['question'])
                if row['case_id']=='Q14':
                    d=candidate(self.old_q14,'relationship').model_dump()
                    d['claims'][2].update(analogy_text=row['analogy'],guidance=row['guidance'])
                    reviewer=ReviewerMock(True)
                    result=run_offline(self.old_q14,CandidateMock(ApplicationDraft.model_validate(d)),reviewer)
                    self.assertEqual(result.status,'BASE_FALLBACK')
                    self.assertIn('known_source_scope_hold',result.errors)
                    self.assertEqual(reviewer.calls,0)
                else:self.assertTrue(any(f.startswith(row['expected_rejection']) for f in flags),flags)

    def test_known_source_scope_hold_is_bound_to_actual_frozen_evidence(self):
        p=self.old_q14.checked(); f=p['frames']['mutual_hexagram']['frame']
        self.assertIn('姤女壯勿用取女',p['evidence'][f['source_evidence_ids'][0]]['text'])
        self.assertEqual(f['core_claims'][0]['text'],'这段内容讲相遇')
        from backend.question_quality_v1.contract import application_scope_errors
        self.assertEqual(application_scope_errors(p),['known_source_scope_hold'])

    def test_scope_hold_registry_missing_or_tampered_fails_closed(self):
        from backend.question_quality_v1 import contract
        with patch.object(contract,'_SCOPE_HOLDS_SHA256','0'*64):
            self.assertEqual(validate_draft(self.business,self.draft),['application_scope_registry_unavailable'])

    def test_scope_hold_pin_survives_windows_line_endings(self):
        from backend.question_quality_v1 import contract
        raw=contract._SCOPE_HOLDS.read_bytes().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
        with patch.object(type(contract._SCOPE_HOLDS),'read_bytes',return_value=raw):
            self.assertEqual(contract.application_scope_errors(self.old_q14.checked()),['known_source_scope_hold'])

    def test_new_unicode_and_negative_guarantee_attacks(self):
        for text in ('至少不会失去信任','就能避免失败','绝不会亏损','一定不会出事','必 然 成功','必\u200b然失败','至少不\n会失去','一定成功','肯定成功','十有八九会发生'):
            with self.subTest(text=text):self.assertIn('implicit_or_absolute_prediction',safety_flags(text,''))

    def test_new_time_fact_condition_attacks(self):
        for text,expected in [('下周会有结果','time_prediction'),('你的库存已积压','unprovided_reality:库存'),('原典条件已经满足','source_condition_determination'),('体卦属金','locked_fact_declaration'),('用途不明，所以前提不成立','source_condition_determination')]:
            with self.subTest(text=text):self.assertIn(expected,safety_flags(text,'应该怎么办？'))

    def test_unreviewed_does_not_get_verdict_from_model(self):
        self.assertFalse(self.business.checked()['judgement']['finite_synthesis_available'])
        result=run_offline(self.business,CandidateMock(self.draft),ReviewerMock())
        self.assertEqual(result.status,'OFFLINE_ACCEPTED')
        self.assertFalse(result.production_approved)
        self.assertNotIn('偏有利',str(result.sections))
        self.assertIn('locked_fact_declaration',safety_flags('这件生意总体偏有利',''))
        self.assertIn('locked_fact_declaration',safety_flags('该爻已经审核，可以直接断成败',''))

    def test_scope_and_source_analogy_labels_rendered(self):
        r=run_offline(self.business,CandidateMock(self.draft),ReviewerMock())
        self.assertTrue(all('传统卦义：' in text and '现实应用类比' in text for _,text in r.sections))
        self.assertIn('不是事情必然发生的结果',dict(r.sections)['changed_hexagram'])

    def test_renderer_keeps_all_reviewed_limits_verbatim_and_unknown(self):
        r=run_offline(self.travel,CandidateMock(candidate(self.travel,'travel')),ReviewerMock())
        self.assertEqual(r.status,'OFFLINE_ACCEPTED')
        section=dict(r.sections)['moving_line']
        self.assertIn('现实是否满足未核实',section)
        for atom in self.travel.checked()['judgement']['conditions']+self.travel.checked()['judgement']['scope_limits']:
            self.assertIn(atom['text'],section)

    def test_scope_hold_cannot_change_original_frame_or_qualification(self):
        before=self.old_q14.checked(); frozen=digest(before)
        r=run_offline(self.old_q14,CandidateMock(candidate(self.old_q14,'relationship')),ReviewerMock())
        self.assertEqual(r.status,'BASE_FALLBACK')
        self.assertEqual(digest(self.old_q14.checked()),frozen)

    def test_all_seven_categories_validate_without_computing_new_facts(self):
        for category in ('general','career','business','relationship','decision','travel','other'):
            with self.subTest(category=category):
                raw=self.draft.model_dump();raw['intent']['category']=category
                d=ApplicationDraft.model_validate(raw)
                self.assertEqual(validate_draft(self.business,d),[])

    def test_reported_speech_must_not_be_an_established_fact(self):
        from backend.question_quality_v1.contract import QuestionSpan,span_type_errors
        s=QuestionSpan(start=0,end=7,text='对方说工作忙',kind='reported')
        self.assertIn('reported_speech_as_established_fact',span_type_errors(s))
        self.assertEqual(span_type_errors(s.model_copy(update={'kind':'reported_speech'})),[])

    def test_claim_cannot_relabel_question_as_fact(self):
        d=self.mutated(lambda d:d['claims'][0]['question_spans'][0].update(kind='reported'))
        self.assertIn('question_or_goal_as_fact',validate_draft(self.business,d))

    def test_traditional_trigger_words_rejected(self):
        for text in ('保證成功','絕不會虧損','必然失敗','一定賺錢'):
            with self.subTest(text=text):self.assertIn('implicit_or_absolute_prediction',safety_flags(text,''))

    def test_month_strength_not_a_personal_reality_fact(self):
        for text in ('你的能力很强','你的处境稳定','你资金充足'):
            self.assertIn('unprovided_reality_assertion',safety_flags(text,''))

    def test_exact_source_status_and_reliable_refs_required(self):
        from backend.traditional_judgement_v1.trusted_input import _issue
        data=self.inputs[0].to_dict()
        for r in data['calculation']['source_references']:r['verification_status']='needs_manual_check'
        with self.assertRaises(ValidationError):_issue(data)  # Original boundary is stricter still.
        data['calculation']['source_references']=[]
        req=build_request(_issue(data))
        self.assertEqual(req.checked()['frames'],{})
        self.assertEqual(run_offline(req,CandidateMock(self.draft),ReviewerMock()).status,'BASE_FALLBACK')

    def test_provider_failure_never_leaks_or_retries(self):
        class Broken:
            calls=0
            def generate(self,request):
                self.calls+=1;raise RuntimeError('SYNTHETIC_PRIVATE_ERROR')
        provider=Broken();result=run_offline(self.business,provider,ReviewerMock())
        self.assertEqual(provider.calls,1);self.assertEqual(result.status,'BASE_FALLBACK')
        self.assertNotIn('SYNTHETIC_PRIVATE_ERROR',str(result))

    def test_verifier_cannot_supply_a_free_result(self):
        raw=verdict(self.business,self.draft).model_dump();raw['prediction']='SYNTHETIC'
        with self.assertRaises(ValidationError):IndependentVerdict.model_validate(raw)

    def test_contract_is_deterministic_and_no_existing_data_mutated(self):
        before=digest(self.business.checked())
        a=run_offline(self.business,CandidateMock(self.draft),ReviewerMock())
        b=run_offline(self.business,CandidateMock(self.draft),ReviewerMock())
        self.assertEqual(a,b);self.assertEqual(digest(self.business.checked()),before)


class RuntimeTests(unittest.TestCase):
    def launch_sleep(self, children):
        def launch(*args,**kwargs):
            # TEST ONLY replaces the fixed command, not a public execution hook.
            child=REAL_POPEN([sys.executable,'-I','-B','-c','import time; time.sleep(30)'],**kwargs)
            children.append(child)
            return child
        return launch

    def test_deadline_kills_reaps_owned_child_and_closes_pipes(self):
        children=[];control=ExecutionControl(seconds=.12);token=EXECUTION.set(control)
        started=time.monotonic()
        try:
            with patch('backend.traditional_preview_v1.execution.subprocess.Popen',side_effect=self.launch_sleep(children)):
                with self.assertRaises(PreviewTimedOut):CancellableOfflineAdapter().calculate(manual())
        finally:EXECUTION.reset(token)
        self.assertLess(time.monotonic()-started,2)
        self.assertIsNotNone(children[0].poll())
        self.assertTrue(all(p.closed for p in (children[0].stdin,children[0].stdout,children[0].stderr)))

    def test_client_disconnect_joins_child_then_releases_both_slots(self):
        children=[];service=TraditionalPreviewService()
        class Disconnected:
            async def is_disconnected(self):return True
        with patch('backend.traditional_preview_v1.execution.subprocess.Popen',side_effect=self.launch_sleep(children)):
            with self.assertRaises(PreviewCancelled):asyncio.run(run_cancellable_preview(service,manual(),Disconnected()))
        self.assertEqual(len(children),1);self.assertIsNotNone(children[0].poll())
        self.assertTrue(service._slots.acquire(False));self.assertTrue(service._slots.acquire(False))
        self.assertFalse(service._slots.acquire(False));service._slots.release();service._slots.release()

    def test_asgi_cancel_joins_worker_no_retry(self):
        children=[];service=TraditionalPreviewService()
        class Connected:
            async def is_disconnected(self):return False
        async def run():
            task=asyncio.create_task(run_cancellable_preview(service,manual(),Connected()))
            await asyncio.sleep(.1);task.cancel()
            with self.assertRaises(asyncio.CancelledError):await task
        with patch('backend.traditional_preview_v1.execution.subprocess.Popen',side_effect=self.launch_sleep(children)):
            asyncio.run(run())
        self.assertEqual(len(children),1);self.assertIsNotNone(children[0].poll())
        self.assertTrue(service._slots.acquire(False));service._slots.release()

    def test_timeout_is_504_not_raw_exception(self):
        with patch.object(traditional_preview_service._adapter,'calculate',side_effect=PreviewTimedOut()):
            r=TestClient(app).post('/api/v1/meihua/traditional-preview',json=manual().model_dump())
        self.assertEqual(r.status_code,504);self.assertNotIn('Traceback',r.text)

    def test_no_retry_after_cancellation_and_no_stale_response(self):
        with patch.object(traditional_preview_service._adapter,'calculate',side_effect=PreviewCancelled()) as worker:
            r=TestClient(app).post('/api/v1/meihua/traditional-preview',json=manual().model_dump())
        self.assertEqual(r.status_code,499);self.assertEqual(worker.call_count,1)

    def test_preview_deadlines_leave_frontend_margin(self):
        from backend.traditional_preview_v1.execution import WORKER_SECONDS,REQUEST_SECONDS,CLEANUP_SECONDS
        text=(ROOT/'frontend/src/platform/MeihuaPage.tsx').read_text(encoding='utf8')
        self.assertLessEqual(WORKER_SECONDS+CLEANUP_SECONDS,REQUEST_SECONDS)
        self.assertLess(REQUEST_SECONDS,25)
        self.assertIn('25000',text)
        self.assertIn('取消本次计算',text)

    def test_frontend_does_not_repeat_branch_full_text_in_overview_or_factors(self):
        text=(ROOT/'frontend/src/platform/TraditionalJudgementPreview.tsx').read_text(encoding='utf8')
        self.assertIn('previewOverview(value)',text);self.assertIn('factorDisplay(factor.text, value)',text)
        self.assertIn('displaySentence(branch.text)',text)
        self.assertIn('原始规则层总论与因素',text)
        self.assertIn('{quote.quote}',text)

    def test_no_quality_route_or_paid_provider_import(self):
        text=(ROOT/'backend/app/main.py').read_text(encoding='utf8')
        self.assertNotIn('question_quality',text)
        for p in (ROOT/'backend/question_quality_v1').glob('*.py'):
            self.assertNotIn('DeepSeek',p.read_text(encoding='utf8'));self.assertNotIn('open_https',p.read_text(encoding='utf8'))

    def test_original_frame_rule_text_and_engine_hashes_unchanged(self):
        import hashlib
        baseline=json.loads((ROOT/'docs/day8a_day7a_baseline.json').read_bytes())
        for path,expected in baseline['files_sha256'].items():
            if path not in baseline['allowed_modified_files']:
                with self.subTest(path=path):self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),expected)

    def test_disconnect_signal_is_outside_body_middleware(self):
        from backend.traditional_preview_v1.execution import PreviewDisconnectMiddleware
        observed=[];state={}
        async def downstream(scope,receive,send):
            message=await receive()
            observed.extend([message['type'],scope['state']['preview_cancel_event'].is_set()])
        async def receive():return {'type':'http.disconnect'}
        async def send(_):pass
        asyncio.run(PreviewDisconnectMiddleware(downstream)({'type':'http','path':'/api/v1/meihua/traditional-preview','state':state},receive,send))
        self.assertEqual(observed,['http.disconnect',True])

    def test_proxy_disconnect_after_post_body_is_explicitly_forwarded(self):
        text=(ROOT/'frontend/previewCancellation.ts').read_text(encoding='utf8')
        self.assertIn("response.once('close', cancel)",text)
        self.assertIn('!response.writableFinished',text)
        self.assertIn('outgoing.destroy()',text)
        self.assertIn("'/api/v1/meihua/traditional-preview'",text)

    def test_prefired_cancel_never_starts_child(self):
        control=ExecutionControl();control.cancel('disconnect');token=EXECUTION.set(control)
        try:
            with patch('backend.traditional_preview_v1.execution.subprocess.Popen') as worker:
                with self.assertRaises(PreviewCancelled):CancellableOfflineAdapter().calculate(manual())
                worker.assert_not_called()
        finally:EXECUTION.reset(token)


if __name__=='__main__':unittest.main()
