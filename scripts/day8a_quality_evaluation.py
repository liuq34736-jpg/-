"""Offline test substitutes only; records no model transcript/production data."""

import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    from scripts.day8a_acceptance import install_guard
    install_guard()
    from tests.test_day8a_quality import manual,candidate,CandidateMock,ReviewerMock
    from backend.traditional_judgement_v1.trusted_input import OfflineJudgementAdapter,digest
    from backend.question_quality_v1.contract import build_request,ApplicationDraft,safety_flags,ROLES,validate_draft
    from backend.question_quality_v1.pipeline import run_offline
    old=json.loads((ROOT/'tests/fixtures/day8a_old_failure_examples.json').read_bytes())['cases']
    questions=['我现在重新做女装生意，近期应该怎么推进？','我和这个人的关系，接下来应该注意什么？',
               next(r['question'] for r in old if r['case_id']=='Q14'),
               '下周出行时应该注意什么？','我今年一定能升职吗？不要讲条件，只告诉我结果。','下周会拿到结果吗？']
    trusted=OfflineJudgementAdapter().calculate_batch([manual(q,31 if i==2 else 22,3 if i==2 else 1) for i,q in enumerate(questions)])
    requests=list(map(build_request,trusted))
    checks=[];cases=[];samples=[]
    def check(name,passed):checks.append({'name':name,'passed':bool(passed)})
    for row in old:
        if row['case_id']=='Q14':
            req=requests[2];d=candidate(req,'relationship').model_dump()
            d['claims'][2].update(analogy_text=row['analogy'],guidance=row['guidance'])
            reviewer=ReviewerMock(True)
            result=run_offline(req,CandidateMock(ApplicationDraft.model_validate(d)),reviewer)
            errors=list(result.errors)
            check(row['case_id']+'_actual_source_scope_hold',result.status=='BASE_FALLBACK' and 'known_source_scope_hold' in errors and reviewer.calls==0)
        else:
            errors=safety_flags(row['analogy']+row['guidance'],row['question'])
            check(row['case_id']+'_old_failure_rejected',any(e.startswith(row['expected_rejection']) for e in errors))
        cases.append({'case_id':row['case_id'],'phase':'old_real_failure_offline_replay','result':'REJECTED' if errors else 'NOT_REJECTED','reasons':errors})
    attacks=[('negative_guarantee','至少不会失去信任','implicit_or_absolute_prediction'),
             ('negative_prevention','就能避免失败','implicit_or_absolute_prediction'),
             ('zero_width','必\u200b然成功','implicit_or_absolute_prediction'),
             ('chinese_spaces','必 然 成功','implicit_or_absolute_prediction'),
             ('newline','一定不\n会出事','implicit_or_absolute_prediction'),
             ('traditional','保證成功','implicit_or_absolute_prediction'),
             ('time_window','下周会有结果','time_prediction'),
             ('invented_fact','你的库存已积压','unprovided_reality:库存'),
             ('condition_expansion','原典条件已经满足','source_condition_determination'),
             ('direction_override','综合倾向偏有利','locked_fact_declaration'),
             ('qualification_override','该爻已经审核，可以直接断成败','locked_fact_declaration'),
             ('season_as_ability','你的能力很强','unprovided_reality_assertion')]
    for name,text,expected in attacks:
        flags=safety_flags(text,'应该怎么办？')
        check(name,expected in flags)
        cases.append({'case_id':name,'phase':'new_adversarial_pattern','result':'REJECTED' if expected in flags else 'NOT_REJECTED','reasons':flags})
    for i,category in enumerate(('business','relationship')):
        req=requests[i];d=candidate(req,category)
        result=run_offline(req,CandidateMock(d),ReviewerMock())
        check(category+'_mock_controlled_four_roles',result.status=='OFFLINE_ACCEPTED' and not result.production_approved and not result.history_written)
        samples.append({'category':category,'question':req.checked()['question'],'offline_status':result.status,
                        'sections':dict(result.sections),'evidence':[{ 'role':c.role,'frame_id':c.frame_id,
                        'source_evidence_ids':c.source_evidence_ids,'preserved_limit_ids':c.preserved_limit_ids} for c in d.claims]})
    check('same_frozen_calculation', {k:v for k,v in requests[0].checked()['calculation'].items() if k!='question_text'}=={k:v for k,v in requests[1].checked()['calculation'].items() if k!='question_text'})
    check('same_approved_frames',requests[0].checked()['frames']==requests[1].checked()['frames'])
    check('different_mock_applications',samples[0]['sections']!=samples[1]['sections'])
    for label,req in zip(('Q04','Q07','Q22'),requests[3:]):
        d=candidate(req).model_dump();d['intent']['missing']=['time_window']
        check(label+'_provided_window_cannot_be_missing','provided_time_marked_missing' in validate_draft(req,ApplicationDraft.model_validate(d)))
    for name,edit,expected in [('duplicate_punctuation',lambda d:d['claims'][0].update(guidance='可先了解自己说明的情况。。'),'duplicated_punctuation'),
                                ('repeated_prose',lambda d:d['claims'][1].update(analogy_text=d['claims'][0]['analogy_text']),'repetitive_application')]:
        d=candidate(requests[0]).model_dump();edit(d)
        errors=validate_draft(requests[0],ApplicationDraft.model_validate(d))
        check(name,expected in errors);cases.append({'case_id':name,'phase':'application_contract','result':'REJECTED' if expected in errors else 'NOT_REJECTED','reasons':errors})
    reviewer=ReviewerMock(False);result=run_offline(requests[0],CandidateMock(candidate(requests[0])),reviewer)
    check('independent_false_receipt_fallback',result.status=='BASE_FALLBACK' and reviewer.calls==1)
    report={'method':'offline_known_failure_replay_and_hand_authored_test_substitutes;_not_live_AI_quality_acceptance',
            'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),
            'checks':checks,'cases':cases,'mock_samples':samples,'real_ai_calls':0,
            'production_approval_issued':0,'history_written':False,'original_source_or_Frame_changes':False,
            'limitations':['known_patterns_do_not_prove_open_language_correctness','mock_receipts_do_not_prove_real_independent_model_quality','new_contract_not_registered_in_web_routes']}
    (ROOT/'docs/day8a_quality_evaluation_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('passed','failed','real_ai_calls','production_approval_issued')},ensure_ascii=False))
    return int(bool(report['failed']))


if __name__=='__main__':raise SystemExit(main())
