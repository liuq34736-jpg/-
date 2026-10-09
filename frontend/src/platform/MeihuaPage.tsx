import { useEffect, useRef, useState, type FormEvent } from 'react'
import { BookOpen, ArrowRight, LoaderCircle } from 'lucide-react'
import { catalogSchema, resultSchema, ROLE_LABELS, type Catalog, type MeihuaResult } from './meihuaContract'
import './meihua.css'

function chinaNow() {
  const parts = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23' }).formatToParts(new Date())
  const value = Object.fromEntries(parts.map(part => [part.type, part.value]))
  return `${value.year}-${value.month}-${value.day}T${value.hour}:${value.minute}:${value.second}`
}

function Lines({ hexagram, moving }: { hexagram: MeihuaResult['original_hexagram']; moving?: number }) {
  return <div className="hexagram-lines" role="img" aria-label={`${hexagram.full_name}，六爻从下往上编号`}>
    {hexagram.lines.map((value, i) => <div key={i} data-testid="hexagram-line" data-position={i + 1}
      data-moving={moving === i + 1 ? 'true' : 'false'} className={`yao-row ${moving === i + 1 ? 'is-moving' : ''}`}>
      <span className={`yao-stroke ${value ? 'yang' : 'yin'}`}><i /><i /></span>
      <span className="yao-number">{i + 1}{moving === i + 1 ? ' · 动' : ''}</span>
    </div>)}
  </div>
}

const SECTION_LABELS: Record<string, string> = {
  'judgment.classical_text': '卦辞', 'tuan.classical_text': '彖传', 'xiang.classical_text': '大象',
  yao_classical_text: '爻辞', xiang_classical_text: '小象',
}
const UNIT_LABELS: Record<string, string> = { current_state: '当前格局', primary_change: '核心变化', change_direction: '变化方向',
  internal_process: '内部过程', body_use: '体用', body_use_relation: '生克关系', seasonal_strength: '时令', overall_structure: '综合结构' }

function ReadingResult({ value }: { value: MeihuaResult }) {
  const { original_hexagram: original, changed_hexagram: changed, mutual_hexagram: mutual, moving_line: moving, body_use: body, strength } = value
  return <section className="meihua-results" aria-live="polite" data-testid="meihua-result">
    {value.question_text && <div className="question-display"><span className="eyebrow">你问的是</span><p>{value.question_text}</p>
      <small>本轮保留问题作为上下文，以下基础解释不作个性化 AI 推断。</small></div>}
    <div className="reading-hero">
      <div><span className="eyebrow">{value.input_mode === 'manual_hexagram' ? '你输入的卦象' : '冻结时间算法起卦'}</span>
        <h2 data-testid="original-name">{original.full_name}</h2><p className="moving-name" data-testid="moving-name">{moving.name}动</p>
        <p className="hexagram-transition">{original.name} <ArrowRight size={16} /> {changed.name}</p>
        <span className="small-note">{value.cast_at.replace('T', ' ')} · 中国时间</span></div>
      <Lines hexagram={original} moving={moving.position} />
    </div>
    <div className="result-facts">
      <div><span>本卦</span><strong>{original.name}</strong></div><div><span>互卦</span><strong data-testid="mutual-name">{mutual.full_name}</strong></div>
      <div><span>变卦</span><strong data-testid="changed-name">{changed.full_name}</strong></div>
      <div><span>体卦</span><strong>{body.body_trigram}（{body.body_element}）</strong></div><div><span>用卦</span><strong>{body.yong_trigram}（{body.yong_element}）</strong></div>
      <div><span>五行关系</span><strong data-testid="relation">{body.relation_text}</strong></div>
    </div>
    <div className="season-card"><div><span className="eyebrow">时令 · 节气月建</span><p>{strength.solar_term_month_branch}月 · {strength.ruling_element}当令</p>
      <small>当前节气：{strength.active_solar_term} · 下一个节气：{strength.next_solar_term}</small></div>
      <div><p>体{body.body_element}{strength.body.state_label} · 用{body.yong_element}{strength.yong.state_label}</p>
        <small>旺衰只描述传统月令状态，不推定现实结果。</small></div></div>
    <h3>已批准的基础卦义</h3><p className="section-description">沿用现有已核验古籍与已批准解释。本轮未调用 AI，也未将问题套入新的个性化断语。</p>
    <div className="meaning-grid">{value.standard_meanings.map(meaning => <article key={meaning.role} data-testid={`meaning-${meaning.role}`}>
      <span className="eyebrow">{ROLE_LABELS[meaning.role]}</span><p>{meaning.text}</p>
      <small>{meaning.status === 'SEMANTIC_APPROVED' ? '资料依据：已核验' : '本项使用结构性安全回退'}</small>
    </article>)}</div>
    <details className="reading-details"><summary>为什么这么看？</summary>
      <div className="unit-list">{value.interpretation_units.map(unit => <div key={unit.type}><h4>{UNIT_LABELS[unit.type] || unit.type}</h4><p>{unit.statement}</p></div>)}</div>
      <p className="section-description">互卦及互、变卦旺衰为辅助信息；变卦是结构变化方向，不代表必然发生的未来。</p>
      <h4>古籍资料引用</h4><p className="section-description">电子文本的卷次与段落位置不是原书连续页码。未确定的原书页码保持为空。</p>
      {value.source_references.map((reference, i) => <details className="source-reference" key={`${reference.role}-${reference.evidence_id}-${i}`}>
        <summary>{ROLE_LABELS[reference.role]} · {SECTION_LABELS[reference.section_type]} · {reference.source_title}</summary>
        <p>{reference.text}</p><small>{reference.edition} · {reference.location}</small>
        <p><a href={reference.url} target="_blank" rel="noopener noreferrer">查看来源页面 ↗</a></p>
        <small>核验方式：{reference.verification_status}{reference.variant_present ? ' · 存在版本字形差异，未判正误' : ''}</small>
      </details>)}
    </details>
    <details className="reading-details"><summary>计算与版本详情</summary>
      <p>六爻位置 1 为最下爻，6 为最上爻；动爻所在的三爻卦为用。</p>
      <p>当月切换：{strength.strength_boundary_time.replace('T', ' ')}；下月切换：{strength.next_month_boundary_time.replace('T', ' ')}。</p>
      <p>互卦辅助：上{strength.mutual.upper.trigram}{strength.mutual.upper.state_label}，下{strength.mutual.lower.trigram}{strength.mutual.lower.state_label}；
        变卦辅助：上{strength.changed.upper.trigram}{strength.changed.upper.state_label}，下{strength.changed.lower.trigram}{strength.changed.lower.state_label}。</p>
      {value.time_calculation && <div data-testid="time-calculation"><p>农历：{value.time_calculation.lunar_datetime}；年支{value.time_calculation.year_branch}（{value.time_calculation.year_branch_number}），时支{value.time_calculation.hour_branch}（{value.time_calculation.hour_branch_number}）。</p>
        <p>上卦总数 {value.time_calculation.upper_total}，除八余 {value.time_calculation.upper_remainder}；下卦总数 {value.time_calculation.lower_total}，除八余 {value.time_calculation.lower_remainder}；动爻除六余 {value.time_calculation.moving_remainder}。</p>
        <p>23:00–00:59 为子时；农历日期在 00:00 换日。除八余零为坤，除六余零为第六爻。</p></div>}
      <dl>{Object.entries(value.versions).map(([name, version]) => <div key={name}><dt>{name}</dt><dd>{version}</dd></div>)}</dl>
    </details>
    <p className="small-note">本次网页计算未保存历史。原系统历史仍保持原样；AI 问事正文和传统综合断卦尚未接入。</p>
  </section>
}

export default function MeihuaPage() {
  const [catalog, setCatalog] = useState<Catalog | null>(null)
  const [catalogFailed, setCatalogFailed] = useState(false)
  const [mode, setMode] = useState<'manual_hexagram' | 'time_cast'>('manual_hexagram')
  const [question, setQuestion] = useState('')
  const [hexagramId, setHexagramId] = useState(20)
  const [position, setPosition] = useState(4)
  const [castAt, setCastAt] = useState(chinaNow)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<MeihuaResult | null>(null)
  const controller = useRef<AbortController | null>(null)
  const locked = useRef(false)
  useEffect(() => {
    const abort = new AbortController()
    fetch('/api/v1/meihua/catalog', { signal: abort.signal }).then(async response => {
      if (!response.ok) throw new Error('unavailable')
      return catalogSchema.parse(await response.json())
    }).then(setCatalog).catch(() => { if (!abort.signal.aborted) setCatalogFailed(true) })
    return () => { abort.abort(); controller.current?.abort() }
  }, [])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (locked.current) return
    locked.current = true
    setBusy(true); setError(''); setResult(null)
    const abort = new AbortController()
    controller.current = abort
    const timeout = window.setTimeout(() => abort.abort(), 25000)
    try {
      const payload = { input_mode: mode, question_text: question, cast_at: `${castAt.length === 16 ? castAt + ':00' : castAt}+08:00`,
        ...(mode === 'manual_hexagram' ? { hexagram_id: hexagramId, moving_line: position } : {}) }
      const response = await fetch('/api/v1/readings', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload), signal: abort.signal })
      if (!response.ok) {
        setError(response.status === 422 ? '输入格式不正确，请检查卦象、爻位及中国起卦时间（2000–2099 年）。' :
          response.status === 413 ? '问题过长，请缩短后重新提交。' : '冻结计算服务暂不可用，请稍后重试。')
        return
      }
      setResult(resultSchema.parse(await response.json()))
    } catch {
      if (controller.current === abort) setError('计算未完成，请检查本地服务后重试。')
    } finally {
      window.clearTimeout(timeout)
      locked.current = false
      if (controller.current === abort) { setBusy(false); controller.current = null }
    }
  }
  const selected = catalog?.entries.find(entry => entry.id === hexagramId)
  return <section className="page-panel meihua-page"><span className="eyebrow">探索工具 / 有依据的卦象分析</span>
    <div className="page-heading"><BookOpen size={29} strokeWidth={1.6} /><h1>梅花易数</h1><span className="tag">确定性计算</span></div>
    <p>输入自己起好的卦，或选择独立的时间起卦。所有卦象、体用与时令关系均来自冻结规则。</p>
    <form className="casting-form" onSubmit={submit}>
      <label htmlFor="question-text">你想问什么？<span>选填 · 最多 500 字</span></label>
      <textarea id="question-text" maxLength={500} rows={3} value={question} disabled={busy} onChange={event => setQuestion(event.target.value)}
        placeholder="例如：我正在重新做女装生意，近期应该怎么推进？" />
      <small>问题只保留为上下文，不参与本卦、动爻、体用或旺衰的计算。</small>
      <fieldset disabled={busy}><legend>起卦方式</legend><div className="mode-control">
        <label><input type="radio" name="mode" value="manual_hexagram" checked={mode === 'manual_hexagram'} onChange={() => setMode('manual_hexagram')} />手动输入卦象</label>
        <label><input type="radio" name="mode" value="time_cast" checked={mode === 'time_cast'} onChange={() => setMode('time_cast')} />时间起卦</label>
      </div></fieldset>
      {mode === 'manual_hexagram' && <div className="casting-fields"><div><label htmlFor="hexagram-id">本卦</label>
        <select id="hexagram-id" disabled={!catalog || busy} value={hexagramId} onChange={event => setHexagramId(Number(event.target.value))}>
          {!catalog && <option value={20}>正在读取六十四卦…</option>}{catalog?.entries.map(entry => <option key={entry.id} value={entry.id}>{entry.id} · {entry.full_name}</option>)}
        </select></div><div><label htmlFor="moving-position">动爻位置</label><select id="moving-position" value={position} disabled={!catalog || busy} onChange={event => setPosition(Number(event.target.value))}>
          {(selected?.line_names || ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻']).map((name, i) => <option value={i + 1} key={i}>{name}（第 {i + 1} 爻）</option>)}
        </select></div></div>}
      <label htmlFor="cast-at">起卦时间<span>中国标准时间 · UTC+08:00</span></label>
      <input id="cast-at" type="datetime-local" step="1" min="2000-01-01T00:00:00" max="2099-12-31T23:59:59" required disabled={busy} value={castAt} onChange={event => setCastAt(event.target.value)} />
      <small>{mode === 'manual_hexagram' ? '此时间仅用于时令分析，改变时间不会改变你输入的本卦和动爻。' : '使用农历年月日时法；23 点进入子时，农历日期仍按 00:00 换日。'}</small>
      {catalogFailed && <p role="alert" className="notice">卦象目录暂不可用，请检查本地服务后刷新页面。</p>}
      {error && <p role="alert" className="notice">{error}</p>}
      <button className="start-casting" type="submit" disabled={busy || (mode === 'manual_hexagram' && !catalog)}>
        {busy ? <><LoaderCircle size={17} />正在计算…</> : <>开始起卦 <ArrowRight size={17} /></>}
      </button>
    </form>
    {result && <ReadingResult value={result} />}
  </section>
}
