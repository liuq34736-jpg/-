"""Mock-only acceptance + guarded regression. No live flag/authorization command."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def mock_first_batch():
    from scripts.day8a_acceptance import install_guard
    install_guard()
    from backend.ai_acceptance_v1.ledger import BudgetLedger
    from backend.ai_acceptance_v1.policy import sha
    from backend.ai_acceptance_v1.executor import AcceptanceExecutor
    from backend.ai_acceptance_v1.prompts import OfficialTokenCounter
    from backend.ai_acceptance_v1.transport import ProcessTransport
    from backend.app.meihua_models import ManualInput
    from backend.traditional_judgement_v1.trusted_input import OfflineJudgementAdapter
    from backend.question_quality_v1.contract import build_request
    from scripts.day8b_prepare import CASES, CAST_AT
    from tests.day8b1_fixtures import replies_for
    ledger = BudgetLedger(ROOT/'private/day8b1/mock-records', ROOT/'private/day8b1-anchors','mock')
    report_path=ROOT/'docs/day8b1_batch1_mock_report.json'
    # Re-running the validation script never initializes a replacement budget.
    if ledger.marker.exists() or ledger.db.exists() or ledger.anchor.exists():
        state=ledger.snapshot()
        report=json.loads(report_path.read_bytes())
        if state['reports'].get(1) != sha(report): raise ValueError('existing_mock_report_invalid')
        return {'passed':all(r['status']=='MOCK_CONTRACT_ACCEPTED' for r in report['cases']),
                'requests':state['requests'],'mock_worker_starts_this_run':0,'reused_existing_mock_report':True,
                'real_ai_calls':0,'report_sha256':sha(report)}
    ledger.initialize(); ledger.authorize(1,'DAY8B1_USER_AUTHORIZED_MOCK_ONLY_BATCH1')
    selected=CASES[:2]
    trusted=OfflineJudgementAdapter().calculate_batch([ManualInput(input_mode='manual_hexagram',
        hexagram_id=c['hexagram_id'],moving_line=c['moving_line'],cast_at=CAST_AT,question_text=c['question']) for c in selected])
    requests={c['case_id']:build_request(x) for c,x in zip(selected,trusted)}
    transport=ProcessTransport(ledger,mock_replies=replies_for(requests))
    report=AcceptanceExecutor(ledger,transport,OfficialTokenCounter(ROOT)).run_batch(1,requests,report_path)
    return {'passed':all(r['status']=='MOCK_CONTRACT_ACCEPTED' for r in report['cases']),
            'requests':report['budget']['requests'],'mock_worker_starts_this_run':transport.starts,
            'mock_workers_reaped':transport.reaped,'second_batch_authorized':2 in ledger.snapshot()['authorized_batches'],
            'real_ai_calls':0,'report_sha256':sha(report)}


def child(kind):
    env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','TEMP','TMP'}}
    env['DEEPSEEK_API_KEY']='SYNTHETIC_OFFLINE_CONFIG_ONLY'
    started=datetime.now(timezone.utc).isoformat(); before=time.monotonic()
    run=subprocess.run([sys.executable,'-I','-B','-X','utf8',str(Path(__file__).resolve()),kind,'--worker'],
        cwd=ROOT,env=env,capture_output=True,timeout=900,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    try: value=json.loads(run.stdout)
    except ValueError: value={'passed':False,'failed':1,'reason':'guarded_runner_failure'}
    # Keep case outcomes/hashes, not duplicated full classical sources or
    # hand-authored narratives already held in the dedicated evidence files.
    for key in ('examples','synthetic_examples','mock_samples'):
        value.pop(key,None)
    return {'command':f'.venv/Scripts/python.exe -I -B -X utf8 scripts/day8b1_acceptance.py {kind} --worker',
            'started_at_utc':started,'seconds':round(time.monotonic()-before,3),'exit_code':run.returncode,'result':value}


def worker(kind):
    if kind=='mock': return mock_first_batch()
    if kind=='unit':
        from scripts.day5_offline_acceptance import unit_worker
        return unit_worker()
    if kind=='failures':
        from unittest.mock import patch
        from scripts import day8a_quality_evaluation
        original=Path.write_text
        def redirect(path,data,*args,**kw):
            if path.resolve() != (ROOT/'docs/day8a_quality_evaluation_results.json').resolve(): raise PermissionError('unexpected_write')
            return original(ROOT/'docs/day8b1_old_failure_results.json',data,*args,**kw)
        # Its stdout is counts; only the parent writes new stage results.
        import contextlib,io
        with patch.object(Path,'write_text',redirect), contextlib.redirect_stdout(io.StringIO()): day8a_quality_evaluation.main()
        return json.loads((ROOT/'docs/day8b1_old_failure_results.json').read_bytes())
    if kind in {'legacy','frozen_matrix','preview_matrix','old71'}:
        from scripts.day8a_acceptance import install_guard,preview_matrix,old71
        if kind=='preview_matrix': return preview_matrix()
        if kind=='old71': return old71()
        from scripts.day4_offline_checks import run_legacy,run_matrix
        return run_legacy() if kind=='legacy' else run_matrix()
    raise ValueError('unknown_mock_check')


def main():
    if len(sys.argv)==3 and sys.argv[2]=='--worker':
        try: result=worker(sys.argv[1])
        except Exception: result={'failed':1,'passed':False,'reason':'guarded_runner_failure'}
        print(json.dumps(result,ensure_ascii=True))
        return int(result.get('failed',0)>0 or result.get('passed') is False)
    before=json.loads((ROOT/'runtime/day8b1-baseline/files.json').read_text(encoding='utf-8-sig'))
    checks={kind:child(kind) for kind in ('unit','failures','mock','legacy','frozen_matrix','preview_matrix','old71')}
    from scripts.day6a_integrity_check import inspect
    integrity=inspect()
    changed=[p for p,h in before['files'].items() if not (ROOT/p).is_file() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    result={'stage':'day8b1_mock_acceptance','base_commit':before['base_commit'],'python':sys.version.split()[0],
        'checked_at_utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'baseline_files':len(before['files']),
        'changed_baseline_files':changed,
        **{k:integrity[k] for k in ('production_files','changed_production_files','signed_cache_files',
           'changed_signed_cache_files','history_rows','history_schema_unchanged','history_row_hashes_unchanged',
           'history_database_bytes_unchanged','git_safety')},
        'real_ai_calls':0,'live_budget_authorized':False,'production_application_enabled':False}
    result['passed']=(not changed and all(c['exit_code']==0 for c in checks.values())
        and not integrity['changed_production_files'] and not integrity['changed_signed_cache_files']
        and integrity['history_rows']==42 and integrity['git_safety']['passed'] and all(integrity[k] for k in
        ('history_schema_unchanged','history_row_hashes_unchanged','history_database_bytes_unchanged')))
    (ROOT/'docs/day8b1_acceptance_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'unit':checks['unit']['result'],
                     'checks_exit_codes':{k:v['exit_code'] for k,v in checks.items()},
                     'changed_baseline_files':changed,'history_rows':result['history_rows'],'real_ai_calls':0},ensure_ascii=False))
    return int(not result['passed'])


if __name__=='__main__': raise SystemExit(main())
