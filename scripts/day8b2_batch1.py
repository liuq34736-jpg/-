"""Private operator tool for the single authorized Batch1. No website route.

Separate commands deliberately pause after B01 for source review. None retries,
resets, changes prompts or enables Batch2. The existing live RUN_ID/path is fixed.
"""
from datetime import datetime, timezone
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.ai_acceptance_v1.ledger import BudgetLedger
from backend.ai_acceptance_v1.policy import AcceptanceDenied, MAX_INPUT, PEAK, OFF_PEAK, sha, canonical
from backend.ai_acceptance_v1.prompts import OfficialTokenCounter, messages_for
from backend.ai_acceptance_v1.executor import AcceptanceExecutor
from backend.ai_acceptance_v1.transport import ProcessTransport

AUDIT = ROOT / 'private/day8b2-audit'
REAL_RECORDS = ROOT / 'private/day8b1/records'
REAL_ANCHORS = ROOT / 'private/day8b1-anchors'
APPROVAL = 'DAY8B2_USER_AUTH_BATCH1_2Q_4REQ_80000TOKENS_USD006_ZERO_RETRIES'
PRICE_REFERENCE = 'https://api-docs.deepseek.com/quick_start/pricing/'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Audit objects contain only synthetic inputs, constrained text and safe codes.
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def hashes():
    names = ['backend/ai_acceptance_v1/ledger.py', 'scripts/day8b2_batch1.py', 'tests/test_day8b2_batch1.py']
    return {n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}


def requests():
    from backend.app.meihua_models import ManualInput
    from backend.traditional_judgement_v1.trusted_input import OfflineJudgementAdapter
    from backend.question_quality_v1.contract import build_request
    from scripts.day8b_prepare import CASES, CAST_AT
    selected = CASES[:2]
    inputs = [ManualInput(input_mode='manual_hexagram', hexagram_id=c['hexagram_id'],
              moving_line=c['moving_line'], cast_at=CAST_AT, question_text=c['question']) for c in selected]
    return {c['case_id']: build_request(t) for c,t in zip(selected, OfflineJudgementAdapter().calculate_batch(inputs))}


class ConservativeCounter:
    """Reserve the entire allowed 30k input envelope, not the measured estimate.

    Official local measurement is a preflight bound check; extra reservation
    stays charged until authoritative, consistent usage arrives. No cache credit
    is assumed. Unknown bills stop the run. This is not a vendor account cap.
    """
    def __init__(self): self.official = OfficialTokenCounter(ROOT)
    def reserve_input(self, messages):
        measured = self.official.reserve_input(messages)
        if measured > MAX_INPUT: raise AcceptanceDenied('invalid_reservation')
        return MAX_INPUT


class AuditTransport:
    """Restricted redacted fragments, not an upstream envelope/prompt/error log."""
    def __init__(self, inner, folder):
        self.inner, self.ledger, self.folder = inner, inner.ledger, folder
    def perform(self, permit, wire, cancel):
        result = self.inner.perform(permit, wire, cancel)
        fragment = {'phase': permit.phase, 'code': result.code, 'http_status': result.http_status}
        if result.content:
            from backend.app.deepseek import strict_json
            try:
                data = strict_json(result.content)
                if type(data) is dict:
                    # No arbitrary extra keys or unconstrained error objects.
                    if permit.phase == 'candidate':
                        fragment['intent'] = data.get('intent')
                        keys = {'claim_id','role','frame_id','meaning_refs','source_evidence_ids',
                                'question_spans','preserved_limit_ids','analogy_text','guidance','source_layer'}
                    else:
                        keys = {'claim_id','reviewed_frame_id','reviewed_evidence_ids','reviewed_limit_ids',
                                'supported','preserves_conditions','no_invented_facts','no_prediction',
                                'preserves_scope','question_relevant','score','reason'}
                    fragment['claims'] = [{k:v for k,v in c.items() if k in keys}
                                          for c in data.get('claims',[]) if type(c) is dict][:4]
                    fragment['schema_keys'] = sorted(k for k in data if k in
                        {'contract_version','request_fingerprint','draft_fingerprint','intent','claims'})
            except Exception:
                fragment['parse_result'] = 'not_valid_json'
        encoded = canonical(fragment)
        if re.search(r'authorization|bearer|sk-[a-zA-Z0-9_-]{10,}|<[^>]*>', encoded, re.I):
            fragment = {'phase': permit.phase, 'code': 'unsafe_fragment_excluded'}
        write(self.folder/f'{permit.case_id}_{permit.phase}_fragments.json', fragment)
        return result


def mock_check():
    from scripts.day8a_acceptance import install_guard
    install_guard()
    from tests.day8b1_fixtures import replies_for, draft_for
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        ledger=BudgetLedger(root/'records',root/'anchors','mock')
        ledger.initialize(); ledger.restrict_first_batch(); ledger.authorize(1, APPROVAL+'_MOCK')
        reqs=requests(); counter=ConservativeCounter()
        inner=ProcessTransport(ledger,mock_replies=replies_for(reqs))
        engine=AcceptanceExecutor(ledger,inner,counter)
        outputs=[engine.run_case(c,r) for c,r in reqs.items()]
        measurements=[]
        for c,r in reqs.items():
            for phase in ('candidate','reviewer'):
                m=messages_for(r,phase,None if phase=='candidate' else draft_for(c,r))
                measurements.append({'case_id':c,'phase':phase,
                                     'measured_with_margin':counter.official.reserve_input(m),
                                     'input_reserved_per_call':counter.reserve_input(m)})
        ledger.record_batch_report(1,sha([asdict(o) for o in outputs])); ledger.close_batch(1)
        state=ledger.snapshot()
        denied=False
        try: ledger.reserve('B02','reviewer',30000,'a'*64)
        except AcceptanceDenied: denied=True
        return {'passed':all(o.status=='MOCK_CONTRACT_ACCEPTED' for o in outputs) and denied,
                'calls':state['requests'],'workers_started':inner.starts,'workers_reaped':inner.reaped,
                'live_calls':0,'closed':state['closed_batches'],'batch_limits':state['batch_limits'],
                'measured_prompts':measurements,'state_is_disposable_mock':True}


def checks():
    records={}
    for kind in ('unit','mock','legacy','frozen_matrix','old71'):
        env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','TEMP','TMP'}}
        env['DEEPSEEK_API_KEY']='SYNTHETIC_OFFLINE_CONFIG_ONLY'
        import time
        start=time.monotonic(); at=datetime.now(timezone.utc).isoformat()
        run=subprocess.run([sys.executable,'-I','-B','-X','utf8',str(Path(__file__).resolve()),kind,'--worker'],
            env=env,cwd=ROOT,capture_output=True,timeout=900,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        try: value=json.loads(run.stdout)
        except ValueError: value={'passed':False,'reason':'guarded_runner_failure'}
        records[kind]={'started_at_utc':at,'seconds':round(time.monotonic()-start,3),
                       'exit_code':run.returncode,'result':value,
                       'command':f'.venv/Scripts/python.exe -I -B -X utf8 scripts/day8b2_batch1.py {kind} --worker'}
    value={'checks':records,'tool_hashes':hashes(),
           'passed':all(r['exit_code']==0 and r['result'].get('passed') is not False for r in records.values()),
           'real_calls':0}
    write(ROOT/'docs/day8b2_batch1_mock_test_results.json',value)
    print(canonical({'passed':value['passed'],'unit':records['unit']['result'],'mock':records['mock']['result']}))


def preflight():
    from scripts.day6a_integrity_check import inspect
    from backend.app.deepseek import load_config
    checks=json.loads((ROOT/'docs/day8b2_batch1_mock_test_results.json').read_bytes())
    if not checks['passed'] or checks['tool_hashes']!=hashes(): raise AcceptanceDenied('mock_preflight_required')
    baseline=json.loads((ROOT/'runtime/day8b2-baseline/files.json').read_bytes())
    changed=[n for n,h in baseline['files'].items() if hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h]
    if changed!=['backend/ai_acceptance_v1/ledger.py']: raise AcceptanceDenied('unexpected_project_change')
    i=inspect()
    if (i['changed_production_files'] or i['changed_signed_cache_files'] or i['history_rows']!=42 or
            not all(i[k] for k in ('history_schema_unchanged','history_row_hashes_unchanged','history_database_bytes_unchanged')) or
            not i['git_safety']['passed']): raise AcceptanceDenied('protected_integrity_failure')
    config=load_config()
    if not config.configured: raise AcceptanceDenied('not_configured')
    ledger=BudgetLedger(REAL_RECORDS,REAL_ANCHORS,'live')
    paths=(ledger.db,ledger.anchor,ledger.marker)
    exists=[p.exists() for p in paths]
    if any(exists) and not all(exists): raise AcceptanceDenied('budget_state_missing')
    prior=ledger.snapshot() if all(exists) else None
    if prior and (prior['requests'] or prior['authorized_batches'] or prior['closed_batches'] or prior['stopped']):
        raise AcceptanceDenied('existing_execution_no_repeat')
    reqs=requests()
    proof={'at_utc':datetime.now(timezone.utc).isoformat(),'base_commit':baseline['base_commit'],
           'key_configured':True,'fixed_endpoint':config.endpoint,'provider':config.provider_name,
           'model':config.model_name,'timeout_seconds':config.timeout_seconds,'redirects':False,'retries':0,
           'tool_hashes':hashes(),'mock_report_sha256':sha(checks),'live_prior':prior,
           'price_url':PRICE_REFERENCE,'price_checked_on':'2026-10-12','peak':PEAK,'off_peak':OFF_PEAK,
           'case_fingerprints':{c:r.fingerprint for c,r in reqs.items()},
           'two_calls_per_case_maximum':True,'original_case_plan_preserved':True,
           'batch_limit':{'questions':2,'requests':4,'tokens':80000,'fee_nano_usd':60000000},
           'full_input_envelope_reserved':30000,'four_call_worst_peak_fee_nano_usd':53203200,
           'token_reservation_gate_may_stop_before_two_complete_cases':True}
    write(AUDIT/'preflight.json',proof)
    # Restricted local synthetic fragments cannot be read by other ordinary users.
    if os.name=='nt':
        import getpass
        user=getpass.getuser()
        result=subprocess.run(['icacls',str(AUDIT),'/inheritance:r','/grant:r',f'{user}:(OI)(CI)F',
                               'SYSTEM:(OI)(CI)F'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode: raise AcceptanceDenied('audit_acl_required')
    print(canonical({'preflight_passed':True,'key_configured':True,'live_previous_requests':0 if prior is None else prior['requests'],
                     'fixed_cases':list(reqs),'calls_per_case':2,'batch2_authorized':False}))


def run_one(case_id):
    proof=json.loads((AUDIT/'preflight.json').read_bytes())
    checks=json.loads((ROOT/'docs/day8b2_batch1_mock_test_results.json').read_bytes())
    if proof['tool_hashes']!=hashes() or proof['mock_report_sha256']!=sha(checks) or not checks['passed']:
        raise AcceptanceDenied('preflight_changed')
    if datetime.now().date().isoformat()!=proof['price_checked_on']: raise AcceptanceDenied('price_reconfirmation_required')
    ledger=BudgetLedger(REAL_RECORDS,REAL_ANCHORS,'live')
    if case_id=='B01':
        if any(p.exists() for p in (ledger.db,ledger.marker,ledger.anchor)):
            raise AcceptanceDenied('existing_execution_no_repeat')
        ledger.initialize()  # First registration of the SAME fixed live run, not a new cycle/reset.
        ledger.restrict_first_batch()
        ledger.confirm_unchanged_prices(proof['price_checked_on'],PEAK,OFF_PEAK,sha(proof))
        ledger.authorize(1,APPROVAL)
    elif case_id=='B02':
        review=json.loads((AUDIT/'B01_source_review.json').read_bytes())
        first=json.loads((AUDIT/'B01_result.json').read_bytes())
        if review.get('result_sha256')!=sha(first) or review.get('serious_violation') is not False or not review.get('source_review_completed'):
            raise AcceptanceDenied('first_source_review_required')
        state=ledger.snapshot()
        if state['stopped'] or state['closed_batches'] or state['requests']>2:
            raise AcceptanceDenied('run_stopped')
    else: raise AcceptanceDenied('fixed_batch_required')
    req=requests()[case_id]
    if req.fingerprint!=proof['case_fingerprints'][case_id]: raise AcceptanceDenied('case_or_source_changed')
    write(AUDIT/f'{case_id}_bound_evidence.json',req.checked())  # Synthetic evidence; no sealed request object/secret.
    state_before=ledger.snapshot()
    inner=ProcessTransport(ledger)
    result=AcceptanceExecutor(ledger,AuditTransport(inner,AUDIT),ConservativeCounter()).run_case(case_id,req)
    record={**asdict(result),'at_utc':datetime.now(timezone.utc).isoformat(),'budget_before':state_before,
            'budget_after':ledger.snapshot(),'workers_started':inner.starts,'workers_reaped':inner.reaped}
    write(AUDIT/f'{case_id}_result.json',record)
    print(canonical({'case_id':case_id,'status':result.status,'errors':result.errors,'calls':result.calls,
                     'budget':record['budget_after'],'workers_started':inner.starts,'workers_reaped':inner.reaped}))


def close():
    ledger=BudgetLedger(REAL_RECORDS,REAL_ANCHORS,'live')
    rows=[json.loads(p.read_bytes()) for p in [AUDIT/'B01_result.json',AUDIT/'B02_result.json'] if p.exists()]
    before=ledger.snapshot()
    if not before['stopped'] and len(rows)<2: ledger.stop('safety_rejection')
    report={'batch':1,'cases':rows,'second_batch_not_run':True,'budget_before_close':ledger.snapshot()}
    path=REAL_RECORDS.parent/'batch1_day8b2_receipt.json'
    write(path,report)
    if not before['active'] and 1 not in before['reports']: ledger.record_batch_report(1,sha(report))
    ledger.close_batch(1)
    state=ledger.snapshot()
    write(AUDIT/'closed_budget_receipt.json',{'report_sha256':sha(report),'state':state,
          'closed_at_utc':datetime.now(timezone.utc).isoformat(),'batch2_authorized':False})
    print(canonical({'live_permission_closed':1 in state['closed_batches'],'budget':state,'batch2_authorized':False}))


def main():
    command=sys.argv[1]
    if len(sys.argv)==3 and sys.argv[2]=='--worker':
        if command=='mock': value=mock_check()
        else:
            from scripts.day8b1_acceptance import worker
            value=worker(command)
        print(canonical(value)); return int(value.get('failed',0)>0 or value.get('passed') is False)
    if command=='checks': checks()
    elif command=='preflight': preflight()
    elif command=='case1': run_one('B01')
    elif command=='case2': run_one('B02')
    elif command=='close': close()
    else: raise AcceptanceDenied('unknown_command')
    return 0


if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception:
        # Never print a config, upstream error, draft, request or exception repr.
        print('{"passed":false,"reason":"controlled_operator_stop"}')
        raise SystemExit(1)
