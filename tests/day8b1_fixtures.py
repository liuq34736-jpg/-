"""Hand-authored synthetic contract fixtures; never corpus or real AI approval."""
from backend.question_quality_v1.contract import ApplicationDraft, IndependentVerdict, VERSION, ROLES, limit_ids
from backend.ai_acceptance_v1.policy import canonical, sha
from scripts.day8b_prepare import CASES

ANALOGIES = {
    "B01": ["可先观察你准备重新经营时有哪些可核对的时机，再比较线上与小店，不从顺应时机推出经营成果。",
            "如果两种经营方式需要取舍，可先辨别各自牵涉的选择，不把两边同时兼顾当成已满足的情形。",
            "可把逐步推进作为核对经营准备的线索，先看下一步适不适合，再安排后续，不由此确定经营结果。",
            "可核对表达方式是否既坚持原则又便于沟通，不把柔和表达理解成已经获得合作。"],
    "B02": ["可先观察工作环境与实际情况，再考虑如何推进换工作的想法，不替未获得的岗位补写条件。",
            "如果有以参与者身份了解工作的机会，可先核对这种身份的限制，不将参与的提醒扩成全部换工作都有利。",
            "可把先停下观察作为辅助提醒，核对外部情况再行动，不认定现在的工作环境已有不良变化。",
            "若参与渠道不畅，可核对是否需要收敛对外在待遇的追求，不断言这种阻隔已在你的工作中发生。"],
    "B03": ["可先区分外在表达与实际互动，再核对你想怎样安排联系，不替对方认定真实想法。",
            "可先看怎样表达符合自己的原则，再决定联系方式，不因为表面形式就勉强相处。",
            "如果互动中有需要澄清的事，可先了解情况再决定何时联系，不预设过失属于谁。",
            "可核对实际互动是否适合继续联系，再决定停或做，不把节奏当作关系已有结果。"],
    "B04": ["可先核对尚未确定的行程需要哪些安排，再考虑怎样应对起步困难，不据此断言出行环境危险。",
            "可分别保留小事与大事守正的不同提醒，先核对适用范围，不按活动三天自动选择其中一支。",
            "可把暂停观察作为行程安排的辅助线索，再了解实际情况，不认定阻碍已经存在。",
            "可观察计划是否需要往复调整，再决定下一步安排，不把返回的线索解释为活动结束的日期。"],
    "B05": ["可把持续努力与长期持守作为核对项目想法的提醒，不由此给出利润、金额或截止期结果。",
            "若推进时有把事情做绝的倾向，可核对是否需要留余地，不推定现实所处的位置。",
            "可将持续奋发作为辅助观察，不把重复的提醒增加成新的判断，也不据此推算收益。",
            "如果需要公开表达主张，可先核对表达的范围与风险，不认定项目已经进入这一阶段。"],
    "B06": ["可先辨别想法与完成计划之间还缺什么，再考虑下一步，不推定你已有行动或成果。",
            "如果想法仍未具体化，可先核对怎样把握限度，再考虑行动，不认定已有冒进行为。",
            "可将完成后仍需预先准备作为辅助提醒，不把已有想法当成事情已经完成。",
            "可先核对有哪些备选方向，再考虑如何保留差异，不替尚未说明的选项作选择。"],
}


def draft_for(case_id, request):
    p = request.checked()
    case = next(c for c in CASES if c['case_id'] == case_id)
    q = p['question']
    focus = {'start': 0, 'end': len(q), 'text': q, 'kind': 'question'}
    provided = [{'start': q.index(s), 'end': q.index(s) + len(s), 'text': s, 'kind': k} for s, k in case['provided']]
    claims = []
    for i, role in enumerate(ROLES):
        row = p['frames'][role]
        claims.append({'claim_id': f'claim_{i}', 'role': role, 'frame_id': row['frame_id'],
            'meaning_refs': list(range(len(row['frame']['core_claims']))),
            'source_evidence_ids': sorted({e for a in row['frame']['core_claims'] for e in a['supported_by']}),
            'question_spans': [focus], 'preserved_limit_ids': limit_ids(p, role),
            'analogy_text': ANALOGIES[case_id][i], 'guidance': '可先核对已提供的信息与适用范围，再考虑下一步安排。', 'source_layer': 'application_analogy'})
    return ApplicationDraft.model_validate({'contract_version': VERSION, 'request_fingerprint': request.fingerprint,
        'intent': {'category': case['category'], 'focus': focus, 'provided': provided, 'missing': []}, 'claims': claims})


def verdict_for(request, draft, supported=True):
    return IndependentVerdict.model_validate({'contract_version': VERSION, 'request_fingerprint': request.fingerprint,
        'draft_fingerprint': sha(draft.model_dump()), 'claims': [
            {'claim_id': c.claim_id, 'reviewed_frame_id': c.frame_id, 'reviewed_evidence_ids': c.source_evidence_ids,
             'reviewed_limit_ids': c.preserved_limit_ids, 'supported': supported, 'preserves_conditions': True,
             'no_invented_facts': True, 'no_prediction': True, 'preserves_scope': True, 'question_relevant': True,
             'score': 3, 'reason': '独立审核协议测试替身；该数值不是实际模型质量或来源复核结论。'} for c in draft.claims]})


def reply(content, **changes):
    value = {'code': 'ok', 'http_status': 200, 'content': content,
             'usage': {'prompt_tokens': 150, 'completion_tokens': 50, 'total_tokens': 200,
                       'prompt_cache_hit_tokens': 50, 'prompt_cache_miss_tokens': 100}}
    value.update(changes)
    return value


def replies_for(requests):
    replies = {}
    for case_id, request in requests.items():
        draft = draft_for(case_id, request)
        replies[(case_id, 'candidate')] = reply(canonical(draft.model_dump()))
        replies[(case_id, 'reviewer')] = reply(canonical(verdict_for(request, draft).model_dump()))
    return replies
