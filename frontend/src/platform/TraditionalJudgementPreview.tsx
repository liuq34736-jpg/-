import { type JudgementPreview } from './traditionalPreviewContract'
import { displaySentence, factorDisplay, previewOverview, PRESENTATION_VERSION } from './traditionalPresentation'

const RELATIONS: Record<string, string> = {
  yong_generates_body: '生体', body_generates_yong: '体生', body_controls_yong: '体克',
  yong_controls_body: '克体', same_element: '比和',
}
const BASIS: Record<string, string> = { DIRECT_SOURCE: '古籍直接依据', PROJECT_CONVENTION: '项目约定',
  MODERN_INTERPRETATION: '现代解释', DISPUTED: '存在争议', PENDING_RESEARCH: '待研究' }
const STATUS: Record<string, string> = { bounded: '有限综合判断', branch_unresolved: '条件分支未决',
  unreviewed: '结构性回退', not_eligible: '结构性回退', evidence_unavailable: '依据不可用 · 安全回退' }

export default function TraditionalJudgementPreview({ value }: { value: JudgementPreview }) {
  return <section className="traditional-preview" data-testid="traditional-preview" data-review-status={value.review_status}>
    <div className="judgement-heading"><div><span className="eyebrow">本地预览 · 传统规则层</span><h3>传统综合判断</h3></div>
      <span className="tag" data-testid="review-status">{STATUS[value.review_status]}</span></div>
    <div className="judgement-summary"><h4 data-testid="judgement-label">{value.label}</h4>{previewOverview(value).map(text => <p key={text}>{text}</p>)}</div>
    <h4>主要依据</h4><p className="section-description">体用为结构依据，旺衰限制同一关系；动爻只在已审核的条件范围内参与。下列有利、不利不按数量相加。</p>
    <div className="judgement-factors">{[['有利因素', value.favorable_factors], ['不利因素', value.adverse_factors]].map(([title, factors]) =>
      <article key={title as string}><h5>{title as string}</h5>{typeof factors !== 'string' && factors.length ? <ul>{factors.map(factor =>
        <li key={factor.id}><p>{factorDisplay(factor.text, value)}</p><small>{factor.scope}</small></li>)}</ul> : <p className="section-description">本次没有可采用的该类扩展依据。</p>}</article>)}</div>
    {value.strength_modifiers.length > 0 && <div className="strength-reminders"><h5>旺衰修饰</h5><ul>{value.strength_modifiers.map(factor => <li key={factor.id}>{factor.text}</li>)}</ul></div>}
    <h4>动爻条件与提醒</h4>
    {value.eligible_for_condition_review ? <>
      <p className="section-description">条件尚未核实。以下是原文适用范围，不是对你现实情况的认定。</p>
      <ol className="condition-list">{value.conditions.map(condition => <li key={condition.id}><p>{displaySentence(condition.text)}</p><span className="condition-state">尚未核实</span></li>)}</ol>
      {value.review_status === 'branch_unresolved' && <p className="notice">不同分支不代表同时成立，程序不会根据问题替你选定分支。</p>}
      <div className="branch-list">{value.branches.map((branch, index) => <article key={branch.id} data-testid="condition-branch">
        <h5>{value.review_status === 'branch_unresolved' ? `条件分支 ${index + 1}` : `提醒 ${index + 1}`}</h5>
        <p>{displaySentence(branch.text)}</p><small>适用条件：{branch.condition_ids.map(id => `上列条件 ${value.conditions.findIndex(item => item.id === id) + 1}`).join('、')}（尚未核实）</small>
      </article>)}</div>
      {value.scope_limits.length > 0 && <ul>{value.scope_limits.map(limit => <li key={limit.id}>{displaySentence(limit.text)}</li>)}</ul>}
    </> : <p className="notice" data-testid="judgement-fallback">{value.review_status === 'evidence_unavailable' ?
      '扩展判断的证据校验未通过，本次未采用；以下保留已验证卦象与基础卦义。' : '该爻的扩展综合判断尚未完成来源审核'}。</p>}
    {value.conflicts.length > 0 && <div className="judgement-conflicts"><h5>主要依据中的未决冲突</h5>{value.conflicts.map(item => <p key={item.type}>{item.text}</p>)}</div>}
    <h4>互卦、变卦辅助分析</h4><div className="judgement-auxiliary">{value.auxiliary_analysis.map(item => <article key={item.role}>
      <h5>{item.role === 'mutual_hexagram' ? '互卦' : '变卦'} · {item.name}</h5><p>{item.note}</p>
      <ul>{item.items.map(side => <li key={side.side}>{side.side === 'upper' ? '上卦' : '下卦'}：{side.trigram}{side.element}{side.state_label} · {RELATIONS[side.relation_to_original_body] || '结构关系'}
        {side.status === 'reference_only' ? '（仅供参校）' : side.status === 'context_only' ? '（背景，不重复计入）' : '（辅助）'}</li>)}</ul>
    </article>)}</div>
    {value.auxiliary_analysis.length === 0 && <p className="section-description">扩展依据未采用；互卦和变卦的冻结计算仍显示在上方。</p>}
    {value.auxiliary_divergences.map(item => <p className="section-description" key={`${item.type}-${item.text}`}>{item.text}</p>)}
    <div className="judgement-uncertainties"><h5>限制与未决事项</h5><ul>{value.uncertainties.map(item => <li key={item.type}>{item.text}</li>)}</ul></div>
    <details className="reading-details judgement-sources" data-testid="judgement-sources"><summary>古籍与审核来源</summary>
      <h5>原始规则层总论与因素（完整保留）</h5><p>{displaySentence(value.summary)}</p>
      <ul>{value.favorable_factors.concat(value.adverse_factors).map(factor => <li key={factor.id}>{displaySentence(factor.text)} · {factor.scope}</li>)}</ul>
      <p>展示版本：{PRESENTATION_VERSION}。默认摘要未改动判断方向、资格、条件或来源；原典摘录保持原字形和标点。</p>
      <p>本预览采用固定的逐条离线条件审核记录；不等于人工 verified 或生产签名，不批准其他爻位。</p>
      {value.review_provenance && <p>条件规则：{value.review_provenance.rule_version}</p>}
      <p>预览版本：{value.preview_version}；裁决政策：{value.policy_version}；只读注册：{value.registry_version}。</p>
      {value.conditions.concat(value.branches, value.scope_limits).map(atom => <div className="condition-evidence" key={atom.id}>
        <h5>{atom.text}</h5>{atom.source_quotes.map((quote, index) => {
          const source = value.classical_sources.find(item => item.evidence_id === quote.evidence_id)
          return <blockquote key={`${quote.evidence_id}-${index}`}>{quote.quote}{source && <cite>{source.source_title} · {source.edition} · {source.location} · 核验方式：{source.verification_status}{source.variant_present ? ' · 存在版本字形差异，未判正误' : ''}
            <a href={source.url} target="_blank" rel="noopener noreferrer"> 查看来源 ↗</a></cite>}</blockquote>
        })}
      </div>)}
      {value.rule_sources.map(source => <details className="source-reference" key={source.source_id}><summary>{source.title} · {source.location}</summary>
        <p>{source.excerpt}</p><p>{source.limits}</p><small>{source.edition} · {source.volume} · 扫描页 {source.pdf_pages.join('、')} · 原印页 {source.printed_pages.join('、')}</small>
        <a href={source.url} target="_blank" rel="noopener noreferrer">查看古籍扫描来源 ↗</a></details>)}
      <h5>采用的规则</h5><ul>{value.rules.map(rule => <li key={rule.rule_id}>{rule.rule_id} · {BASIS[rule.basis] || rule.basis}：{rule.summary}</li>)}</ul>
    </details>
    <p className="small-note">仅用于本地传统判断预览。不推定现实事件必然成败，不给出成功概率，未调用 AI，也未写入历史。</p>
  </section>
}
